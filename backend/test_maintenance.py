"""
Direct service-layer test — no HTTP, no auth token needed.
Tests all CRUD operations and Task 4 vehicle validations.
"""
from datetime import date
from fastapi import HTTPException
from app.database import SessionLocal
from app.models.maintenance import MaintenanceCategory, MaintenanceStatus
from app.schemas.maintenance import MaintenanceCreate, MaintenanceUpdate
from app.services import maintenance_service

db = SessionLocal()
PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"

def check(label, condition, got=""):
    icon = PASS if condition else FAIL
    suffix = f"  → {got}" if got else ""
    print(f"  [{icon}] {label}{suffix}")

print("=" * 60)
print("  Maintenance Service-Layer Smoke Test")
print("=" * 60)

# ── Find a real vehicle_id ─────────────────────────────────────
from app.models.vehicle import Vehicle
vehicle = db.query(Vehicle).first()
if not vehicle:
    print("  [SKIP] No vehicles in DB – cannot run full test")
    db.close()
    exit()

REAL_VID = vehicle.id
print(f"\n  Using vehicle_id={REAL_VID}  ({vehicle.vehicle_number})\n")

# ── 1. Task 4: reject invalid vehicle ─────────────────────────
try:
    maintenance_service.create_maintenance(
        MaintenanceCreate(vehicle_id=99999, category=MaintenanceCategory.OIL_CHANGE,
                          service_date=date.today()), db)
    check("Task4 – invalid vehicle rejected", False, "no exception raised")
except HTTPException as e:
    check("Task4 – invalid vehicle rejected (404)", e.status_code == 404, f"HTTP {e.status_code}")

# ── 2. Create record ───────────────────────────────────────────
payload = MaintenanceCreate(
    vehicle_id=REAL_VID,
    category=MaintenanceCategory.OIL_CHANGE,
    service_date=date(2026, 7, 28),
    next_service_date=date(2026, 10, 28),
    service_cost=1500.0,
    service_provider="QuickLube Center",
    status=MaintenanceStatus.SCHEDULED,
    notes="Regular oil change"
)
record = maintenance_service.create_maintenance(payload, db)
check("Create maintenance record", record.id is not None, f"id={record.id}")
check("  – category stored correctly", record.category == MaintenanceCategory.OIL_CHANGE,
      record.category)
check("  – status default Scheduled", record.status == MaintenanceStatus.SCHEDULED,
      record.status)
check("  – vehicle_id linked", record.vehicle_id == REAL_VID, record.vehicle_id)

RID = record.id

# ── 3. Get all ─────────────────────────────────────────────────
all_records = maintenance_service.get_all_maintenance(db)
check("Get all maintenance records", len(all_records) >= 1, f"count={len(all_records)}")

# ── 4. Get by ID ───────────────────────────────────────────────
fetched = maintenance_service.get_maintenance_by_id(RID, db)
check("Get by ID", fetched.id == RID, f"id={fetched.id}")

# ── 5. Get by non-existent ID ──────────────────────────────────
try:
    maintenance_service.get_maintenance_by_id(999999, db)
    check("Get by invalid ID → 404", False, "no exception")
except HTTPException as e:
    check("Get by invalid ID → 404", e.status_code == 404, f"HTTP {e.status_code}")

# ── 6. Task 4: get by vehicle (valid) ─────────────────────────
veh_records = maintenance_service.get_maintenance_by_vehicle(REAL_VID, db)
check("Task4 – get by vehicle (valid)", len(veh_records) >= 1, f"count={len(veh_records)}")

# ── 7. Task 4: get by invalid vehicle ─────────────────────────
try:
    maintenance_service.get_maintenance_by_vehicle(99999, db)
    check("Task4 – invalid vehicle → 404", False, "no exception")
except HTTPException as e:
    check("Task4 – invalid vehicle → 404", e.status_code == 404, f"HTTP {e.status_code}")

# ── 8. Task 4: ownership check ─────────────────────────────────
owns = any(r.id == RID for r in veh_records)
check("Task4 – record belongs to correct vehicle", owns, f"id={RID} in vehicle {REAL_VID}")

# ── 9. Update ──────────────────────────────────────────────────
update = MaintenanceUpdate(
    category=MaintenanceCategory.BRAKE_SERVICE,
    service_date=date(2026, 7, 28),
    next_service_date=date(2027, 1, 1),
    service_cost=3200.0,
    service_provider="BrakePro",
    status=MaintenanceStatus.COMPLETED,
    notes="Brake pads replaced"
)
updated = maintenance_service.update_maintenance(RID, update, db)
check("Update maintenance record", updated.category == MaintenanceCategory.BRAKE_SERVICE,
      updated.category)
check("  – status updated to Completed", updated.status == MaintenanceStatus.COMPLETED,
      updated.status)
check("  – vehicle_id unchanged after update", updated.vehicle_id == REAL_VID, updated.vehicle_id)

# ── 10. Delete ─────────────────────────────────────────────────
result = maintenance_service.delete_maintenance(RID, db)
check("Delete maintenance record", "deleted successfully" in result["message"], result["message"])

# ── 11. Confirm deleted ────────────────────────────────────────
try:
    maintenance_service.get_maintenance_by_id(RID, db)
    check("Deleted record is gone (404)", False, "record still exists")
except HTTPException as e:
    check("Deleted record is gone (404)", e.status_code == 404, f"HTTP {e.status_code}")

# ── 12. All predefined categories available ────────────────────
expected = {"Oil Change", "Tyre Replacement", "Brake Service", "Engine Service", "General Inspection"}
actual = {c.value for c in MaintenanceCategory}
check("All 5 predefined categories defined", actual == expected, str(actual))

print()
print("=" * 60)
print("  All checks complete!")
print("=" * 60)

db.close()

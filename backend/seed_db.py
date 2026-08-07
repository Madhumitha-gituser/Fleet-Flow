import asyncio
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.database import SessionLocal
from app.models.vehicle import Vehicle
from app.models.driver import Driver
from app.models.shipment import Shipment, ShipmentStatus
from app.models.trip import Trip, TripStatus
from app.models.maintenance import Maintenance
from app.models.fuel_record import FuelRecord
from app.models.driver_assignment import DriverAssignment

def seed_database():
    db = SessionLocal()
    try:
        # 1. Vehicles (Indian Registration format)
        vehicles_data = [
            {"vehicle_number": "MH-12-AB-1234", "registration_number": "REG-IND-101", "vehicle_type": "Heavy Truck", "capacity": 20000, "fuel_type": "Diesel", "status": "Available"},
            {"vehicle_number": "KA-01-CD-5678", "registration_number": "REG-IND-102", "vehicle_type": "Light Truck", "capacity": 8000, "fuel_type": "Diesel", "status": "In Transit"},
            {"vehicle_number": "DL-4C-EF-9012", "registration_number": "REG-IND-103", "vehicle_type": "Van", "capacity": 3500, "fuel_type": "Petrol", "status": "Available"},
            {"vehicle_number": "TN-09-GH-3456", "registration_number": "REG-IND-104", "vehicle_type": "Heavy Truck", "capacity": 22000, "fuel_type": "Diesel", "status": "Maintenance"},
            {"vehicle_number": "GJ-01-IJ-7890", "registration_number": "REG-IND-105", "vehicle_type": "Refrigerated Truck", "capacity": 18000, "fuel_type": "Diesel", "status": "Available"},
            {"vehicle_number": "UP-32-KL-1234", "registration_number": "REG-IND-106", "vehicle_type": "Light Truck", "capacity": 7500, "fuel_type": "Electric", "status": "In Transit"},
            {"vehicle_number": "WB-02-MN-5678", "registration_number": "REG-IND-107", "vehicle_type": "Van", "capacity": 3200, "fuel_type": "Petrol", "status": "Available"},
            {"vehicle_number": "TS-07-OP-9012", "registration_number": "REG-IND-108", "vehicle_type": "Heavy Truck", "capacity": 21000, "fuel_type": "Diesel", "status": "In Transit"},
            {"vehicle_number": "RJ-14-QR-3456", "registration_number": "REG-IND-109", "vehicle_type": "Light Truck", "capacity": 8200, "fuel_type": "Petrol", "status": "Available"},
            {"vehicle_number": "KL-01-ST-7890", "registration_number": "REG-IND-110", "vehicle_type": "Refrigerated Truck", "capacity": 17500, "fuel_type": "Diesel", "status": "Maintenance"}
        ]
        
        vehicles = []
        for v_data in vehicles_data:
            vehicle = Vehicle(**v_data)
            db.add(vehicle)
            vehicles.append(vehicle)
        db.commit()
        for v in vehicles:
            db.refresh(v)
            
        # 2. Drivers (Indian Names)
        drivers_data = [
            {"name": "Rajesh Kumar", "license_number": "DL-MH-992134", "phone": "9876543210", "status": "Available"},
            {"name": "Amit Patel", "license_number": "DL-GJ-349812", "phone": "9876543211", "status": "On Trip"},
            {"name": "Suresh Menon", "license_number": "DL-KL-773821", "phone": "9876543212", "status": "Available"},
            {"name": "Vikram Singh", "license_number": "DL-UP-112993", "phone": "9876543213", "status": "Off Duty"},
            {"name": "Manoj Sharma", "license_number": "DL-DL-882734", "phone": "9876543214", "status": "Available"},
            {"name": "Anil Reddy", "license_number": "DL-TS-441029", "phone": "9876543215", "status": "On Trip"},
            {"name": "Karthik Natarajan", "license_number": "DL-TN-663812", "phone": "9876543216", "status": "Available"},
            {"name": "Sandeep Desai", "license_number": "DL-MH-991283", "phone": "9876543217", "status": "On Trip"},
            {"name": "Ravi Yadav", "license_number": "DL-UP-331902", "phone": "9876543218", "status": "Available"},
            {"name": "Dinesh Gupta", "license_number": "DL-RJ-552719", "phone": "9876543219", "status": "Off Duty"}
        ]
        
        drivers = []
        for d_data in drivers_data:
            driver = Driver(**d_data)
            db.add(driver)
            drivers.append(driver)
        db.commit()
        for d in drivers:
            db.refresh(d)
            
        # 3. Shipments (Indian Locations)
        shipments_data = [
            {"tracking_number": "SHP-IND-89102", "sender_name": "Tata Logistics", "receiver_name": "Reliance Retail", "pickup_location": "Mumbai, Maharashtra", "delivery_location": "Pune, Maharashtra", "weight": 4500, "current_status": ShipmentStatus.CREATED, "assigned_driver_id": drivers[0].id, "assigned_vehicle_id": vehicles[0].id},
            {"tracking_number": "SHP-IND-45012", "sender_name": "Mahindra Freight", "receiver_name": "Flipkart Hub", "pickup_location": "Delhi", "delivery_location": "Gurgaon, Haryana", "weight": 2200, "current_status": ShipmentStatus.IN_TRANSIT, "assigned_driver_id": drivers[1].id, "assigned_vehicle_id": vehicles[1].id},
            {"tracking_number": "SHP-IND-99218", "sender_name": "Godrej Supply", "receiver_name": "Amazon Fulfillment", "pickup_location": "Bangalore, Karnataka", "delivery_location": "Chennai, Tamil Nadu", "weight": 8000, "current_status": ShipmentStatus.DELIVERED, "assigned_driver_id": drivers[2].id, "assigned_vehicle_id": vehicles[2].id},
            {"tracking_number": "SHP-IND-33109", "sender_name": "Adani Ports", "receiver_name": "L&T Manufacturing", "pickup_location": "Ahmedabad, Gujarat", "delivery_location": "Surat, Gujarat", "weight": 12000, "current_status": ShipmentStatus.CREATED, "assigned_driver_id": drivers[3].id, "assigned_vehicle_id": vehicles[3].id},
            {"tracking_number": "SHP-IND-11928", "sender_name": "TVS Supply Chain", "receiver_name": "Apollo Tyres Hub", "pickup_location": "Chennai, Tamil Nadu", "delivery_location": "Coimbatore, Tamil Nadu", "weight": 5600, "current_status": ShipmentStatus.IN_TRANSIT, "assigned_driver_id": drivers[4].id, "assigned_vehicle_id": vehicles[4].id},
            {"tracking_number": "SHP-IND-55291", "sender_name": "VRL Logistics", "receiver_name": "D-Mart Stores", "pickup_location": "Hyderabad, Telangana", "delivery_location": "Vijayawada, AP", "weight": 3400, "current_status": ShipmentStatus.DELIVERED, "assigned_driver_id": drivers[5].id, "assigned_vehicle_id": vehicles[5].id},
            {"tracking_number": "SHP-IND-77283", "sender_name": "Blue Dart Express", "receiver_name": "Spencer's Retail", "pickup_location": "Kolkata, West Bengal", "delivery_location": "Bhubaneswar, Odisha", "weight": 2100, "current_status": ShipmentStatus.CREATED, "assigned_driver_id": drivers[6].id, "assigned_vehicle_id": vehicles[6].id},
            {"tracking_number": "SHP-IND-66102", "sender_name": "Safexpress", "receiver_name": "Maruti Suzuki Plant", "pickup_location": "Gurgaon, Haryana", "delivery_location": "Jaipur, Rajasthan", "weight": 8900, "current_status": ShipmentStatus.IN_TRANSIT, "assigned_driver_id": drivers[7].id, "assigned_vehicle_id": vehicles[7].id},
            {"tracking_number": "SHP-IND-22910", "sender_name": "Delhivery", "receiver_name": "Bajaj Auto", "pickup_location": "Pune, Maharashtra", "delivery_location": "Nagpur, Maharashtra", "weight": 6700, "current_status": ShipmentStatus.DELIVERED, "assigned_driver_id": drivers[8].id, "assigned_vehicle_id": vehicles[8].id},
            {"tracking_number": "SHP-IND-88192", "sender_name": "Gati KWE", "receiver_name": "Hero MotoCorp", "pickup_location": "Delhi", "delivery_location": "Chandigarh", "weight": 4200, "current_status": ShipmentStatus.CREATED, "assigned_driver_id": drivers[9].id, "assigned_vehicle_id": vehicles[9].id}
        ]
        
        shipments = []
        for s_data in shipments_data:
            shipment = Shipment(**s_data)
            db.add(shipment)
            shipments.append(shipment)
        db.commit()
        for s in shipments:
            db.refresh(s)

        # 4. Trips
        today = datetime.now()
        trips_data = [
            {"shipment_id": shipments[1].id, "vehicle_id": vehicles[1].id, "driver_id": drivers[1].id, "pickup_location": "Delhi", "destination": "Gurgaon, Haryana", "trip_status": TripStatus.IN_TRANSIT, "scheduled_start_time": today - timedelta(hours=3), "scheduled_end_time": today + timedelta(hours=5)},
            {"shipment_id": shipments[5].id, "vehicle_id": vehicles[5].id, "driver_id": drivers[5].id, "pickup_location": "Hyderabad, Telangana", "destination": "Vijayawada, AP", "trip_status": TripStatus.DELIVERED, "scheduled_start_time": today - timedelta(days=2), "scheduled_end_time": today - timedelta(days=1, hours=2)},
            {"shipment_id": shipments[7].id, "vehicle_id": vehicles[7].id, "driver_id": drivers[7].id, "pickup_location": "Gurgaon, Haryana", "destination": "Jaipur, Rajasthan", "trip_status": TripStatus.IN_TRANSIT, "scheduled_start_time": today - timedelta(hours=5), "scheduled_end_time": today + timedelta(hours=1)},
            {"shipment_id": shipments[0].id, "vehicle_id": vehicles[0].id, "driver_id": drivers[0].id, "pickup_location": "Mumbai, Maharashtra", "destination": "Pune, Maharashtra", "trip_status": TripStatus.CREATED, "scheduled_start_time": today + timedelta(days=1), "scheduled_end_time": today + timedelta(days=1, hours=8)},
            {"shipment_id": shipments[2].id, "vehicle_id": vehicles[2].id, "driver_id": drivers[2].id, "pickup_location": "Bangalore, Karnataka", "destination": "Chennai, Tamil Nadu", "trip_status": TripStatus.DELIVERED, "scheduled_start_time": today - timedelta(days=5), "scheduled_end_time": today - timedelta(days=4, hours=6)},
            {"shipment_id": shipments[4].id, "vehicle_id": vehicles[4].id, "driver_id": drivers[4].id, "pickup_location": "Chennai, Tamil Nadu", "destination": "Coimbatore, Tamil Nadu", "trip_status": TripStatus.CREATED, "scheduled_start_time": today + timedelta(days=2), "scheduled_end_time": today + timedelta(days=2, hours=6)},
            {"shipment_id": shipments[6].id, "vehicle_id": vehicles[6].id, "driver_id": drivers[6].id, "pickup_location": "Kolkata, West Bengal", "destination": "Bhubaneswar, Odisha", "trip_status": TripStatus.DELIVERED, "scheduled_start_time": today - timedelta(days=10), "scheduled_end_time": today - timedelta(days=9, hours=4)},
            {"shipment_id": shipments[8].id, "vehicle_id": vehicles[8].id, "driver_id": drivers[8].id, "pickup_location": "Pune, Maharashtra", "destination": "Nagpur, Maharashtra", "trip_status": TripStatus.CREATED, "scheduled_start_time": today + timedelta(hours=12), "scheduled_end_time": today + timedelta(hours=18)},
            {"shipment_id": shipments[3].id, "vehicle_id": vehicles[3].id, "driver_id": drivers[3].id, "pickup_location": "Ahmedabad, Gujarat", "destination": "Surat, Gujarat", "trip_status": TripStatus.DELIVERED, "scheduled_start_time": today - timedelta(days=15), "scheduled_end_time": today - timedelta(days=14, hours=2)},
            {"shipment_id": shipments[9].id, "vehicle_id": vehicles[9].id, "driver_id": drivers[9].id, "pickup_location": "Delhi", "destination": "Chandigarh", "trip_status": TripStatus.DELIVERED, "scheduled_start_time": today - timedelta(days=20), "scheduled_end_time": today - timedelta(days=19, hours=5)}
        ]
        
        trips = []
        for t_data in trips_data:
            trip = Trip(**t_data)
            db.add(trip)
            trips.append(trip)
        db.commit()
        for t in trips:
            db.refresh(t)
            
        # 5. Maintenance
        maintenance_data = [
            {"vehicle_id": vehicles[3].id, "category": "Engine Service", "service_date": today.date() - timedelta(days=2), "service_cost": 15000.00, "service_provider": "Tata Motors Service", "status": "In Progress", "notes": "Engine knocking sounds reported by driver."},
            {"vehicle_id": vehicles[9].id, "category": "Brake Service", "service_date": today.date() - timedelta(days=1), "service_cost": 4500.00, "service_provider": "Ashok Leyland Garage", "status": "In Progress", "notes": "Replacing worn brake pads."},
            {"vehicle_id": vehicles[0].id, "category": "Oil Change", "service_date": today.date() - timedelta(days=45), "service_cost": 2500.00, "service_provider": "Castrol Auto Service", "status": "Completed", "next_service_date": today.date() + timedelta(days=45)},
            {"vehicle_id": vehicles[1].id, "category": "Tyre Replacement", "service_date": today.date() - timedelta(days=90), "service_cost": 32000.00, "service_provider": "MRF Tyres Outlet", "status": "Completed", "next_service_date": today.date() + timedelta(days=180)},
            {"vehicle_id": vehicles[2].id, "category": "General Inspection", "service_date": today.date() - timedelta(days=15), "service_cost": 1500.00, "service_provider": "Mahindra First Choice", "status": "Completed", "next_service_date": today.date() + timedelta(days=75)},
            {"vehicle_id": vehicles[4].id, "category": "Oil Change", "service_date": today.date() + timedelta(days=5), "service_cost": None, "service_provider": "Castrol Auto Service", "status": "Scheduled", "notes": "Routine oil change"},
            {"vehicle_id": vehicles[5].id, "category": "Engine Service", "service_date": today.date() - timedelta(days=120), "service_cost": 21000.00, "service_provider": "Bosch Car Service", "status": "Completed"},
            {"vehicle_id": vehicles[6].id, "category": "Brake Service", "service_date": today.date() + timedelta(days=10), "service_cost": None, "service_provider": "Ashok Leyland Garage", "status": "Scheduled"},
            {"vehicle_id": vehicles[7].id, "category": "Tyre Replacement", "service_date": today.date() - timedelta(days=30), "service_cost": 28000.00, "service_provider": "CEAT Shoppe", "status": "Completed", "next_service_date": today.date() + timedelta(days=330)},
            {"vehicle_id": vehicles[8].id, "category": "General Inspection", "service_date": today.date() - timedelta(days=60), "service_cost": 1200.00, "service_provider": "Mahindra First Choice", "status": "Completed", "next_service_date": today.date() + timedelta(days=30)}
        ]
        
        for m_data in maintenance_data:
            maintenance = Maintenance(**m_data)
            db.add(maintenance)
        db.commit()

        # 6. Fuel Records
        fuel_data = [
            {"vehicle_id": vehicles[0].id, "driver_id": drivers[0].id, "fuel_date": today.date() - timedelta(days=5), "fuel_quantity": 120.5, "fuel_cost": 11500.00, "odometer_reading": 45000, "fuel_station": "IndianOil - Mumbai Pune Exp", "remarks": "Refueled before departure"},
            {"vehicle_id": vehicles[1].id, "driver_id": drivers[1].id, "fuel_date": today.date() - timedelta(days=1), "fuel_quantity": 85.0, "fuel_cost": 8200.00, "odometer_reading": 52000, "fuel_station": "Bharat Petroleum - NH48", "remarks": ""},
            {"vehicle_id": vehicles[2].id, "driver_id": drivers[2].id, "fuel_date": today.date() - timedelta(days=10), "fuel_quantity": 65.2, "fuel_cost": 6500.00, "odometer_reading": 12000, "fuel_station": "Hindustan Petroleum - Bangalore", "remarks": ""},
            {"vehicle_id": vehicles[4].id, "driver_id": drivers[4].id, "fuel_date": today.date() - timedelta(days=2), "fuel_quantity": 95.5, "fuel_cost": 9100.00, "odometer_reading": 34000, "fuel_station": "Reliance Petrol Pump - Chennai", "remarks": ""},
            {"vehicle_id": vehicles[5].id, "driver_id": drivers[5].id, "fuel_date": today.date() - timedelta(days=4), "fuel_quantity": 78.0, "fuel_cost": 7500.00, "odometer_reading": 61000, "fuel_station": "IndianOil - Hyderabad", "remarks": ""},
            {"vehicle_id": vehicles[6].id, "driver_id": drivers[6].id, "fuel_date": today.date() - timedelta(days=15), "fuel_quantity": 55.0, "fuel_cost": 5300.00, "odometer_reading": 22000, "fuel_station": "Bharat Petroleum - Kolkata", "remarks": ""},
            {"vehicle_id": vehicles[7].id, "driver_id": drivers[7].id, "fuel_date": today.date() - timedelta(days=1), "fuel_quantity": 110.0, "fuel_cost": 10500.00, "odometer_reading": 87000, "fuel_station": "Hindustan Petroleum - Gurgaon", "remarks": ""},
            {"vehicle_id": vehicles[8].id, "driver_id": drivers[8].id, "fuel_date": today.date() - timedelta(days=8), "fuel_quantity": 72.4, "fuel_cost": 6900.00, "odometer_reading": 45000, "fuel_station": "Nayara Energy - Pune", "remarks": ""},
            {"vehicle_id": vehicles[3].id, "driver_id": drivers[3].id, "fuel_date": today.date() - timedelta(days=20), "fuel_quantity": 140.0, "fuel_cost": 13400.00, "odometer_reading": 92000, "fuel_station": "IndianOil - Ahmedabad", "remarks": ""},
            {"vehicle_id": vehicles[9].id, "driver_id": drivers[9].id, "fuel_date": today.date() - timedelta(days=25), "fuel_quantity": 135.5, "fuel_cost": 12900.00, "odometer_reading": 105000, "fuel_station": "Bharat Petroleum - Delhi", "remarks": ""}
        ]
        
        for f_data in fuel_data:
            fuel = FuelRecord(**f_data)
            db.add(fuel)
        db.commit()
        
        print("Successfully seeded 10 realistic Indian records for each main entity!")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

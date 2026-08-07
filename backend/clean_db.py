import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.database import SessionLocal, engine
from sqlalchemy import text

def clean_database():
    with engine.connect() as conn:
        try:
            print("Truncating tables (except users)...")
            conn.execute(text("""
                TRUNCATE TABLE 
                    audit_logs,
                    driver_attendances,
                    driver_assignments,
                    fuel_records,
                    maintenance_alerts,
                    maintenance,
                    trips,
                    shipments,
                    drivers,
                    vehicles
                CASCADE;
            """))
            conn.commit()
            print("Database cleaned successfully. Left only the user accounts.")
        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()

if __name__ == "__main__":
    clean_database()

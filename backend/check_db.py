from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT id, name, email, role FROM users LIMIT 5"))
    print("=== users ===")
    for row in result:
        print(row)

    result = conn.execute(text("SELECT id, vehicle_number FROM vehicles LIMIT 5"))
    print("\n=== vehicles ===")
    for row in result:
        print(row)

from database import engine, SessionLocal
from sqlalchemy import text

def test_connection():
    try:
        # Attempt to connect and execute a simple query
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("[OK] Connection to PostgreSQL successful!")
            
        # Attempt to create a session
        db = SessionLocal()
        print("[OK] SQLAlchemy Session created successfully!")
        db.close()
        
    except Exception as e:
        print("[ERROR] Connection failed!")
        print(f"Error detail: {e}")

if __name__ == "__main__":
    test_connection()

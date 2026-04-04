from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models

def seed_circles():
    # Initialize database session
    db: Session = SessionLocal()
    
    # Define a sample circle with a strict Tag Schema
    # The 'required' dict defines: {Tag_Name: Expected_Type}
    sample_tag_schema = {
        "required": {
            "Major": "str",      # Must be a string
            "GPA": "float",      # Must be a number (int or float)
            "Skills": "list"     # Must be a list, e.g., ["Python", "C++"]
        }
    }

    # Check if the test circle already exists to avoid duplicates
    existing_circle = db.query(models.Circle).filter(models.Circle.name == "EECS Career Fair").first()
    
    if not existing_circle:
        new_circle = models.Circle(
            name="EECS Career Fair",
            tag_schema=sample_tag_schema
        )
        db.add(new_circle)
        db.commit()
        print("Successfully created 'EECS Career Fair' circle with Tag Schema.")
    else:
        print("Circle already exists. Skipping...")

    db.close()

if __name__ == "__main__":
    # Ensure tables are created before seeding
    models.Base.metadata.create_all(bind=engine)
    seed_circles()
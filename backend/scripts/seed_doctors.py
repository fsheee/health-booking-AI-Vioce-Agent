"""
Usage: uv run python scripts/seed_doctors.py <org_slug>

Creates cardiologist and dermatologist doctor records in the given org.
If users don't exist, they are created.  Existing doctor records are updated.
"""
import sys

from passlib.context import CryptContext
from sqlmodel import Session, create_engine, select

from app.core.config import settings
from app.models.doctor import Doctor
from app.models.organization import Organization
from app.models.user import User, UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DOCTORS = [
    ("Dr. John Heart", "Cardiology", "LIC-CARDIO-001"),
    ("Dr. Emma Skin", "Dermatology", "LIC-DERMA-001"),
]


def main(org_slug: str):
    engine = create_engine(str(settings.database_url))
    with Session(engine) as session:
        org = session.exec(select(Organization).where(Organization.slug == org_slug)).first()
        if not org:
            print(f"Organization '{org_slug}' not found. Creating it.")
            org = Organization(name=org_slug, slug=org_slug)
            session.add(org)
            session.commit()
            session.refresh(org)

        print(f"Using organization: {org.name} ({org.id})")

        for full_name, specialization, license_number in DOCTORS:
            email = f"{specialization.lower()}@clinic.local"

            user = session.exec(select(User).where(User.email == email)).first()
            if user:
                print(f"  User exists: {user.full_name} ({user.email})")
                # Check if user already has a doctor record in ANY org
                existing_doctor = session.exec(
                    select(Doctor).where(Doctor.user_id == user.id)
                ).first()
                if existing_doctor:
                    # Move existing doctor to this org and update specialization
                    existing_doctor.org_id = org.id
                    existing_doctor.specialization = specialization
                    existing_doctor.license_number = license_number
                    existing_doctor.is_available = True
                    session.add(existing_doctor)
                    session.commit()
                    print(f"  Moved doctor to this org: {user.full_name} -> {specialization}")
                    continue
            else:
                user = User(
                    org_id=org.id,
                    hashed_password=pwd_context.hash("password123"),
                    email=email,
                    full_name=full_name,
                    role=UserRole.doctor,
                    phone="",
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                print(f"  Created user: {user.full_name} ({user.email})")

            # No existing doctor for this user — create one
            doctor = Doctor(
                user_id=user.id,
                org_id=org.id,
                specialization=specialization,
                license_number=license_number,
                is_available=True,
            )
            session.add(doctor)
            session.commit()
            print(f"  Created doctor: {user.full_name} -> {specialization}")

        print("\nDone. Restart the server and test.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python scripts/seed_doctors.py <org_slug>")
        sys.exit(1)
    main(sys.argv[1])

from sqlmodel import SQLModel, create_engine

from app.models import *  # noqa: F401, F403

engine = create_engine("sqlite:///./dev.db")
SQLModel.metadata.create_all(engine)
print("Tables created successfully")

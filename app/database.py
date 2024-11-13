from sqlalchemy import create_engine, Column, Integer, String, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import load_config

config = load_config()

# Database connection string
DATABASE_URL = config.get('database_url', 'sqlite:///./fijiAI.db')

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative models
Base = declarative_base()

class ImageMetadata(Base):
    """
    Model for storing image metadata.
    """
    __tablename__ = "image_metadata"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, unique=True, index=True)
    image_metadata = Column("metadata", JSON)  # Note the use of "metadata" as the actual column name
    original_path = Column(Text)  # Field to store the path of the original file
    preview_path = Column(Text)  # Field to store the path of the preview file
    original_file_type = Column(String)  # Field to store the original file type
    file_type = Column(String)  # Add this line to include file_type

def get_db():
    """
    Get a database session.

    Yields:
        Session: A SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Update the table to reflect the changes in the model
Base.metadata.drop_all(bind=engine, tables=[ImageMetadata.__table__])
Base.metadata.create_all(bind=engine, tables=[ImageMetadata.__table__])

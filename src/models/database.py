from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resume_evaluation.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class JobDescription(Base):
    __tablename__ = "job_descriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255))
    location = Column(String(255))
    raw_text = Column(Text, nullable=False)
    parsed_requirements = Column(Text)  # JSON string of parsed requirements
    must_have_skills = Column(Text)  # JSON string
    good_to_have_skills = Column(Text)  # JSON string
    qualifications = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    evaluations = relationship("ResumeEvaluation", back_populates="job_description")

class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    student_name = Column(String(255))
    student_email = Column(String(255))
    raw_text = Column(Text, nullable=False)
    parsed_content = Column(Text)  # JSON string of parsed content
    skills = Column(Text)  # JSON string
    education = Column(Text)  # JSON string
    experience = Column(Text)  # JSON string
    projects = Column(Text)  # JSON string
    certifications = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    evaluations = relationship("ResumeEvaluation", back_populates="resume")

class ResumeEvaluation(Base):
    __tablename__ = "resume_evaluations"
    
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=False)
    
    # Scoring results
    relevance_score = Column(Float, nullable=False)  # 0-100
    verdict = Column(String(20), nullable=False)  # High/Medium/Low
    hard_match_score = Column(Float)
    semantic_match_score = Column(Float)
    
    # Analysis results
    missing_skills = Column(Text)  # JSON string
    missing_certifications = Column(Text)  # JSON string
    missing_projects = Column(Text)  # JSON string
    improvement_suggestions = Column(Text)  # JSON string
    
    # Metadata
    evaluation_details = Column(Text)  # JSON string with detailed analysis
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    resume = relationship("Resume", back_populates="evaluations")
    job_description = relationship("JobDescription", back_populates="evaluations")

class EvaluationLog(Base):
    __tablename__ = "evaluation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(Integer, ForeignKey("resume_evaluations.id"))
    log_type = Column(String(50))  # INFO, WARNING, ERROR
    message = Column(Text)
    details = Column(Text)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)

# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

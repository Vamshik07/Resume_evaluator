from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
import uvicorn
import os
import json
import logging
from typing import List, Optional
import uuid
from datetime import datetime
import sys
import numpy as np


def convert_numpy_types(obj):
    """Recursively convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    return obj

print("=== BACKEND STARTING ===", flush=True)

# Add project root to sys.path to fix src import issue
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our modules
print("Loading database module...", flush=True)
from src.models.database import get_db, create_tables, JobDescription, Resume, ResumeEvaluation
print("Loading resume parser module...", flush=True)
from src.parsers.resume_parser import ResumeParser
print("Loading job description parser module...", flush=True)
from src.parsers.jd_parser import JobDescriptionParser
print("Loading hard matching module...", flush=True)
from src.matching.hard_matching import HardMatching
print("Loading semantic matching module...", flush=True)
from src.matching.semantic_matching import SemanticMatching
print("Loading scoring engine module...", flush=True)
from src.scoring.scoring_engine import ScoringEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
print("Initializing FastAPI...", flush=True)
app = FastAPI(
    title="Automated Resume Relevance Check System",
    description="AI-powered resume evaluation system for Innomatics Research Labs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
print("Instantiating ResumeParser...", flush=True)
resume_parser = ResumeParser()
print("Instantiating JobDescriptionParser...", flush=True)
jd_parser = JobDescriptionParser()
print("Instantiating HardMatching...", flush=True)
hard_matcher = HardMatching()
print("Instantiating SemanticMatching...", flush=True)
semantic_matcher = SemanticMatching()
print("Instantiating ScoringEngine...", flush=True)
scoring_engine = ScoringEngine()

# Create database tables
print("Creating database tables...", flush=True)
create_tables()
print("Database tables ready.", flush=True)

# Ensure upload directory exists
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
print("=== BACKEND INITIALIZED AND READY ===", flush=True)

# ... (rest of your routes remain unchanged)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Automated Resume Relevance Check System",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/upload/job-description")
async def upload_job_description(
    file: UploadFile = File(...),
    title: str = Form(""),
    company: str = Form(""),
    location: str = Form(""),
    db: Session = Depends(get_db)
):
    """Upload and parse job description"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.docx', '.doc', '.txt')):
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, DOCX, or TXT files.")
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1]
        file_path = os.path.join(UPLOAD_DIR, f"jd_{file_id}.{file_extension}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract text from file
        if file_extension == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
        else:
            # Use resume parser for PDF/DOCX
            raw_text = resume_parser.extract_text(file_path)
        
        if not raw_text:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Parse job description
        parsed_jd = jd_parser.parse_job_description(raw_text)
        
        # Create database record
        jd_record = JobDescription(
            title=title or parsed_jd.get("job_title", "Unknown Position"),
            company=company or parsed_jd.get("company_info", {}).get("name", ""),
            location=location or parsed_jd.get("company_info", {}).get("location", ""),
            raw_text=raw_text,
            parsed_requirements=json.dumps(parsed_jd),
            must_have_skills=json.dumps(parsed_jd.get("required_skills", [])),
            good_to_have_skills=json.dumps(parsed_jd.get("preferred_skills", [])),
            qualifications=json.dumps(parsed_jd.get("qualifications", []))
        )
        
        db.add(jd_record)
        db.commit()
        db.refresh(jd_record)
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return {
            "message": "Job description uploaded successfully",
            "job_description_id": jd_record.id,
            "parsed_data": parsed_jd
        }
        
    except Exception as e:
        logger.error(f"Error uploading job description: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing job description: {str(e)}")

@app.post("/upload/resume")
async def upload_resume(
    file: UploadFile = File(...),
    student_name: str = Form(""),
    student_email: str = Form(""),
    db: Session = Depends(get_db)
):
    """Upload and parse resume"""
    try:
        # Validate file type
        if not file.filename.lower().endswith(('.pdf', '.docx', '.doc')):
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF or DOCX files.")
        
        # Save uploaded file
        file_id = str(uuid.uuid4())
        file_extension = file.filename.split('.')[-1]
        file_path = os.path.join(UPLOAD_DIR, f"resume_{file_id}.{file_extension}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Parse resume
        parsed_resume = resume_parser.parse_resume(file_path)
        
        if not parsed_resume.get("raw_text"):
            raise HTTPException(status_code=400, detail="Could not extract text from resume")
        
        # Create database record
        resume_record = Resume(
            filename=file.filename,
            student_name=student_name or parsed_resume.get("contact_info", {}).get("name", ""),
            student_email=student_email or parsed_resume.get("contact_info", {}).get("email", ""),
            raw_text=parsed_resume["raw_text"],
            parsed_content=json.dumps(parsed_resume),
            skills=json.dumps(parsed_resume.get("skills", [])),
            education=json.dumps(parsed_resume.get("education", [])),
            experience=json.dumps(parsed_resume.get("experience", [])),
            projects=json.dumps(parsed_resume.get("projects", [])),
            certifications=json.dumps(parsed_resume.get("certifications", []))
        )
        
        db.add(resume_record)
        db.commit()
        db.refresh(resume_record)
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return {
            "message": "Resume uploaded successfully",
            "resume_id": resume_record.id,
            "parsed_data": parsed_resume
        }
        
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")

@app.post("/evaluate")
async def evaluate_resume(
    resume_id: int = Form(...),
    job_description_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Evaluate resume against job description"""
    try:
        # Get resume and job description from database
        resume_record = db.query(Resume).filter(Resume.id == resume_id).first()
        jd_record = db.query(JobDescription).filter(JobDescription.id == job_description_id).first()
        
        if not resume_record:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        if not jd_record:
            raise HTTPException(status_code=404, detail="Job description not found")
        
        # Parse the stored data
        resume_data = json.loads(resume_record.parsed_content)
        jd_data = json.loads(jd_record.parsed_requirements)
        
        # Perform hard matching
        hard_match_results = hard_matcher.calculate_hard_match_score(resume_data, jd_data)
        
        # Perform semantic matching
        semantic_match_results = semantic_matcher.calculate_semantic_match_score(resume_data, jd_data)
        
        # Generate final analysis
        analysis = scoring_engine.generate_detailed_analysis(
            resume_data, jd_data, hard_match_results, semantic_match_results
        )
        
        # Convert all numpy types to native Python types for JSON safety
        analysis = convert_numpy_types(analysis)
        hard_match_results = convert_numpy_types(hard_match_results)
        semantic_match_results = convert_numpy_types(semantic_match_results)
        
        # Create evaluation record
        evaluation_record = ResumeEvaluation(
            resume_id=resume_id,
            job_description_id=job_description_id,
            relevance_score=float(analysis["relevance_score"]),
            verdict=analysis["verdict"],
            hard_match_score=float(hard_match_results.get("hard_match_score", 0.0)),
            semantic_match_score=float(semantic_match_results.get("semantic_score", 0.0)),
            missing_skills=json.dumps(analysis["missing_elements"].get("skills", [])),
            missing_certifications=json.dumps(analysis["missing_elements"].get("certifications", [])),
            missing_projects=json.dumps(analysis["missing_elements"].get("projects", [])),
            improvement_suggestions=json.dumps(analysis["improvement_suggestions"]),
            evaluation_details=json.dumps(analysis)
        )
        
        db.add(evaluation_record)
        db.commit()
        db.refresh(evaluation_record)
        
        return {
            "message": "Evaluation completed successfully",
            "evaluation_id": evaluation_record.id,
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error evaluating resume: {e}")
        raise HTTPException(status_code=500, detail=f"Error evaluating resume: {str(e)}")

@app.get("/results")
async def get_results(
    job_description_id: Optional[int] = None,
    verdict: Optional[str] = None,
    min_score: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get evaluation results with optional filtering"""
    try:
        query = db.query(ResumeEvaluation)
        
        if job_description_id:
            query = query.filter(ResumeEvaluation.job_description_id == job_description_id)
        
        if verdict:
            query = query.filter(ResumeEvaluation.verdict == verdict)
        
        if min_score:
            query = query.filter(ResumeEvaluation.relevance_score >= min_score)
        
        # Order by relevance score descending
        query = query.order_by(ResumeEvaluation.relevance_score.desc())
        
        # Limit results
        evaluations = query.limit(limit).all()
        
        results = []
        for eval_record in evaluations:
            # Get related resume and job description
            resume = db.query(Resume).filter(Resume.id == eval_record.resume_id).first()
            jd = db.query(JobDescription).filter(JobDescription.id == eval_record.job_description_id).first()
            
            result = {
                "evaluation_id": eval_record.id,
                "resume_id": eval_record.resume_id,
                "job_description_id": eval_record.job_description_id,
                "relevance_score": eval_record.relevance_score,
                "verdict": eval_record.verdict,
                "hard_match_score": eval_record.hard_match_score,
                "semantic_match_score": eval_record.semantic_match_score,
                "student_name": resume.student_name if resume else "Unknown",
                "job_title": jd.title if jd else "Unknown",
                "company": jd.company if jd else "Unknown",
                "evaluation_date": eval_record.created_at.isoformat(),
                "missing_skills": json.loads(eval_record.missing_skills or "[]"),
                "improvement_suggestions": json.loads(eval_record.improvement_suggestions or "[]")
            }
            results.append(result)
        
        return {
            "results": results,
            "total_count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving results: {str(e)}")

@app.get("/evaluations")
async def get_evaluations(db: Session = Depends(get_db)):
    """Get all evaluations"""
    try:
        evaluations = db.query(ResumeEvaluation).all()
        results = []
        
        for eval_record in evaluations:
            result = {
                "id": eval_record.id,
                "resume_id": eval_record.resume_id,
                "job_description_id": eval_record.job_description_id,
                "relevance_score": eval_record.relevance_score,
                "verdict": eval_record.verdict,
                "hard_match_score": eval_record.hard_match_score,
                "semantic_match_score": eval_record.semantic_match_score,
                "evaluation_date": eval_record.created_at.isoformat(),
                "missing_skills": json.loads(eval_record.missing_skills or "[]"),
                "improvement_suggestions": json.loads(eval_record.improvement_suggestions or "[]")
            }
            results.append(result)
        
        return {
            "evaluations": results,
            "total_count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error getting evaluations: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving evaluations: {str(e)}")

@app.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    try:
        # Get basic counts
        total_resumes = db.query(Resume).count()
        total_jds = db.query(JobDescription).count()
        total_evaluations = db.query(ResumeEvaluation).count()
        
        # Get verdict distribution
        verdict_counts = db.query(
            ResumeEvaluation.verdict,
            func.count(ResumeEvaluation.id)
        ).group_by(ResumeEvaluation.verdict).all()
        
        verdict_distribution = {verdict: count for verdict, count in verdict_counts}
        
        # Get average scores
        avg_scores = db.query(
            func.avg(ResumeEvaluation.relevance_score),
            func.avg(ResumeEvaluation.hard_match_score),
            func.avg(ResumeEvaluation.semantic_match_score)
        ).first()
        
        return {
            "total_resumes": total_resumes,
            "total_job_descriptions": total_jds,
            "total_evaluations": total_evaluations,
            "verdict_distribution": verdict_distribution,
            "average_scores": {
                "relevance_score": round(avg_scores[0] or 0, 2),
                "hard_match_score": round(avg_scores[1] or 0, 2),
                "semantic_match_score": round(avg_scores[2] or 0, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard stats: {str(e)}")

@app.get("/resumes")
async def get_resumes(limit: int = 50, db: Session = Depends(get_db)):
    """Get list of uploaded resumes"""
    try:
        resumes = db.query(Resume).order_by(Resume.created_at.desc()).limit(limit).all()
        
        results = []
        for resume in resumes:
            result = {
                "id": resume.id,
                "filename": resume.filename,
                "student_name": resume.student_name,
                "student_email": resume.student_email,
                "upload_date": resume.created_at.isoformat(),
                "skills": json.loads(resume.skills or "[]")
            }
            results.append(result)
        
        return {"resumes": results}
        
    except Exception as e:
        logger.error(f"Error getting resumes: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving resumes: {str(e)}")

@app.get("/job-descriptions")
async def get_job_descriptions(limit: int = 50, db: Session = Depends(get_db)):
    """Get list of uploaded job descriptions"""
    try:
        jds = db.query(JobDescription).order_by(JobDescription.created_at.desc()).limit(limit).all()
        
        results = []
        for jd in jds:
            result = {
                "id": jd.id,
                "title": jd.title,
                "company": jd.company,
                "location": jd.location,
                "upload_date": jd.created_at.isoformat(),
                "required_skills": json.loads(jd.must_have_skills or "[]")
            }
            results.append(result)
        
        return {"job_descriptions": results}
        
    except Exception as e:
        logger.error(f"Error getting job descriptions: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving job descriptions: {str(e)}")



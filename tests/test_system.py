#!/usr/bin/env python3
"""
Test script for the Resume Evaluation System
"""

import sys
import os
import json
import requests
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from parsers.resume_parser import ResumeParser
from parsers.jd_parser import JobDescriptionParser
from matching.hard_matching import HardMatching
from matching.semantic_matching import SemanticMatching
from scoring.scoring_engine import ScoringEngine

def test_resume_parser():
    """Test resume parser functionality"""
    print("🧪 Testing Resume Parser...")
    
    parser = ResumeParser()
    
    # Test with sample resume text
    sample_resume_text = """
    John Doe
    Software Engineer
    Email: john.doe@email.com
    Phone: +91-9876543210
    
    TECHNICAL SKILLS
    - Python (3 years)
    - Django, FastAPI
    - PostgreSQL, MySQL
    - Git, GitHub
    - REST API development
    - Docker
    - AWS
    
    EXPERIENCE
    Software Engineer - TechCorp (2021-2024)
    - Developed web applications using Django
    - Built REST APIs
    - Implemented database optimization
    
    EDUCATION
    Bachelor of Technology in Computer Science
    Indian Institute of Technology (2017-2021)
    
    PROJECTS
    E-commerce Platform
    - Built using Django and React
    - Implemented payment gateway
    - Deployed on AWS
    """
    
    # Create a temporary file
    with open("temp_resume.txt", "w") as f:
        f.write(sample_resume_text)
    
    try:
        result = parser.parse_resume("temp_resume.txt")
        
        print(f"✅ Resume parsed successfully")
        print(f"   - Skills found: {len(result.get('skills', []))}")
        print(f"   - Experience entries: {len(result.get('experience', []))}")
        print(f"   - Education entries: {len(result.get('education', []))}")
        print(f"   - Projects: {len(result.get('projects', []))}")
        
        return True
    except Exception as e:
        print(f"❌ Resume parser test failed: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists("temp_resume.txt"):
            os.remove("temp_resume.txt")

def test_jd_parser():
    """Test job description parser functionality"""
    print("🧪 Testing Job Description Parser...")
    
    parser = JobDescriptionParser()
    
    sample_jd_text = """
    Software Engineer - Python
    
    We are looking for a talented Software Engineer with strong Python skills.
    
    Required Skills:
    - Python (3+ years experience)
    - Django/FastAPI framework
    - SQL/PostgreSQL
    - Git version control
    - REST API development
    - Docker containerization
    
    Preferred Skills:
    - AWS cloud services
    - Machine Learning basics
    - React.js frontend
    
    Qualifications:
    - Bachelor's degree in Computer Science
    - 3-5 years of software development experience
    
    Responsibilities:
    - Develop and maintain web applications
    - Collaborate with cross-functional teams
    - Write clean, maintainable code
    """
    
    try:
        result = parser.parse_job_description(sample_jd_text)
        
        print(f"✅ Job description parsed successfully")
        print(f"   - Job title: {result.get('job_title', 'N/A')}")
        print(f"   - Required skills: {len(result.get('required_skills', []))}")
        print(f"   - Preferred skills: {len(result.get('preferred_skills', []))}")
        print(f"   - Qualifications: {len(result.get('qualifications', []))}")
        
        return True
    except Exception as e:
        print(f"❌ Job description parser test failed: {e}")
        return False

def test_hard_matching():
    """Test hard matching functionality"""
    print("🧪 Testing Hard Matching...")
    
    matcher = HardMatching()
    
    # Sample resume data
    resume_data = {
        "skills": ["python", "django", "postgresql", "git", "docker"],
        "education": [{"degree": "Bachelor of Technology in Computer Science"}],
        "experience": [{"title": "Software Engineer", "duration": "3 years"}],
        "certifications": ["aws certified developer"],
        "cleaned_text": "Python developer with Django experience and PostgreSQL knowledge."
    }
    
    # Sample job description data
    jd_data = {
        "required_skills": ["python", "django", "fastapi", "postgresql", "git"],
        "preferred_skills": ["aws", "docker", "react"],
        "qualifications": ["Bachelor's degree in Computer Science"],
        "experience_requirements": {"min_years": 3, "level": "mid_level"},
        "cleaned_text": "Looking for Python developer with Django and FastAPI experience."
    }
    
    try:
        result = matcher.calculate_hard_match_score(resume_data, jd_data)
        
        print(f"✅ Hard matching completed successfully")
        print(f"   - Hard match score: {result.get('hard_match_score', 0):.2f}")
        print(f"   - Exact skill matches: {len(result.get('exact_skill_match', {}).get('exact_matches', []))}")
        print(f"   - Education score: {result.get('education_match', {}).get('education_score', 0):.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Hard matching test failed: {e}")
        return False

def test_semantic_matching():
    """Test semantic matching functionality"""
    print("🧪 Testing Semantic Matching...")

    # Allow CI/offline skips to avoid external calls/downloads
    if os.getenv("SKIP_SEMANTIC_TESTS", "false").lower() == "true":
        print("⚠️  Skipping semantic matching test (SKIP_SEMANTIC_TESTS is true)")
        return True

    # Skip if no Google API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Skipping semantic matching test (no Google API key)")
        return True
    
    matcher = SemanticMatching()
    
    # Sample data
    resume_data = {
        "cleaned_text": "Experienced Python developer with Django framework knowledge and PostgreSQL database experience."
    }
    
    jd_data = {
        "required_skills": ["python", "django", "fastapi", "postgresql"],
        "cleaned_text": "We need a Python developer with web framework experience and database skills."
    }
    
    try:
        result = matcher.calculate_semantic_match_score(resume_data, jd_data)
        
        print(f"✅ Semantic matching completed successfully")
        print(f"   - Semantic score: {result.get('semantic_score', 0):.2f}")
        print(f"   - Overall similarity: {result.get('overall_similarity', 0):.2f}")
        print(f"   - Semantic skill matches: {len(result.get('semantic_skills', {}).get('semantic_matches', []))}")
        
        return True
    except Exception as e:
        print(f"❌ Semantic matching test failed: {e}")
        return False

def test_scoring_engine():
    """Test scoring engine functionality"""
    print("🧪 Testing Scoring Engine...")
    
    engine = ScoringEngine()
    
    # Sample hard match results
    hard_match_results = {
        "hard_match_score": 0.75,
        "exact_skill_match": {"exact_matches": ["python", "django"]},
        "education_match": {"education_score": 0.8},
        "experience_match": {"experience_score": 0.7}
    }
    
    # Sample semantic match results
    semantic_match_results = {
        "semantic_score": 0.65,
        "overall_similarity": 0.7,
        "semantic_skills": {"semantic_matches": [{"similarity_score": 0.8}]},
        "llm_analysis": {"fit_score": 70, "strengths": ["Python experience"]}
    }
    
    try:
        final_score = engine.calculate_final_score(hard_match_results, semantic_match_results)
        verdict = engine.determine_verdict(final_score)
        percentage = engine.convert_to_percentage(final_score)
        
        print(f"✅ Scoring engine completed successfully")
        print(f"   - Final score: {final_score:.2f}")
        print(f"   - Percentage: {percentage}%")
        print(f"   - Verdict: {verdict}")
        
        return True
    except Exception as e:
        print(f"❌ Scoring engine test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("🧪 Testing API Endpoints...")
    
    base_url = "http://localhost:8000"
    
    try:
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test root endpoint
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Root endpoint working")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
        
        # Test dashboard stats
        response = requests.get(f"{base_url}/dashboard/stats", timeout=5)
        if response.status_code == 200:
            print("✅ Dashboard stats endpoint working")
        else:
            print(f"❌ Dashboard stats endpoint failed: {response.status_code}")
            return False
        
        return True
    except requests.exceptions.ConnectionError:
        print("⚠️  API server not running. Start the server with: python start_server.py")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Running Resume Evaluation System Tests")
    print("=" * 50)
    
    tests = [
        test_resume_parser,
        test_jd_parser,
        test_hard_matching,
        test_semantic_matching,
        test_scoring_engine,
        test_api_endpoints
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

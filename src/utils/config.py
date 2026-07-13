import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the application"""
    
    # API Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gemini-pro")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resume_evaluation.db")
    
    # Application Configuration
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # File Upload Configuration
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./data/uploads")
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}
    
    # Scoring Weights
    HARD_MATCH_WEIGHT = float(os.getenv("HARD_MATCH_WEIGHT", "0.4"))
    SEMANTIC_MATCH_WEIGHT = float(os.getenv("SEMANTIC_MATCH_WEIGHT", "0.6"))
    
    # Matching Thresholds
    FUZZY_MATCH_THRESHOLD = 80
    SEMANTIC_MATCH_THRESHOLD = 0.3
    
    # Verdict Thresholds
    HIGH_FIT_THRESHOLD = 0.8
    MEDIUM_FIT_THRESHOLD = 0.6
    
    @classmethod
    def validate_config(cls):
        """Validate configuration settings"""
        errors = []
        
        if not cls.GOOGLE_API_KEY:
            errors.append("GOOGLE_API_KEY is required")
        
        if cls.HARD_MATCH_WEIGHT + cls.SEMANTIC_MATCH_WEIGHT != 1.0:
            errors.append("HARD_MATCH_WEIGHT + SEMANTIC_MATCH_WEIGHT must equal 1.0")
        
        if cls.MAX_FILE_SIZE <= 0:
            errors.append("MAX_FILE_SIZE must be positive")
        
        return errors

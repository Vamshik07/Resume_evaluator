import re
import json
from typing import Dict, List, Optional, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeParser:
    def __init__(self):
        """Initialize the resume parser (heavy deps loaded lazily)"""
        self.nlp = None
        self.matcher = None
    
    def _load_spacy(self):
        """Lazily load spaCy model"""
        if self.nlp is not None:
            return
        try:
            import spacy
            from spacy.matcher import Matcher
            self.nlp = spacy.load("en_core_web_sm")
            self.matcher = Matcher(self.nlp.vocab)
            self._setup_patterns()
        except OSError:
            logger.warning("spaCy model not found. Please install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        except Exception as e:
            logger.warning(f"spaCy load failed: {e}")
            self.nlp = None
    
    def _setup_patterns(self):
        """Set up spaCy patterns for entity recognition"""
        # Email pattern
        email_pattern = [{"TEXT": {"REGEX": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"}}]
        self.matcher.add("EMAIL", [email_pattern])
        
        # Phone pattern
        phone_pattern = [{"TEXT": {"REGEX": r"(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"}}]
        self.matcher.add("PHONE", [phone_pattern])
        
        # Skills pattern (common technical skills)
        skills_keywords = [
            "python", "java", "javascript", "react", "angular", "vue", "node.js", "express",
            "django", "flask", "fastapi", "spring", "hibernate", "sql", "mysql", "postgresql",
            "mongodb", "redis", "docker", "kubernetes", "aws", "azure", "gcp", "git",
            "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
            "pandas", "numpy", "matplotlib", "seaborn", "jupyter", "data analysis",
            "web development", "mobile development", "ios", "android", "swift", "kotlin",
            "html", "css", "bootstrap", "tailwind", "sass", "less", "typescript",
            "rest api", "graphql", "microservices", "agile", "scrum", "devops"
        ]
        
        for skill in skills_keywords:
            skill_pattern = [{"LOWER": skill}]
            self.matcher.add(f"SKILL_{skill.upper()}", [skill_pattern])
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            import fitz
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            # Fallback to pdfplumber
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                return text
            except Exception as e2:
                logger.error(f"Error with pdfplumber fallback: {e2}")
                return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            # Try with python-docx first
            from docx import Document
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error with python-docx: {e}")
            # Fallback to docx2txt
            try:
                import docx2txt
                return docx2txt.process(file_path)
            except Exception as e2:
                logger.error(f"Error with docx2txt fallback: {e2}")
                return ""
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from resume file based on extension"""
        file_extension = file_path.lower().split('.')[-1]
        
        if file_extension == 'pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension in ['docx', 'doc']:
            return self.extract_text_from_docx(file_path)
        else:
            logger.error(f"Unsupported file format: {file_extension}")
            return ""
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        # Remove common resume headers/footers
        headers_to_remove = [
            r'page \d+ of \d+',
            r'confidential',
            r'private',
            r'resume',
            r'curriculum vitae',
            r'cv'
        ]
        
        for header in headers_to_remove:
            text = re.sub(header, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def extract_contact_info(self, text: str) -> Dict[str, str]:
        """Extract contact information from resume text"""
        contact_info = {
            "email": "",
            "phone": "",
            "name": ""
        }
        
        if not self.nlp:
            return contact_info
        
        doc = self.nlp(text)
        matches = self.matcher(doc)
        
        for match_id, start, end in matches:
            label = self.nlp.vocab.strings[match_id]
            if label == "EMAIL":
                contact_info["email"] = doc[start:end].text
            elif label == "PHONE":
                contact_info["phone"] = doc[start:end].text
        
        # Extract name (first line that looks like a name)
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 2 and len(line) < 50:
                # Simple heuristic: if line doesn't contain common resume keywords
                if not any(keyword in line.lower() for keyword in 
                          ['resume', 'cv', 'curriculum', 'vitae', 'email', 'phone', 'address']):
                    contact_info["name"] = line
                    break
        
        return contact_info
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text"""
        skills = []
        
        # Common technical skills patterns
        skill_patterns = [
            r'\b(python|java|javascript|react|angular|vue|node\.?js|express|django|flask|fastapi)\b',
            r'\b(sql|mysql|postgresql|mongodb|redis|docker|kubernetes)\b',
            r'\b(aws|azure|gcp|git|github|gitlab)\b',
            r'\b(machine learning|deep learning|tensorflow|pytorch|scikit-learn)\b',
            r'\b(pandas|numpy|matplotlib|seaborn|jupyter)\b',
            r'\b(html|css|bootstrap|tailwind|sass|less|typescript)\b',
            r'\b(rest api|graphql|microservices|agile|scrum|devops)\b'
        ]
        
        text_lower = text.lower()
        for pattern in skill_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            skills.extend(matches)
        
        # Remove duplicates and return
        return list(set(skill.lower() for skill in skills))
    
    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education information"""
        education = []
        
        # Education patterns
        education_patterns = [
            r'(bachelor|master|phd|doctorate|diploma|certificate).*?(in|of|,).*?(\d{4}|\d{4}-\d{4})',
            r'(b\.?s\.?|m\.?s\.?|ph\.?d\.?|m\.?b\.?a\.?).*?(in|of|,).*?(\d{4}|\d{4}-\d{4})',
            r'(university|college|institute).*?(\d{4}|\d{4}-\d{4})'
        ]
        
        for pattern in education_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                education.append({
                    "degree": match.group(0).strip(),
                    "institution": "",
                    "year": ""
                })
        
        return education
    
    def extract_experience(self, text: str) -> List[Dict[str, str]]:
        """Extract work experience information"""
        experience = []
        
        # Experience patterns
        exp_patterns = [
            r'(experience|work|employment|career)',
            r'(intern|internship|trainee)',
            r'(developer|engineer|analyst|manager|consultant)'
        ]
        
        # Simple extraction - look for job titles and companies
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['experience', 'work', 'employment']):
                # Look for job titles in following lines
                for j in range(i+1, min(i+10, len(lines))):
                    next_line = lines[j].strip()
                    if len(next_line) > 5 and len(next_line) < 100:
                        experience.append({
                            "title": next_line,
                            "company": "",
                            "duration": "",
                            "description": ""
                        })
                        break
        
        return experience
    
    def extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract project information"""
        projects = []
        
        # Project patterns
        project_keywords = ['project', 'portfolio', 'github', 'repository']
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in project_keywords):
                # Look for project descriptions in following lines
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j].strip()
                    if len(next_line) > 10:
                        projects.append({
                            "name": next_line,
                            "description": "",
                            "technologies": "",
                            "url": ""
                        })
                        break
        
        return projects
    
    def extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        certifications = []
        
        # Certification patterns
        cert_patterns = [
            r'\b(aws|azure|gcp|google|microsoft|oracle|cisco|comptia).*?(certified|certification|certificate)\b',
            r'\b(certified|certification|certificate).*?(aws|azure|gcp|google|microsoft|oracle|cisco|comptia)\b',
            r'\b(pmp|scrum|agile|itil|six sigma)\b'
        ]
        
        for pattern in cert_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            certifications.extend(matches)
        
        return list(set(cert.lower() for cert in certifications))
    
    def parse_resume(self, file_path: str) -> Dict[str, Any]:
        """Main method to parse resume and extract all information"""
        try:
            # Extract raw text
            raw_text = self.extract_text(file_path)
            if not raw_text:
                raise ValueError("Could not extract text from file")
            
            # Clean text
            cleaned_text = self.clean_text(raw_text)
            
            # Extract various components
            contact_info = self.extract_contact_info(cleaned_text)
            skills = self.extract_skills(cleaned_text)
            education = self.extract_education(cleaned_text)
            experience = self.extract_experience(cleaned_text)
            projects = self.extract_projects(cleaned_text)
            certifications = self.extract_certifications(cleaned_text)
            
            return {
                "raw_text": raw_text,
                "cleaned_text": cleaned_text,
                "contact_info": contact_info,
                "skills": skills,
                "education": education,
                "experience": experience,
                "projects": projects,
                "certifications": certifications,
                "filename": file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
            }
            
        except Exception as e:
            logger.error(f"Error parsing resume: {e}")
            return {
                "raw_text": "",
                "cleaned_text": "",
                "contact_info": {},
                "skills": [],
                "education": [],
                "experience": [],
                "projects": [],
                "certifications": [],
                "filename": "",
                "error": str(e)
            }

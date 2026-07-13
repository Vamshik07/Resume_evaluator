import re
import json
from typing import Dict, List, Optional, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobDescriptionParser:
    def __init__(self):
        """Initialize the job description parser (spaCy loaded lazily)"""
        self.nlp = None
    
    def _load_spacy(self):
        """Lazily load spaCy model"""
        if self.nlp is not None:
            return
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Please install with: python -m spacy download en_core_web_sm")
            self.nlp = None
        except Exception as e:
            logger.warning(f"spaCy load failed: {e}")
            self.nlp = None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize job description text"""
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        # Remove common job posting headers/footers
        headers_to_remove = [
            r'job description',
            r'job posting',
            r'career opportunity',
            r'we are hiring',
            r'join our team'
        ]
        
        for header in headers_to_remove:
            text = re.sub(header, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def extract_job_title(self, text: str) -> str:
        """Extract job title from job description"""
        # Enhanced patterns for job titles
        title_patterns = [
            r'(?:position|role|title|job|opening):\s*([^\n]+?)(?:\n|$)',
            r'(?:we are looking for|seeking|hiring|recruiting)\s+(?:a|an)?\s*([^\n]+?)(?:\s+to|$|\n)',
            r'^([A-Z][^.\n]{5,50}?)(?:\s+position|\s+role|\s+job|\n|$)',
            r'(?:software|data|web|mobile|devops|cloud|ai|ml|backend|frontend|full.?stack)\s+(?:engineer|developer|analyst|scientist|architect|consultant|specialist)',
            r'(?:senior|junior|lead|principal|staff|associate)\s+(?:software|data|web|mobile|devops|cloud|ai|ml|backend|frontend|full.?stack)\s+(?:engineer|developer|analyst|scientist|architect|consultant|specialist)',
            r'(?:data\s+)?(?:engineer|developer|analyst|scientist|architect|consultant|specialist|intern)',
            r'(?:python|java|javascript|react|angular|vue|node)\s+(?:developer|engineer)',
            r'(?:machine learning|deep learning|ai|ml)\s+(?:engineer|developer|scientist|specialist)'
        ]
        
        text_lower = text.lower()
        for pattern in title_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                title = matches[0].strip()
                # Clean up the title
                title = re.sub(r'\s+', ' ', title)  # Remove extra spaces
                if len(title) > 3 and len(title) < 100:  # Reasonable length
                    return title
        
        # Fallback: look for common job titles in the first few lines
        lines = text.split('\n')[:10]  # Check more lines
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in 
                  ['engineer', 'developer', 'analyst', 'scientist', 'architect', 'consultant', 'manager', 'intern']):
                # Clean up the line
                line = re.sub(r'\s+', ' ', line)
                if len(line) > 3 and len(line) < 100:
                    return line
        
        return "Software Engineer"  # Default fallback
    
    def extract_company_info(self, text: str) -> Dict[str, str]:
        """Extract company information"""
        company_info = {
            "name": "",
            "location": "",
            "industry": ""
        }
        
        # Better company name patterns
        company_patterns = [
            r'(?:company|organization|firm|corporation):\s*([^\n]+?)(?:\n|$)',
            r'(?:at|join|work with|we are)\s+([A-Z][a-zA-Z\s&]{2,50}?)(?:\s+is|\s+seeks|\s+hiring|\s+offers|\n)',
            r'^([A-Z][a-zA-Z\s&]{2,50}?)(?:\s+is\s+(?:looking|seeking|hiring)|$)',
            r'(?:about\s+)?([A-Z][a-zA-Z\s&]{2,50}?)(?:\s+is\s+a\s+leading)',
            r'(?:we\s+at\s+)([A-Z][a-zA-Z\s&]{2,50}?)(?:\s+are)'
        ]
        
        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                company_name = matches[0].strip()
                # Filter out common false positives
                if not any(word in company_name.lower() for word in 
                          ['data visualization', 'tools like', 'tableau', 'power bi', 'skills', 'experience', 'years']):
                    company_info["name"] = company_name
                    break
        
        # Better location patterns
        location_patterns = [
            r'(?:location|based in|office in|work from):\s*([^\n]+?)(?:\n|$)',
            r'(?:hyderabad|bangalore|pune|delhi|mumbai|chennai|kolkata|gurgaon|noida|bengaluru)(?:\s*\([^)]+\))?',
            r'(?:remote|hybrid|onsite|work from home)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\([^)]*onsite[^)]*\)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\([^)]*remote[^)]*\)'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                location = matches[0].strip()
                # Clean up location text
                location = re.sub(r'\([^)]*\)', '', location).strip()
                if location and len(location) < 50:  # Avoid very long location strings
                    company_info["location"] = location
                    break
        
        return company_info
    
    def extract_required_skills(self, text: str) -> List[str]:
        """Extract must-have/required skills"""
        required_skills = []
        
        # Look for required skills sections
        required_sections = [
            r'(?:required|must have|mandatory|essential|core)\s+(?:skills|qualifications|requirements?):?\s*([^.]*)',
            r'(?:candidate must have|candidates should have|you must have):?\s*([^.]*)',
            r'(?:minimum|basic)\s+(?:requirements?|qualifications?):?\s*([^.]*)'
        ]
        
        text_lower = text.lower()
        for pattern in required_sections:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Extract skills from the matched text
                skills = self._extract_skills_from_text(match)
                required_skills.extend(skills)
        
        # Also look for technical skills mentioned throughout the document
        all_skills = self._extract_skills_from_text(text)
        required_skills.extend(all_skills)
        
        return list(set(skill.lower() for skill in required_skills))
    
    def extract_preferred_skills(self, text: str) -> List[str]:
        """Extract good-to-have/preferred skills"""
        preferred_skills = []
        
        # Look for preferred skills sections
        preferred_sections = [
            r'(?:preferred|good to have|nice to have|bonus|plus|advantage):?\s*([^.]*)',
            r'(?:additional|extra|optional)\s+(?:skills|qualifications?):?\s*([^.]*)',
            r'(?:would be great|ideal candidate):?\s*([^.]*)'
        ]
        
        text_lower = text.lower()
        for pattern in preferred_sections:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            for match in matches:
                skills = self._extract_skills_from_text(match)
                preferred_skills.extend(skills)
        
        return list(set(skill.lower() for skill in preferred_skills))
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract technical skills from a given text"""
        skills = []
        
        # Enhanced technical skills patterns
        skill_patterns = [
            # Programming Languages
            r'\b(python|java|javascript|typescript|go|rust|c\+\+|c#|php|ruby|swift|kotlin|scala|r)\b',
            # Web Technologies
            r'\b(react|angular|vue|node\.?js|express|django|flask|fastapi|spring|laravel|rails)\b',
            # Databases
            r'\b(sql|mysql|postgresql|mongodb|redis|elasticsearch|cassandra|dynamodb|oracle)\b',
            # Cloud & DevOps
            r'\b(aws|azure|gcp|docker|kubernetes|jenkins|terraform|ansible|git|github|gitlab)\b',
            # Data Science & ML
            r'\b(machine learning|deep learning|tensorflow|pytorch|scikit-learn|pandas|numpy|matplotlib|seaborn|jupyter|spark|kafka)\b',
            # Frontend
            r'\b(html|css|bootstrap|tailwind|sass|less|webpack|babel)\b',
            # Backend & APIs
            r'\b(rest api|graphql|microservices|agile|scrum|devops|ci/cd)\b',
            # Mobile
            r'\b(ios|android|flutter|react native|xamarin)\b',
            # System & Tools
            r'\b(linux|unix|bash|shell|powershell|vim|emacs)\b',
            # Monitoring & Analytics
            r'\b(prometheus|grafana|kibana|splunk|datadog)\b',
            # Additional skills
            r'\b(tableau|power bi|excel|airflow|hadoop|hive|pig|sqoop)\b'
        ]
        
        text_lower = text.lower()
        for pattern in skill_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            skills.extend(matches)
        
        # Remove duplicates and clean up
        unique_skills = list(set(skill.lower() for skill in skills))
        
        # Filter out very short or common words
        filtered_skills = [skill for skill in unique_skills if len(skill) > 2 and skill not in ['api', 'ci', 'cd']]
        
        return filtered_skills
    
    def extract_qualifications(self, text: str) -> List[str]:
        """Extract educational qualifications"""
        qualifications = []
        
        # Education patterns
        education_patterns = [
            r'(?:bachelor|master|phd|doctorate|diploma|certificate).*?(?:in|of|,).*?(?:computer science|engineering|technology|it|software)',
            r'(?:b\.?s\.?|m\.?s\.?|ph\.?d\.?|m\.?b\.?a\.?).*?(?:in|of|,).*?(?:computer science|engineering|technology|it|software)',
            r'(?:degree|graduation).*?(?:in|of|,).*?(?:computer science|engineering|technology|it|software)',
            r'(?:years? of experience|experience level):?\s*(\d+[\+\-\s]*(?:years?|yrs?))',
            r'(?:minimum|at least)\s+(\d+)\s+(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)'
        ]
        
        text_lower = text.lower()
        for pattern in education_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            qualifications.extend(matches)
        
        return qualifications
    
    def extract_experience_requirements(self, text: str) -> Dict[str, Any]:
        """Extract experience requirements"""
        experience_req = {
            "min_years": 0,
            "max_years": None,
            "level": "",
            "description": ""
        }
        
        # Experience level patterns
        level_patterns = [
            r'(?:entry level|junior|fresher|0-2\s*years?)',
            r'(?:mid level|intermediate|2-5\s*years?)',
            r'(?:senior|lead|5-8\s*years?)',
            r'(?:principal|architect|8\+\s*years?)'
        ]
        
        text_lower = text.lower()
        for pattern in level_patterns:
            if re.search(pattern, text_lower):
                experience_req["level"] = re.search(pattern, text_lower).group(0)
                break
        
        # Years of experience patterns
        years_patterns = [
            r'(\d+)\s*[-+]\s*(\d+)\s*(?:years?|yrs?)',
            r'(?:minimum|at least)\s+(\d+)\s+(?:years?|yrs?)',
            r'(\d+)\+\s*(?:years?|yrs?)',
            r'(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)'
        ]
        
        for pattern in years_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                if isinstance(matches[0], tuple):
                    if len(matches[0]) == 2:
                        experience_req["min_years"] = int(matches[0][0])
                        experience_req["max_years"] = int(matches[0][1])
                    else:
                        experience_req["min_years"] = int(matches[0][0])
                else:
                    experience_req["min_years"] = int(matches[0])
                break
        
        return experience_req
    
    def extract_responsibilities(self, text: str) -> List[str]:
        """Extract job responsibilities"""
        responsibilities = []
        
        # Look for responsibilities sections
        resp_sections = [
            r'(?:responsibilities|duties|what you will do|key responsibilities?):?\s*([^.]*)',
            r'(?:role and responsibilities?|job responsibilities?):?\s*([^.]*)'
        ]
        
        text_lower = text.lower()
        for pattern in resp_sections:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Split by bullet points or line breaks
                points = re.split(r'[•\-\*\n]', match)
                for point in points:
                    point = point.strip()
                    if len(point) > 10:
                        responsibilities.append(point)
        
        return responsibilities
    
    def extract_benefits(self, text: str) -> List[str]:
        """Extract benefits and perks"""
        benefits = []
        
        # Benefits patterns
        benefit_patterns = [
            r'(?:benefits|perks|compensation|package):?\s*([^.]*)',
            r'(?:we offer|what we offer):?\s*([^.]*)',
            r'(?:competitive|attractive)\s+(?:salary|package|compensation)'
        ]
        
        text_lower = text.lower()
        for pattern in benefit_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Split by bullet points or line breaks
                points = re.split(r'[•\-\*\n]', match)
                for point in points:
                    point = point.strip()
                    if len(point) > 5:
                        benefits.append(point)
        
        return benefits
    
    def parse_job_description(self, text: str) -> Dict[str, Any]:
        """Main method to parse job description and extract all information"""
        try:
            # Clean text
            cleaned_text = self.clean_text(text)
            
            # Extract various components
            job_title = self.extract_job_title(cleaned_text)
            company_info = self.extract_company_info(cleaned_text)
            required_skills = self.extract_required_skills(cleaned_text)
            preferred_skills = self.extract_preferred_skills(cleaned_text)
            qualifications = self.extract_qualifications(cleaned_text)
            experience_req = self.extract_experience_requirements(cleaned_text)
            responsibilities = self.extract_responsibilities(cleaned_text)
            benefits = self.extract_benefits(cleaned_text)
            
            return {
                "raw_text": text,
                "cleaned_text": cleaned_text,
                "job_title": job_title,
                "company_info": company_info,
                "required_skills": required_skills,
                "preferred_skills": preferred_skills,
                "qualifications": qualifications,
                "experience_requirements": experience_req,
                "responsibilities": responsibilities,
                "benefits": benefits
            }
            
        except Exception as e:
            logger.error(f"Error parsing job description: {e}")
            return {
                "raw_text": text,
                "cleaned_text": "",
                "job_title": "",
                "company_info": {},
                "required_skills": [],
                "preferred_skills": [],
                "qualifications": [],
                "experience_requirements": {},
                "responsibilities": [],
                "benefits": [],
                "error": str(e)
            }

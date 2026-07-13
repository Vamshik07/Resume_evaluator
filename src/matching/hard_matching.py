import re
from typing import Dict, List, Tuple, Any
from fuzzywuzzy import fuzz, process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HardMatching:
    def __init__(self):
        """Initialize hard matching with TF-IDF vectorizer"""
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
    
    def exact_keyword_match(self, resume_skills: List[str], jd_skills: List[str]) -> Dict[str, Any]:
        """Perform exact keyword matching between resume and job description skills"""
        resume_skills_lower = [skill.lower() for skill in resume_skills]
        jd_skills_lower = [skill.lower() for skill in jd_skills]
        
        # Find exact matches
        exact_matches = []
        for jd_skill in jd_skills_lower:
            if jd_skill in resume_skills_lower:
                exact_matches.append(jd_skill)
        
        # Find missing skills
        missing_skills = [skill for skill in jd_skills_lower if skill not in resume_skills_lower]
        
        # Calculate exact match score
        exact_match_score = len(exact_matches) / len(jd_skills_lower) if jd_skills_lower else 0
        
        return {
            "exact_matches": exact_matches,
            "missing_skills": missing_skills,
            "exact_match_score": exact_match_score,
            "total_required_skills": len(jd_skills_lower),
            "matched_skills_count": len(exact_matches)
        }
    
    def fuzzy_keyword_match(self, resume_skills: List[str], jd_skills: List[str], threshold: int = 80) -> Dict[str, Any]:
        """Perform fuzzy keyword matching with similarity threshold"""
        resume_skills_lower = [skill.lower() for skill in resume_skills]
        jd_skills_lower = [skill.lower() for skill in jd_skills]
        
        fuzzy_matches = []
        partial_matches = []
        
        for jd_skill in jd_skills_lower:
            # Find best match using fuzzy matching
            best_match = process.extractOne(jd_skill, resume_skills_lower, scorer=fuzz.ratio)
            
            if best_match:
                skill = best_match[0]
                score = best_match[1]
                if score >= threshold:
                    fuzzy_matches.append({
                        "jd_skill": jd_skill,
                        "resume_skill": skill,
                        "similarity_score": score
                    })
                elif score >= 60:  # Lower threshold for partial matches
                    partial_matches.append({
                        "jd_skill": jd_skill,
                        "resume_skill": skill,
                        "similarity_score": score
                    })
        
        # Calculate fuzzy match score
        fuzzy_match_score = len(fuzzy_matches) / len(jd_skills_lower) if jd_skills_lower else 0
        
        return {
            "fuzzy_matches": fuzzy_matches,
            "partial_matches": partial_matches,
            "fuzzy_match_score": fuzzy_match_score,
            "total_required_skills": len(jd_skills_lower),
            "matched_skills_count": len(fuzzy_matches)
        }
    
    def education_match(self, resume_education: List[Dict], jd_qualifications: List[str]) -> Dict[str, Any]:
        """Match education qualifications"""
        education_score = 0
        education_matches = []
        missing_qualifications = []
        
        # Extract degree types from resume education
        resume_degrees = []
        for edu in resume_education:
            if isinstance(edu, dict) and 'degree' in edu:
                degree_text = edu['degree'].lower()
                resume_degrees.append(degree_text)
        
        # Check for degree matches
        for jd_qual in jd_qualifications:
            jd_qual_lower = jd_qual.lower()
            matched = False
            
            for resume_degree in resume_degrees:
                # Check for degree level matches
                if any(level in resume_degree for level in ['bachelor', 'master', 'phd', 'diploma']):
                    if any(level in jd_qual_lower for level in ['bachelor', 'master', 'phd', 'diploma']):
                        education_matches.append({
                            "jd_qualification": jd_qual,
                            "resume_degree": resume_degree,
                            "match_type": "degree_level"
                        })
                        education_score += 0.5
                        matched = True
                        break
                
                # Check for field matches
                if any(field in resume_degree for field in ['computer', 'engineering', 'technology', 'software', 'it']):
                    if any(field in jd_qual_lower for field in ['computer', 'engineering', 'technology', 'software', 'it']):
                        education_matches.append({
                            "jd_qualification": jd_qual,
                            "resume_degree": resume_degree,
                            "match_type": "field"
                        })
                        education_score += 0.3
                        matched = True
                        break
            
            if not matched:
                missing_qualifications.append(jd_qual)
        
        # Normalize score
        max_possible_score = len(jd_qualifications) if jd_qualifications else 1
        education_score = min(education_score / max_possible_score, 1.0)
        
        return {
            "education_score": education_score,
            "education_matches": education_matches,
            "missing_qualifications": missing_qualifications,
            "total_qualifications": len(jd_qualifications)
        }
    
    def experience_match(self, resume_experience: List[Dict], jd_experience_req: Dict[str, Any]) -> Dict[str, Any]:
        """Match work experience requirements"""
        experience_score = 0
        experience_analysis = {
            "meets_minimum": False,
            "experience_level": "",
            "years_estimated": 0
        }
        
        # Estimate years of experience from resume
        estimated_years = self._estimate_experience_years(resume_experience)
        experience_analysis["years_estimated"] = estimated_years
        
        # Check against job requirements
        if jd_experience_req:
            min_years = jd_experience_req.get("min_years", 0)
            max_years = jd_experience_req.get("max_years")
            required_level = jd_experience_req.get("level", "")
            
            # Check if meets minimum
            if estimated_years >= min_years:
                experience_analysis["meets_minimum"] = True
                experience_score = 0.8
                
                # Bonus for exceeding requirements
                if max_years and estimated_years <= max_years:
                    experience_score = 1.0
                elif estimated_years > min_years + 2:
                    experience_score = 0.9
            else:
                # Partial score based on how close they are
                experience_score = max(0, estimated_years / min_years) if min_years > 0 else 0
            
            # Determine experience level
            if estimated_years <= 2:
                experience_analysis["experience_level"] = "entry_level"
            elif estimated_years <= 5:
                experience_analysis["experience_level"] = "mid_level"
            elif estimated_years <= 8:
                experience_analysis["experience_level"] = "senior_level"
            else:
                experience_analysis["experience_level"] = "principal_level"
        
        return {
            "experience_score": experience_score,
            "experience_analysis": experience_analysis,
            "jd_requirements": jd_experience_req
        }
    
    def _estimate_experience_years(self, resume_experience: List[Dict]) -> int:
        """Estimate years of experience from resume"""
        total_years = 0
        
        for exp in resume_experience:
            if isinstance(exp, dict) and 'duration' in exp:
                duration = exp['duration'].lower()
                
                # Extract years from duration text
                year_patterns = [
                    r'(\d+)\s*(?:years?|yrs?)',
                    r'(\d+)\s*(?:months?|mos?)',
                    r'(\d+)\s*(?:days?|d)'
                ]
                
                for pattern in year_patterns:
                    matches = re.findall(pattern, duration)
                    if matches:
                        years = int(matches[0])
                        if 'month' in duration:
                            years = years / 12
                        elif 'day' in duration:
                            years = years / 365
                        total_years += years
                        break
                else:
                    # If no duration found, estimate based on title
                    title = exp.get('title', '').lower()
                    if any(keyword in title for keyword in ['senior', 'lead', 'principal']):
                        total_years += 3
                    elif any(keyword in title for keyword in ['junior', 'entry', 'fresher']):
                        total_years += 1
                    else:
                        total_years += 2  # Default assumption
        
        return int(total_years)
    
    def certification_match(self, resume_certifications: List[str], jd_skills: List[str]) -> Dict[str, Any]:
        """Match certifications and professional qualifications"""
        certification_score = 0
        certification_matches = []
        missing_certifications = []
        
        resume_certs_lower = [cert.lower() for cert in resume_certifications]
        jd_skills_lower = [skill.lower() for skill in jd_skills]
        
        # Look for certification-related skills in JD
        cert_keywords = ['certified', 'certification', 'certificate', 'aws', 'azure', 'gcp', 'pmp', 'scrum']
        jd_cert_requirements = [skill for skill in jd_skills_lower if any(keyword in skill for keyword in cert_keywords)]
        
        for jd_cert in jd_cert_requirements:
            matched = False
            for resume_cert in resume_certs_lower:
                # Check for exact or fuzzy match
                if jd_cert in resume_cert or resume_cert in jd_cert:
                    certification_matches.append({
                        "jd_certification": jd_cert,
                        "resume_certification": resume_cert,
                        "match_type": "exact"
                    })
                    certification_score += 1
                    matched = True
                    break
                elif fuzz.ratio(jd_cert, resume_cert) > 70:
                    certification_matches.append({
                        "jd_certification": jd_cert,
                        "resume_certification": resume_cert,
                        "match_type": "fuzzy"
                    })
                    certification_score += 0.7
                    matched = True
                    break
            
            if not matched:
                missing_certifications.append(jd_cert)
        
        # Normalize score
        max_possible_score = len(jd_cert_requirements) if jd_cert_requirements else 1
        certification_score = min(certification_score / max_possible_score, 1.0)
        
        return {
            "certification_score": certification_score,
            "certification_matches": certification_matches,
            "missing_certifications": missing_certifications,
            "total_cert_requirements": len(jd_cert_requirements)
        }
    
    def tfidf_similarity(self, resume_text: str, jd_text: str) -> float:
        """Calculate TF-IDF based similarity between resume and job description"""
        try:
            # Combine texts for vectorization
            texts = [resume_text, jd_text]
            
            # Fit and transform texts
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating TF-IDF similarity: {e}")
            return 0.0
    
    def calculate_hard_match_score(self, resume_data: Dict[str, Any], jd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall hard match score"""
        try:
            # Extract data
            resume_skills = resume_data.get("skills", [])
            resume_education = resume_data.get("education", [])
            resume_experience = resume_data.get("experience", [])
            resume_certifications = resume_data.get("certifications", [])
            resume_text = resume_data.get("cleaned_text", "")
            
            jd_required_skills = jd_data.get("required_skills", [])
            jd_preferred_skills = jd_data.get("preferred_skills", [])
            jd_qualifications = jd_data.get("qualifications", [])
            jd_experience_req = jd_data.get("experience_requirements", {})
            jd_text = jd_data.get("cleaned_text", "")
            
            # Perform different types of matching
            exact_skill_match = self.exact_keyword_match(resume_skills, jd_required_skills)
            fuzzy_skill_match = self.fuzzy_keyword_match(resume_skills, jd_required_skills)
            education_match = self.education_match(resume_education, jd_qualifications)
            experience_match = self.experience_match(resume_experience, jd_experience_req)
            certification_match = self.certification_match(resume_certifications, jd_required_skills)
            tfidf_similarity = self.tfidf_similarity(resume_text, jd_text)
            
            # Calculate weighted scores
            weights = {
                "exact_skills": 0.3,
                "fuzzy_skills": 0.2,
                "education": 0.15,
                "experience": 0.15,
                "certifications": 0.1,
                "tfidf": 0.1
            }
            
            hard_match_score = float(
                exact_skill_match["exact_match_score"] * weights["exact_skills"] +
                fuzzy_skill_match["fuzzy_match_score"] * weights["fuzzy_skills"] +
                education_match["education_score"] * weights["education"] +
                experience_match["experience_score"] * weights["experience"] +
                certification_match["certification_score"] * weights["certifications"] +
                tfidf_similarity * weights["tfidf"]
            )
            
            return {
                "hard_match_score": float(hard_match_score),
                "exact_skill_match": exact_skill_match,
                "fuzzy_skill_match": fuzzy_skill_match,
                "education_match": education_match,
                "experience_match": experience_match,
                "certification_match": certification_match,
                "tfidf_similarity": tfidf_similarity,
                "weights": weights
            }
            
        except Exception as e:
            logger.error(f"Error calculating hard match score: {e}")
            return {
                "hard_match_score": 0.0,
                "error": str(e)
            }

import os
import numpy as np
from typing import Dict, List, Any, Optional
from sklearn.metrics.pairwise import cosine_similarity
import google.generativeai as genai
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SemanticMatching:
    def __init__(self):
        """Initialize semantic matching with embedding model and Gemini client"""
        self.gemini_model = None
        self.gemini_enabled = False

        api_key = os.getenv("GOOGLE_API_KEY")
        enable_gemini = os.getenv("ENABLE_GEMINI", "false").lower() == "true"

        if api_key and enable_gemini:
            try:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel(os.getenv("DEFAULT_MODEL", "gemini-pro"))
                self.gemini_enabled = True
                logger.info("Gemini client enabled for semantic analysis")
            except Exception as e:
                logger.warning(f"Gemini client disabled: {e}")
                self.gemini_model = None
                self.gemini_enabled = False
        else:
            logger.info("Gemini client disabled (set ENABLE_GEMINI=true and provide GOOGLE_API_KEY to enable)")
            self.gemini_model = None
            self.gemini_enabled = False

        # Model name config
        self.model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.embedding_model = None
    
    def _load_model(self):
        """Lazily load the sentence transformer model"""
        try:
            logger.info(f"Loading embedding model lazily: {self.model_name}...")
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            self.embedding_model = None
        except BaseException as be:
            logger.error(f"Critical error/MemoryError loading embedding model: {be}")
            self.embedding_model = None
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        if not self.embedding_model:
            self._load_model()
            
        if not self.embedding_model:
            logger.error("Embedding model not available")
            return np.array([])
        
        try:
            embeddings = self.embedding_model.encode(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return np.array([])
    
    def calculate_semantic_similarity(self, resume_text: str, jd_text: str) -> float:
        """Calculate semantic similarity between resume and job description"""
        try:
            # Generate embeddings
            embeddings = self.generate_embeddings([resume_text, jd_text])
            
            if embeddings.size == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def extract_semantic_skills(self, resume_text: str, jd_skills: List[str]) -> Dict[str, Any]:
        """Extract semantically similar skills from resume"""
        try:
            # Split resume into sentences for better matching
            resume_sentences = resume_text.split('. ')
            
            # Generate embeddings for resume sentences and JD skills
            all_texts = resume_sentences + jd_skills
            embeddings = self.generate_embeddings(all_texts)
            
            if embeddings.size == 0:
                return {"semantic_matches": [], "semantic_score": 0.0}
            
            resume_embeddings = embeddings[:len(resume_sentences)]
            jd_skill_embeddings = embeddings[len(resume_sentences):]
            
            semantic_matches = []
            total_similarity = 0
            
            for i, jd_skill in enumerate(jd_skills):
                jd_embedding = jd_skill_embeddings[i].reshape(1, -1)
                
                # Find best matching resume sentence
                similarities = cosine_similarity(jd_embedding, resume_embeddings)[0]
                best_match_idx = np.argmax(similarities)
                best_similarity = similarities[best_match_idx]
                
                if best_similarity > 0.3:  # Threshold for semantic match
                    semantic_matches.append({
                        "jd_skill": jd_skill,
                        "resume_context": resume_sentences[best_match_idx],
                        "similarity_score": float(best_similarity)
                    })
                    total_similarity += float(best_similarity)
            
            semantic_score = float(total_similarity / len(jd_skills)) if jd_skills else 0.0
            
            return {
                "semantic_matches": semantic_matches,
                "semantic_score": semantic_score,
                "total_skills": len(jd_skills),
                "matched_skills": len(semantic_matches)
            }
            
        except Exception as e:
            logger.error(f"Error in semantic skill extraction: {e}")
            return {"semantic_matches": [], "semantic_score": 0.0, "error": str(e)}
    
    def llm_semantic_analysis(self, resume_text: str, jd_text: str) -> Dict[str, Any]:
        """Use LLM for advanced semantic analysis"""
        if not self.gemini_enabled or not self.gemini_model:
            return {
                "fit_score": 0,
                "strengths": [],
                "missing_skills": [],
                "experience_assessment": "LLM analysis disabled",
                "recommendations": ["Enable Gemini by setting ENABLE_GEMINI=true and providing GOOGLE_API_KEY"]
            }

        try:
            prompt = f"""
            You are an expert resume evaluator. Analyze the following resume against the job description and provide a detailed assessment.

            JOB DESCRIPTION:
            {jd_text[:2000]}

            RESUME:
            {resume_text[:2000]}

            Please provide:
            1. Overall fit score (0-100)
            2. Key strengths that match the job requirements
            3. Missing skills or qualifications
            4. Experience level assessment
            5. Specific recommendations for improvement

            Format your response as JSON with the following structure:
            {{
                "fit_score": <number>,
                "strengths": ["strength1", "strength2", ...],
                "missing_skills": ["skill1", "skill2", ...],
                "experience_assessment": "<assessment>",
                "recommendations": ["rec1", "rec2", ...]
            }}
            """
            
            response = self.gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1000,
                    temperature=0.3
                )
            )
            
            # Parse the response
            response_text = response.text
            
            # Try to extract JSON from response
            import json
            try:
                # Find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    analysis = json.loads(json_str)
                else:
                    # Fallback parsing
                    analysis = self._parse_llm_response(response_text)
            except json.JSONDecodeError:
                analysis = self._parse_llm_response(response_text)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in LLM semantic analysis: {e}")
            return {
                "fit_score": 0,
                "strengths": [],
                "missing_skills": [],
                "experience_assessment": "Unable to assess",
                "recommendations": ["Error in analysis"],
                "error": str(e)
            }
    
    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response when JSON parsing fails"""
        analysis = {
            "fit_score": 0,
            "strengths": [],
            "missing_skills": [],
            "experience_assessment": "Unable to assess",
            "recommendations": []
        }
        
        # Extract fit score
        import re
        score_match = re.search(r'(\d+)', response_text)
        if score_match:
            analysis["fit_score"] = int(score_match.group(1))
        
        # Extract strengths
        if "strengths" in response_text.lower():
            strengths_section = response_text.lower().split("strengths")[1].split("missing")[0]
            strengths = re.findall(r'[•\-\*]\s*([^\n]+)', strengths_section)
            analysis["strengths"] = [s.strip() for s in strengths]
        
        # Extract missing skills
        if "missing" in response_text.lower():
            missing_section = response_text.lower().split("missing")[1].split("experience")[0]
            missing = re.findall(r'[•\-\*]\s*([^\n]+)', missing_section)
            analysis["missing_skills"] = [s.strip() for s in missing]
        
        return analysis
    
    def generate_improvement_suggestions(self, resume_data: Dict[str, Any], jd_data: Dict[str, Any], analysis: Dict[str, Any]) -> List[str]:
        """Generate personalized improvement suggestions"""
        suggestions = []
        
        # Skills-based suggestions
        missing_skills = analysis.get("missing_skills", [])
        if missing_skills:
            suggestions.append(f"Consider learning or gaining experience with: {', '.join(missing_skills[:3])}")
        
        # Experience-based suggestions
        resume_experience = resume_data.get("experience", [])
        jd_experience_req = jd_data.get("experience_requirements", {})
        
        if jd_experience_req.get("min_years", 0) > 0:
            suggestions.append(f"Gain more experience in relevant technologies to meet the {jd_experience_req['min_years']}+ years requirement")
        
        # Project suggestions
        resume_projects = resume_data.get("projects", [])
        if len(resume_projects) < 2:
            suggestions.append("Add more relevant projects to showcase your technical skills")
        
        # Certification suggestions
        jd_skills = jd_data.get("required_skills", [])
        cert_keywords = ['aws', 'azure', 'gcp', 'certified', 'certification']
        cert_requirements = [skill for skill in jd_skills if any(keyword in skill.lower() for keyword in cert_keywords)]
        
        if cert_requirements:
            suggestions.append(f"Consider obtaining certifications in: {', '.join(cert_requirements[:2])}")
        
        # General suggestions
        suggestions.extend([
            "Tailor your resume to highlight relevant experience for this specific role",
            "Include quantifiable achievements and metrics in your experience descriptions",
            "Ensure your contact information and professional summary are up to date"
        ])
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    def calculate_semantic_match_score(self, resume_data: Dict[str, Any], jd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall semantic match score"""
        try:
            resume_text = resume_data.get("cleaned_text", "")
            jd_text = jd_data.get("cleaned_text", "")
            jd_skills = jd_data.get("required_skills", [])
            
            # Calculate different semantic metrics
            overall_similarity = self.calculate_semantic_similarity(resume_text, jd_text)
            semantic_skills = self.extract_semantic_skills(resume_text, jd_skills)
            llm_analysis = self.llm_semantic_analysis(resume_text, jd_text)

            # Generate improvement suggestions
            suggestions = self.generate_improvement_suggestions(resume_data, jd_data, llm_analysis)

            # Dynamic weights so disabling LLM does not unfairly penalize
            base_weights = {
                "overall_similarity": 0.3,
                "semantic_skills": 0.4,
                "llm_analysis": 0.3
            }

            active_weights = {
                k: v for k, v in base_weights.items() if not (k == "llm_analysis" and not self.gemini_enabled)
            }
            total_weight = sum(active_weights.values()) or 1.0
            normalized_weights = {k: v / total_weight for k, v in active_weights.items()}

            semantic_score = float(
                overall_similarity * normalized_weights.get("overall_similarity", 0.0) +
                float(semantic_skills["semantic_score"]) * normalized_weights.get("semantic_skills", 0.0) +
                (llm_analysis.get("fit_score", 0) / 100) * normalized_weights.get("llm_analysis", 0.0)
            )
            
            return {
                "semantic_score": float(semantic_score),
                "overall_similarity": float(overall_similarity),
                "semantic_skills": semantic_skills,
                "llm_analysis": llm_analysis,
                "improvement_suggestions": suggestions,
                "weights": {k: float(v) for k, v in normalized_weights.items()}
            }
            
        except Exception as e:
            logger.error(f"Error calculating semantic match score: {e}")
            return {
                "semantic_score": 0.0,
                "error": str(e)
            }

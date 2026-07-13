import os
from typing import Dict, List, Any, Tuple
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScoringEngine:
    def __init__(self):
        """Initialize the scoring engine with configurable weights"""
        # Get weights from environment or use defaults
        self.hard_match_weight = float(os.getenv("HARD_MATCH_WEIGHT", "0.4"))
        self.semantic_match_weight = float(os.getenv("SEMANTIC_MATCH_WEIGHT", "0.6"))
        
        # Ensure weights sum to 1
        total_weight = self.hard_match_weight + self.semantic_match_weight
        if total_weight != 1.0:
            self.hard_match_weight = self.hard_match_weight / total_weight
            self.semantic_match_weight = self.semantic_match_weight / total_weight
            logger.warning(f"Adjusted weights to sum to 1.0: hard={self.hard_match_weight}, semantic={self.semantic_match_weight}")
    
    def calculate_final_score(self, hard_match_results: Dict[str, Any], semantic_match_results: Dict[str, Any]) -> float:
        """Calculate the final weighted score"""
        try:
            hard_score = hard_match_results.get("hard_match_score", 0.0)
            semantic_score = semantic_match_results.get("semantic_score", 0.0)
            
            final_score = float(
                hard_score * self.hard_match_weight +
                semantic_score * self.semantic_match_weight
            )
            
            # Ensure score is between 0 and 1
            final_score = max(0.0, min(1.0, final_score))
            
            return float(final_score)
            
        except Exception as e:
            logger.error(f"Error calculating final score: {e}")
            return 0.0
    
    def determine_verdict(self, final_score: float) -> str:
        """Determine the fit verdict based on final score"""
        if final_score >= 0.8:
            return "High"
        elif final_score >= 0.6:
            return "Medium"
        else:
            return "Low"
    
    def convert_to_percentage(self, score: float) -> int:
        """Convert score to percentage (0-100)"""
        return int(score * 100)
    
    def generate_missing_elements(self, hard_match_results: Dict[str, Any], semantic_match_results: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate comprehensive list of missing elements"""
        missing_elements = {
            "skills": [],
            "certifications": [],
            "projects": [],
            "experience": []
        }
        
        try:
            # Extract missing skills from hard matching
            exact_skill_match = hard_match_results.get("exact_skill_match", {})
            missing_skills = exact_skill_match.get("missing_skills", [])
            missing_elements["skills"].extend(missing_skills)
            
            # Extract missing certifications
            certification_match = hard_match_results.get("certification_match", {})
            missing_certs = certification_match.get("missing_certifications", [])
            missing_elements["certifications"].extend(missing_certs)
            
            # Extract missing qualifications
            education_match = hard_match_results.get("education_match", {})
            missing_qualifications = education_match.get("missing_qualifications", [])
            missing_elements["skills"].extend(missing_qualifications)
            
            # Extract from LLM analysis
            llm_analysis = semantic_match_results.get("llm_analysis", {})
            llm_missing_skills = llm_analysis.get("missing_skills", [])
            missing_elements["skills"].extend(llm_missing_skills)
            
            # Remove duplicates
            for key in missing_elements:
                missing_elements[key] = list(set(missing_elements[key]))
            
            return missing_elements
            
        except Exception as e:
            logger.error(f"Error generating missing elements: {e}")
            return missing_elements
    
    def generate_detailed_analysis(self, resume_data: Dict[str, Any], jd_data: Dict[str, Any], 
                                 hard_match_results: Dict[str, Any], semantic_match_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed analysis report"""
        try:
            final_score = self.calculate_final_score(hard_match_results, semantic_match_results)
            verdict = self.determine_verdict(final_score)
            percentage_score = self.convert_to_percentage(final_score)
            missing_elements = self.generate_missing_elements(hard_match_results, semantic_match_results)
            
            # Extract improvement suggestions
            improvement_suggestions = semantic_match_results.get("improvement_suggestions", [])
            
            # Extract strengths from LLM analysis
            llm_analysis = semantic_match_results.get("llm_analysis", {})
            strengths = llm_analysis.get("strengths", [])
            
            # Extract experience assessment
            experience_assessment = llm_analysis.get("experience_assessment", "Not assessed")
            
            # Generate score breakdown
            score_breakdown = {
                "hard_match_score": float(hard_match_results.get("hard_match_score", 0.0)),
                "semantic_match_score": float(semantic_match_results.get("semantic_score", 0.0)),
                "hard_match_weight": float(self.hard_match_weight),
                "semantic_match_weight": float(self.semantic_match_weight),
                "final_score": float(final_score),
                "percentage_score": int(percentage_score)
            }
            
            # Generate detailed matching results
            matching_details = {
                "exact_skill_matches": hard_match_results.get("exact_skill_match", {}).get("exact_matches", []),
                "fuzzy_skill_matches": hard_match_results.get("fuzzy_skill_match", {}).get("fuzzy_matches", []),
                "semantic_skill_matches": semantic_match_results.get("semantic_skills", {}).get("semantic_matches", []),
                "education_matches": hard_match_results.get("education_match", {}).get("education_matches", []),
                "certification_matches": hard_match_results.get("certification_match", {}).get("certification_matches", []),
                "experience_analysis": hard_match_results.get("experience_match", {}).get("experience_analysis", {})
            }
            
            return {
                "relevance_score": percentage_score,
                "verdict": verdict,
                "final_score": final_score,
                "score_breakdown": score_breakdown,
                "missing_elements": missing_elements,
                "improvement_suggestions": improvement_suggestions,
                "strengths": strengths,
                "experience_assessment": experience_assessment,
                "matching_details": matching_details,
                "analysis_timestamp": self._get_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error generating detailed analysis: {e}")
            return {
                "relevance_score": 0,
                "verdict": "Low",
                "final_score": 0.0,
                "error": str(e)
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    def calculate_confidence_score(self, hard_match_results: Dict[str, Any], semantic_match_results: Dict[str, Any]) -> float:
        """Calculate confidence score for the evaluation"""
        try:
            # Factors that increase confidence
            confidence_factors = []
            
            # High agreement between hard and semantic matching
            hard_score = hard_match_results.get("hard_match_score", 0.0)
            semantic_score = semantic_match_results.get("semantic_score", 0.0)
            score_difference = abs(hard_score - semantic_score)
            if score_difference < 0.2:
                confidence_factors.append(0.3)
            elif score_difference < 0.4:
                confidence_factors.append(0.2)
            else:
                confidence_factors.append(0.1)
            
            # Sufficient data for analysis
            exact_matches = hard_match_results.get("exact_skill_match", {}).get("exact_matches", [])
            if len(exact_matches) > 0:
                confidence_factors.append(0.2)
            
            semantic_matches = semantic_match_results.get("semantic_skills", {}).get("semantic_matches", [])
            if len(semantic_matches) > 0:
                confidence_factors.append(0.2)
            
            # LLM analysis quality
            llm_analysis = semantic_match_results.get("llm_analysis", {})
            if llm_analysis.get("fit_score", 0) > 0:
                confidence_factors.append(0.3)
            
            confidence_score = sum(confidence_factors)
            return min(1.0, confidence_score)
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5  # Default moderate confidence
    
    def generate_evaluation_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate a human-readable evaluation summary"""
        try:
            score = analysis.get("relevance_score", 0)
            verdict = analysis.get("verdict", "Low")
            strengths = analysis.get("strengths", [])
            missing_elements = analysis.get("missing_elements", {})
            suggestions = analysis.get("improvement_suggestions", [])
            
            summary = f"""
            EVALUATION SUMMARY
            =================
            
            Relevance Score: {score}/100
            Fit Verdict: {verdict}
            
            STRENGTHS:
            {chr(10).join([f"• {strength}" for strength in strengths[:3]]) if strengths else "• No specific strengths identified"}
            
            MISSING ELEMENTS:
            • Skills: {', '.join(missing_elements.get('skills', [])[:3]) if missing_elements.get('skills') else 'None identified'}
            • Certifications: {', '.join(missing_elements.get('certifications', [])[:2]) if missing_elements.get('certifications') else 'None identified'}
            
            RECOMMENDATIONS:
            {chr(10).join([f"• {suggestion}" for suggestion in suggestions[:3]]) if suggestions else "• No specific recommendations available"}
            """
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error generating evaluation summary: {e}")
            return f"Error generating summary: {str(e)}"

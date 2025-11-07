"""
Learning Path Personalization Engine

This module handles the personalization of learning paths based on learner profiles,
preferences, and performance data. It integrates with the Bayesian Knowledge Tracing
engine to provide adaptive content recommendations.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models.learner import LearnerProfile, LearningStyle, ProgrammingExperienceLevel

logger = logging.getLogger(__name__)


class PersonalizationEngine:
    """
    Engine for personalizing learning experiences based on learner profiles
    
    This class analyzes learner profiles and generates personalized learning
    recommendations, content preferences, and adaptive parameters.
    """
    
    def __init__(self):
        self.difficulty_mappings = {
            ProgrammingExperienceLevel.NONE: 0.1,
            ProgrammingExperienceLevel.BEGINNER: 0.3,
            ProgrammingExperienceLevel.INTERMEDIATE: 0.5,
            ProgrammingExperienceLevel.ADVANCED: 0.7,
            ProgrammingExperienceLevel.EXPERT: 0.9
        }
        
        self.learning_style_preferences = {
            LearningStyle.VISUAL: {
                "content_types": ["diagrams", "flowcharts", "animations", "videos"],
                "presentation_style": "visual_heavy",
                "interaction_preference": "drag_drop"
            },
            LearningStyle.AUDITORY: {
                "content_types": ["audio_explanations", "narrated_videos", "discussions"],
                "presentation_style": "audio_enhanced",
                "interaction_preference": "voice_commands"
            },
            LearningStyle.KINESTHETIC: {
                "content_types": ["interactive_coding", "hands_on_exercises", "simulations"],
                "presentation_style": "interactive_heavy",
                "interaction_preference": "hands_on"
            },
            LearningStyle.READING_WRITING: {
                "content_types": ["text_explanations", "documentation", "written_exercises"],
                "presentation_style": "text_heavy",
                "interaction_preference": "text_input"
            },
            LearningStyle.MULTIMODAL: {
                "content_types": ["mixed_media", "varied_formats", "adaptive_content"],
                "presentation_style": "balanced",
                "interaction_preference": "varied"
            }
        }
    
    async def generate_personalization_profile(self, learner: LearnerProfile) -> Dict[str, Any]:
        """
        Generate a comprehensive personalization profile for a learner
        
        Args:
            learner: LearnerProfile object containing learner information
            
        Returns:
            Dict containing personalization parameters and recommendations
        """
        try:
            personalization_profile = {
                "learner_id": str(learner.id),
                "generated_at": datetime.utcnow(),
                "difficulty_level": self._calculate_difficulty_level(learner),
                "content_preferences": self._determine_content_preferences(learner),
                "accessibility_adaptations": self._generate_accessibility_adaptations(learner),
                "session_parameters": self._calculate_session_parameters(learner),
                "learning_path_adjustments": self._generate_learning_path_adjustments(learner),
                "assessment_preferences": self._determine_assessment_preferences(learner),
                "motivation_factors": self._identify_motivation_factors(learner)
            }
            
            logger.info(f"Generated personalization profile for learner {learner.id}")
            return personalization_profile
            
        except Exception as e:
            logger.error(f"Error generating personalization profile for learner {learner.id}: {e}")
            raise
    
    def _calculate_difficulty_level(self, learner: LearnerProfile) -> Dict[str, float]:
        """Calculate appropriate difficulty levels for different content types"""
        base_difficulty = self.difficulty_mappings.get(
            learner.programming_experience.overall_level, 
            0.3
        )
        
        # Adjust based on years of experience
        if learner.programming_experience.years_experience:
            experience_factor = min(learner.programming_experience.years_experience / 10, 0.3)
            base_difficulty += experience_factor
        
        # Adjust based on specific data structure familiarity
        ds_familiarity = learner.programming_experience.data_structures_familiarity
        if ds_familiarity:
            avg_familiarity = self._calculate_average_familiarity(ds_familiarity)
            base_difficulty = (base_difficulty + avg_familiarity) / 2
        
        # Ensure difficulty stays within bounds
        base_difficulty = max(0.1, min(0.9, base_difficulty))
        
        return {
            "overall": base_difficulty,
            "coding_challenges": base_difficulty,
            "theoretical_concepts": base_difficulty * 0.9,  # Slightly easier for theory
            "practical_exercises": base_difficulty * 1.1   # Slightly harder for practice
        }
    
    def _determine_content_preferences(self, learner: LearnerProfile) -> Dict[str, Any]:
        """Determine content type preferences based on learning style"""
        learning_style = learner.preferences.learning_style
        
        if learning_style and learning_style in self.learning_style_preferences:
            preferences = self.learning_style_preferences[learning_style].copy()
        else:
            # Default to multimodal if no preference specified
            preferences = self.learning_style_preferences[LearningStyle.MULTIMODAL].copy()
        
        # Add language preference
        preferences["language"] = learner.demographics.language or "en"
        
        return preferences
    
    def _generate_accessibility_adaptations(self, learner: LearnerProfile) -> Dict[str, Any]:
        """Generate accessibility adaptations based on learner needs"""
        adaptations = {
            "enabled": len(learner.preferences.accessibility_needs) > 0,
            "features": []
        }
        
        for need in learner.preferences.accessibility_needs:
            if need.value == "screen_reader":
                adaptations["features"].extend([
                    "alt_text_for_images",
                    "semantic_html",
                    "keyboard_navigation",
                    "aria_labels"
                ])
            elif need.value == "high_contrast":
                adaptations["features"].extend([
                    "high_contrast_theme",
                    "increased_border_width",
                    "enhanced_focus_indicators"
                ])
            elif need.value == "large_text":
                adaptations["features"].extend([
                    "scalable_fonts",
                    "increased_line_spacing",
                    "larger_ui_elements"
                ])
            elif need.value == "keyboard_navigation":
                adaptations["features"].extend([
                    "keyboard_shortcuts",
                    "tab_navigation",
                    "skip_links"
                ])
            elif need.value == "closed_captions":
                adaptations["features"].extend([
                    "video_captions",
                    "audio_transcripts"
                ])
            elif need.value == "reduced_motion":
                adaptations["features"].extend([
                    "disable_animations",
                    "static_transitions",
                    "reduced_parallax"
                ])
            elif need.value == "color_blind_support":
                adaptations["features"].extend([
                    "color_blind_palette",
                    "pattern_indicators",
                    "text_labels_for_colors"
                ])
        
        # Remove duplicates
        adaptations["features"] = list(set(adaptations["features"]))
        
        return adaptations
    
    def _calculate_session_parameters(self, learner: LearnerProfile) -> Dict[str, Any]:
        """Calculate optimal session parameters"""
        session_duration = learner.preferences.preferred_session_duration or 30
        
        # Adjust based on age (if provided)
        if learner.demographics.age:
            if learner.demographics.age < 18:
                session_duration = min(session_duration, 25)  # Shorter for younger learners
            elif learner.demographics.age > 50:
                session_duration = min(session_duration, 35)  # Moderate for older learners
        
        # Calculate break intervals
        break_interval = max(10, session_duration // 3)
        
        return {
            "optimal_duration_minutes": session_duration,
            "break_interval_minutes": break_interval,
            "max_consecutive_challenges": self._calculate_max_challenges(learner),
            "review_frequency": self._calculate_review_frequency(learner)
        }
    
    def _generate_learning_path_adjustments(self, learner: LearnerProfile) -> Dict[str, Any]:
        """Generate learning path adjustments based on experience and goals"""
        adjustments = {
            "skip_prerequisites": [],
            "emphasize_topics": [],
            "learning_sequence": "standard"
        }
        
        # Skip prerequisites based on experience
        experience_level = learner.programming_experience.overall_level
        if experience_level in [ProgrammingExperienceLevel.INTERMEDIATE, 
                               ProgrammingExperienceLevel.ADVANCED, 
                               ProgrammingExperienceLevel.EXPERT]:
            adjustments["skip_prerequisites"].extend([
                "basic_programming_concepts",
                "variable_declaration",
                "basic_loops"
            ])
        
        # Emphasize topics based on data structure familiarity
        ds_familiarity = learner.programming_experience.data_structures_familiarity
        if ds_familiarity:
            for ds, level in ds_familiarity.items():
                if level in ["none", "beginner"]:
                    adjustments["emphasize_topics"].append(ds)
        
        # Adjust learning sequence based on goals
        if learner.self_reported_data:
            latest_goals = learner.self_reported_data[-1].learning_goals
            if "algorithms" in str(latest_goals).lower():
                adjustments["learning_sequence"] = "algorithm_focused"
            elif "data structures" in str(latest_goals).lower():
                adjustments["learning_sequence"] = "data_structure_focused"
        
        return adjustments
    
    def _determine_assessment_preferences(self, learner: LearnerProfile) -> Dict[str, Any]:
        """Determine assessment preferences based on learning style and experience"""
        learning_style = learner.preferences.learning_style
        
        assessment_prefs = {
            "question_types": ["multiple_choice", "coding_challenges"],
            "feedback_style": "immediate",
            "hint_availability": True
        }
        
        if learning_style == LearningStyle.KINESTHETIC:
            assessment_prefs["question_types"] = ["coding_challenges", "interactive_exercises"]
        elif learning_style == LearningStyle.VISUAL:
            assessment_prefs["question_types"] = ["diagram_based", "visual_coding", "multiple_choice"]
        elif learning_style == LearningStyle.READING_WRITING:
            assessment_prefs["question_types"] = ["written_explanations", "code_analysis", "multiple_choice"]
        
        # Adjust hint availability based on experience
        experience_level = learner.programming_experience.overall_level
        if experience_level in [ProgrammingExperienceLevel.ADVANCED, ProgrammingExperienceLevel.EXPERT]:
            assessment_prefs["hint_availability"] = False
        
        return assessment_prefs
    
    def _identify_motivation_factors(self, learner: LearnerProfile) -> Dict[str, Any]:
        """Identify motivation factors based on profile and self-reported data"""
        motivation_factors = {
            "gamification_elements": [],
            "progress_visualization": "standard",
            "social_features": False
        }
        
        # Add gamification based on age and preferences
        if learner.demographics.age and learner.demographics.age < 30:
            motivation_factors["gamification_elements"].extend([
                "badges", "points", "leaderboards", "achievements"
            ])
        else:
            motivation_factors["gamification_elements"].extend([
                "progress_tracking", "skill_mastery", "certificates"
            ])
        
        # Adjust progress visualization based on learning style
        if learner.preferences.learning_style == LearningStyle.VISUAL:
            motivation_factors["progress_visualization"] = "enhanced_visual"
        
        return motivation_factors
    
    def _calculate_average_familiarity(self, familiarity_dict: Dict[str, str]) -> float:
        """Calculate average familiarity score from familiarity dictionary"""
        familiarity_scores = {
            "none": 0.1,
            "beginner": 0.3,
            "intermediate": 0.5,
            "advanced": 0.7,
            "expert": 0.9
        }
        
        if not familiarity_dict:
            return 0.3
        
        total_score = 0
        count = 0
        
        for topic, level in familiarity_dict.items():
            if level.lower() in familiarity_scores:
                total_score += familiarity_scores[level.lower()]
                count += 1
        
        return total_score / count if count > 0 else 0.3
    
    def _calculate_max_challenges(self, learner: LearnerProfile) -> int:
        """Calculate maximum consecutive challenges based on learner profile"""
        base_max = 5
        
        # Adjust based on experience
        experience_level = learner.programming_experience.overall_level
        if experience_level == ProgrammingExperienceLevel.EXPERT:
            base_max = 8
        elif experience_level == ProgrammingExperienceLevel.ADVANCED:
            base_max = 7
        elif experience_level == ProgrammingExperienceLevel.INTERMEDIATE:
            base_max = 6
        elif experience_level == ProgrammingExperienceLevel.BEGINNER:
            base_max = 4
        else:  # NONE
            base_max = 3
        
        # Adjust based on session duration preference
        if learner.preferences.preferred_session_duration:
            if learner.preferences.preferred_session_duration > 60:
                base_max += 2
            elif learner.preferences.preferred_session_duration < 20:
                base_max -= 1
        
        return max(2, base_max)
    
    def _calculate_review_frequency(self, learner: LearnerProfile) -> str:
        """Calculate optimal review frequency"""
        # Default to moderate review frequency
        if learner.self_reported_data:
            latest_data = learner.self_reported_data[-1]
            if latest_data.confidence_level and latest_data.confidence_level < 5:
                return "high"  # More frequent reviews for low confidence
            elif latest_data.confidence_level and latest_data.confidence_level > 7:
                return "low"   # Less frequent reviews for high confidence
        
        return "moderate"


# Global personalization engine instance
personalization_engine = PersonalizationEngine()


async def update_learner_personalization(learner_id: str, learner_profile: LearnerProfile) -> Dict[str, Any]:
    """
    Update personalization settings for a learner
    
    This function is called whenever a learner profile is updated to ensure
    that the learning experience is immediately personalized based on the
    new profile information.
    
    Args:
        learner_id: The learner's unique identifier
        learner_profile: Updated learner profile
        
    Returns:
        Dict containing the updated personalization profile
    """
    try:
        personalization_profile = await personalization_engine.generate_personalization_profile(learner_profile)
        
        # TODO: Store personalization profile in database
        # TODO: Trigger learning path recalculation
        # TODO: Update content recommendations
        # TODO: Notify adaptive engine of changes
        
        logger.info(f"Updated personalization for learner {learner_id}")
        return personalization_profile
        
    except Exception as e:
        logger.error(f"Error updating personalization for learner {learner_id}: {e}")
        raise
#!/usr/bin/env python3
"""
Demonstration of the Adaptive Challenge Selection feature.

This script shows how the adaptive learning system works:
1. Initialize learner competencies
2. Get personalized recommendations
3. Simulate activity completion
4. Update competencies and get new recommendations
"""

import sys
import os
from datetime import datetime
from typing import List

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.adaptive_models import (
    CompetencyLevel, ChallengeMetadata, AdaptationRequest,
    ActivityResult, DifficultyFeedback, BKTParameters
)
from src.algorithms.bkt_engine import BKTEngine
from src.algorithms.adaptive_engine import AdaptiveEngine


def create_sample_competencies() -> List[CompetencyLevel]:
    """Create sample learner competencies."""
    competencies = [
        CompetencyLevel(
            _id="arrays",
            competency_name="Arrays and Lists",
            mastery_probability=0.7,
            confidence_level=0.8,
            last_updated=datetime.utcnow(),
            bkt_parameters=BKTParameters()
        ),
        CompetencyLevel(
            _id="recursion",
            competency_name="Recursion",
            mastery_probability=0.4,
            confidence_level=0.6,
            last_updated=datetime.utcnow(),
            bkt_parameters=BKTParameters()
        ),
        CompetencyLevel(
            _id="trees",
            competency_name="Binary Trees",
            mastery_probability=0.2,
            confidence_level=0.3,
            last_updated=datetime.utcnow(),
            bkt_parameters=BKTParameters()
        ),
        CompetencyLevel(
            _id="sorting",
            competency_name="Sorting Algorithms",
            mastery_probability=0.8,
            confidence_level=0.9,
            last_updated=datetime.utcnow(),
            bkt_parameters=BKTParameters()
        )
    ]
    return competencies


def create_sample_challenges() -> List[ChallengeMetadata]:
    """Create sample challenges."""
    challenges = [
        ChallengeMetadata(
            _id="challenge_1",
            title="Array Rotation",
            description="Implement array rotation algorithms",
            competencies=["arrays"],
            difficulty_level=0.6,
            estimated_duration=30,
            challenge_type="coding",
            prerequisites=[]
        ),
        ChallengeMetadata(
            _id="challenge_2",
            title="Recursive Fibonacci",
            description="Implement Fibonacci using recursion",
            competencies=["recursion"],
            difficulty_level=0.4,
            estimated_duration=25,
            challenge_type="coding",
            prerequisites=[]
        ),
        ChallengeMetadata(
            _id="challenge_3",
            title="Tree Traversal",
            description="Implement tree traversal algorithms",
            competencies=["trees", "recursion"],
            difficulty_level=0.7,
            estimated_duration=45,
            challenge_type="coding",
            prerequisites=["recursion"]
        ),
        ChallengeMetadata(
            _id="challenge_4",
            title="Merge Sort Implementation",
            description="Implement merge sort algorithm",
            competencies=["sorting", "recursion"],
            difficulty_level=0.8,
            estimated_duration=60,
            challenge_type="coding",
            prerequisites=["arrays"]
        ),
        ChallengeMetadata(
            _id="challenge_5",
            title="Binary Search Tree",
            description="Implement a binary search tree",
            competencies=["trees"],
            difficulty_level=0.5,
            estimated_duration=40,
            challenge_type="coding",
            prerequisites=["arrays"]
        )
    ]
    return challenges


def print_competency_summary(competencies: List[CompetencyLevel]):
    """Print a summary of learner competencies."""
    print("\n📊 Current Competency Levels:")
    print("-" * 50)
    for comp in competencies:
        mastery_bar = "█" * int(comp.mastery_probability * 10) + "░" * (10 - int(comp.mastery_probability * 10))
        confidence_bar = "█" * int(comp.confidence_level * 10) + "░" * (10 - int(comp.confidence_level * 10))
        
        print(f"{comp.competency_name:20} | Mastery: {mastery_bar} {comp.mastery_probability:.2f}")
        print(f"{' ' * 20} | Confidence: {confidence_bar} {comp.confidence_level:.2f}")
        print()


def print_recommendation(recommendation, index=0):
    """Print a challenge recommendation."""
    challenge = recommendation.challenge
    prefix = "🎯 RECOMMENDED" if index == 0 else f"🔄 ALTERNATIVE {index}"
    
    print(f"\n{prefix}: {challenge.title}")
    print(f"   📝 Description: {challenge.description}")
    print(f"   ⚡ Difficulty: {challenge.difficulty_level:.2f} (Optimal: {recommendation.optimal_difficulty:.2f})")
    print(f"   ⏱️  Duration: {challenge.estimated_duration} minutes")
    print(f"   🎯 Score: {recommendation.recommendation_score:.2f}")
    print(f"   💡 Reasoning: {recommendation.reasoning}")
    
    target_comps = [comp.competency_name for comp in recommendation.target_competencies]
    print(f"   🎓 Target Skills: {', '.join(target_comps)}")


def main():
    """Main demonstration function."""
    print("🚀 Adaptive Challenge Selection Demo")
    print("=" * 50)
    
    # Initialize engines
    bkt_engine = BKTEngine()
    adaptive_engine = AdaptiveEngine()
    
    # Create sample data
    competencies = create_sample_competencies()
    challenges = create_sample_challenges()
    
    # Show initial competency state
    print_competency_summary(competencies)
    
    # Generate insights
    insights = bkt_engine.get_competency_insights(competencies)
    print(f"\n🧠 Learning Insights:")
    print(f"   Overall Mastery: {insights['overall_mastery']:.2f}")
    print(f"   Strong Skills: {', '.join(insights['strong_competencies'])}")
    print(f"   Developing Skills: {', '.join(insights['developing_competencies'])}")
    print(f"   Areas for Growth: {', '.join(insights['weak_competencies'])}")
    
    # Create adaptation request
    request = AdaptationRequest(
        learner_id="demo_learner",
        current_competencies=competencies,
        learning_goals=["recursion", "trees"],  # Focus on these skills
        time_available=45,
        preferred_difficulty=0.5
    )
    
    # Get recommendations
    print(f"\n🎯 Getting Personalized Recommendations...")
    print(f"   Learning Goals: Recursion, Binary Trees")
    print(f"   Available Time: 45 minutes")
    print(f"   Preferred Difficulty: 0.5")
    
    response = adaptive_engine.generate_recommendations(request, challenges)
    
    # Show recommendations
    print_recommendation(response.next_challenge, 0)
    
    for i, alt in enumerate(response.alternative_challenges[:2], 1):
        print_recommendation(alt, i)
    
    # Simulate activity completion
    print(f"\n🎮 Simulating Activity Completion...")
    selected_challenge = response.next_challenge.challenge
    
    # Simulate learner completing the challenge
    activity_result = ActivityResult(
        learner_id="demo_learner",
        challenge_id=selected_challenge.challenge_id,
        competencies_addressed=selected_challenge.competencies,
        success=True,
        score=0.75,
        attempts=2,
        time_spent=35,
        difficulty_feedback=DifficultyFeedback(
            challenge_id=selected_challenge.challenge_id,
            learner_id="demo_learner",
            perceived_difficulty=0.6,
            actual_difficulty=selected_challenge.difficulty_level,
            completion_time=35,
            success_rate=0.75,
            feedback_text="Good challenge, felt appropriately difficult"
        )
    )
    
    print(f"   ✅ Completed: {selected_challenge.title}")
    print(f"   📊 Score: {activity_result.score:.2f}")
    print(f"   🔄 Attempts: {activity_result.attempts}")
    print(f"   ⏱️  Time: {activity_result.time_spent} minutes")
    print(f"   💬 Feedback: {activity_result.difficulty_feedback.feedback_text}")
    
    # Update competencies
    print(f"\n🔄 Updating Competencies with BKT...")
    updated_competencies = adaptive_engine.adapt_after_activity(
        "demo_learner",
        activity_result,
        competencies,
        activity_result.difficulty_feedback
    )
    
    # Show updated competencies
    print_competency_summary(updated_competencies)
    
    # Show competency changes
    print("\n📈 Competency Changes:")
    print("-" * 30)
    for old_comp, new_comp in zip(competencies, updated_competencies):
        if old_comp.competency_id == new_comp.competency_id:
            mastery_change = new_comp.mastery_probability - old_comp.mastery_probability
            confidence_change = new_comp.confidence_level - old_comp.confidence_level
            
            if abs(mastery_change) > 0.01 or abs(confidence_change) > 0.01:
                print(f"{new_comp.competency_name}:")
                print(f"  Mastery: {old_comp.mastery_probability:.3f} → {new_comp.mastery_probability:.3f} ({mastery_change:+.3f})")
                print(f"  Confidence: {old_comp.confidence_level:.3f} → {new_comp.confidence_level:.3f} ({confidence_change:+.3f})")
    
    # Get new recommendations
    print(f"\n🎯 Getting Updated Recommendations...")
    new_request = AdaptationRequest(
        learner_id="demo_learner",
        current_competencies=updated_competencies,
        learning_goals=["recursion", "trees"],
        time_available=45,
        preferred_difficulty=0.5
    )
    
    new_response = adaptive_engine.generate_recommendations(new_request, challenges)
    
    print(f"\n🆕 New Recommendation After Learning:")
    print_recommendation(new_response.next_challenge, 0)
    
    # Show adaptation metadata
    metadata = new_response.adaptation_metadata
    print(f"\n📊 Adaptation Metadata:")
    print(f"   Challenges Considered: {metadata['total_challenges_considered']}")
    print(f"   Average Score: {metadata['average_score']:.3f}")
    print(f"   Refresh In: {new_response.refresh_in_minutes} minutes")
    
    profile_summary = metadata['learner_profile_summary']
    print(f"   Profile Summary:")
    print(f"     Competencies: {profile_summary['num_competencies']}")
    print(f"     Avg Mastery: {profile_summary['avg_mastery']:.3f}")
    print(f"     Avg Confidence: {profile_summary['avg_confidence']:.3f}")
    
    print(f"\n✅ Demo Complete! The system successfully:")
    print(f"   • Evaluated competencies using BKT")
    print(f"   • Provided personalized recommendations")
    print(f"   • Adapted after activity completion")
    print(f"   • Integrated difficulty feedback")
    print(f"   • Updated recommendations based on learning")


if __name__ == "__main__":
    main()
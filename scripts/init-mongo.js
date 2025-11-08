// MongoDB initialization script
// This script creates the initial database and collections

// Switch to the adaptive learning database
db = db.getSiblingDB('adaptive_learning_system');

// Create collections
db.createCollection('learner_profiles');
db.createCollection('learning_activities');
db.createCollection('performance_data');
db.createCollection('competency_assessments');

// Create indexes for learner_profiles collection
db.learner_profiles.createIndex({ "email": 1 }, { unique: true });
db.learner_profiles.createIndex({ "username": 1 }, { unique: true, sparse: true });
db.learner_profiles.createIndex({ "created_at": 1 });
db.learner_profiles.createIndex({ "is_active": 1 });
db.learner_profiles.createIndex({ 
    "demographics.country": 1, 
    "programming_experience.overall_experience": 1 
});

// Create sample data (optional - remove in production)
if (db.learner_profiles.countDocuments() === 0) {
    print("Creating sample learner profile...");
    
    db.learner_profiles.insertOne({
        email: "demo@example.com",
        first_name: "Demo",
        last_name: "User",
        username: "demouser",
        hashed_password: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3QJgusgqHu",
        demographics: {
            age: 25,
            education_level: "bachelor",
            country: "United States",
            timezone: "America/New_York",
            preferred_language: "en"
        },
        learning_preferences: {
            learning_styles: ["visual", "kinesthetic"],
            session_duration_preference: 30,
            difficulty_preference: "adaptive",
            notification_preferences: {},
            study_time_preferences: []
        },
        programming_experience: {
            overall_experience: "beginner",
            languages_known: ["python", "javascript"],
            data_structures_familiarity: {},
            algorithms_familiarity: {},
            years_of_experience: 1,
            professional_experience: false
        },
        accessibility_settings: {
            enabled_features: [],
            screen_reader_type: null,
            font_size_multiplier: 1.0,
            contrast_preference: "normal",
            motion_sensitivity: false,
            audio_enabled: true
        },
        goals: ["Learn data structures", "Prepare for interviews"],
        interests: ["algorithms", "web development"],
        is_active: true,
        created_at: new Date(),
        updated_at: new Date(),
        last_login: null,
        profile_completion_percentage: 85.0
    });
    
    print("Sample learner profile created successfully!");
}

print("MongoDB initialization completed!");

// MongoDB Initialization Script
// This script sets up the initial database structure and indexes for the BKT system

// Switch to the adaptive_learning database
db = db.getSiblingDB('adaptive_learning');

// Create collections with validation schemas
db.createCollection('competencies', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['learner_id', 'skill_id', 'p_known', 'mastery_threshold', 'total_attempts', 'correct_attempts'],
      properties: {
        learner_id: {
          bsonType: 'string',
          description: 'Unique identifier for the learner'
        },
        skill_id: {
          bsonType: 'string',
          description: 'Unique identifier for the skill'
        },
        p_known: {
          bsonType: 'double',
          minimum: 0.0,
          maximum: 1.0,
          description: 'Probability of knowing the skill'
        },
        mastery_threshold: {
          bsonType: 'double',
          minimum: 0.0,
          maximum: 1.0,
          description: 'Threshold for mastery'
        },
        is_mastered: {
          bsonType: 'bool',
          description: 'Whether the skill is mastered'
        },
        total_attempts: {
          bsonType: 'int',
          minimum: 0,
          description: 'Total number of attempts'
        },
        correct_attempts: {
          bsonType: 'int',
          minimum: 0,
          description: 'Number of correct attempts'
        },
        last_updated: {
          bsonType: 'date',
          description: 'Last update timestamp'
        }
      }
    }
  }
});

db.createCollection('performance_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['learner_id', 'skill_id', 'activity_id', 'is_correct', 'timestamp'],
      properties: {
        learner_id: {
          bsonType: 'string',
          description: 'Unique identifier for the learner'
        },
        skill_id: {
          bsonType: 'string',
          description: 'Unique identifier for the skill'
        },
        activity_id: {
          bsonType: 'string',
          description: 'Unique identifier for the activity'
        },
        is_correct: {
          bsonType: 'bool',
          description: 'Whether the response was correct'
        },
        response_time: {
          bsonType: 'double',
          minimum: 0.0,
          description: 'Response time in seconds'
        },
        confidence_level: {
          bsonType: 'double',
          minimum: 0.0,
          maximum: 1.0,
          description: 'Self-reported confidence level'
        },
        timestamp: {
          bsonType: 'date',
          description: 'Event timestamp'
        },
        metadata: {
          bsonType: 'object',
          description: 'Additional event metadata'
        }
      }
    }
  }
});

db.createCollection('skill_parameters', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['skill_id', 'p_l0', 'p_t', 'p_g', 'p_s'],
      properties: {
        skill_id: {
          bsonType: 'string',
          description: 'Unique identifier for the skill'
        },
        p_l0: {
          bsonType: 'double',
          minimum: 0.0,
          maximum: 1.0,
          description: 'Initial probability of knowing'
        },
        p_t: {
          bsonType: 'double',
          minimum: 0.0,
          maximum: 1.0,
          description: 'Probability of learning transition'
        },
        p_g: {
          bsonType: 'double',
          minimum: 0.0,
          maximum: 1.0,
          description: 'Probability of guessing correctly'
        },
        p_s: {
          bsonType: 'double',
          minimum: 0.0,
          maximum: 1.0,
          description: 'Probability of slipping'
        }
      }
    }
  }
});

db.createCollection('skill_hierarchies');
db.createCollection('learner_profiles');

// Create indexes for optimal performance
print('Creating indexes...');

// Competencies indexes
db.competencies.createIndex({ 'learner_id': 1, 'skill_id': 1 }, { unique: true });
db.competencies.createIndex({ 'learner_id': 1 });
db.competencies.createIndex({ 'skill_id': 1 });
db.competencies.createIndex({ 'is_mastered': 1 });
db.competencies.createIndex({ 'last_updated': -1 });
db.competencies.createIndex({ 'p_known': -1 });

// Performance events indexes
db.performance_events.createIndex({ 'learner_id': 1, 'skill_id': 1 });
db.performance_events.createIndex({ 'learner_id': 1, 'timestamp': -1 });
db.performance_events.createIndex({ 'skill_id': 1, 'timestamp': -1 });
db.performance_events.createIndex({ 'activity_id': 1 });
db.performance_events.createIndex({ 'timestamp': -1 });

// Skill parameters indexes
db.skill_parameters.createIndex({ 'skill_id': 1 }, { unique: true });

// Skill hierarchies indexes
db.skill_hierarchies.createIndex({ 'skill_id': 1 }, { unique: true });
db.skill_hierarchies.createIndex({ 'domain': 1 });
db.skill_hierarchies.createIndex({ 'difficulty_level': 1 });

// Learner profiles indexes
db.learner_profiles.createIndex({ 'learner_id': 1 }, { unique: true });
db.learner_profiles.createIndex({ 'updated_at': -1 });

// Insert sample data for testing
print('Inserting sample data...');

// Sample skill parameters
db.skill_parameters.insertMany([
  {
    skill_id: 'python_variables',
    p_l0: 0.1,
    p_t: 0.15,
    p_g: 0.25,
    p_s: 0.1
  },
  {
    skill_id: 'python_loops',
    p_l0: 0.05,
    p_t: 0.12,
    p_g: 0.2,
    p_s: 0.08
  },
  {
    skill_id: 'python_functions',
    p_l0: 0.08,
    p_t: 0.1,
    p_g: 0.18,
    p_s: 0.12
  }
]);

// Sample skill hierarchies
db.skill_hierarchies.insertMany([
  {
    skill_id: 'python_variables',
    parent_skills: [],
    child_skills: ['python_loops', 'python_functions'],
    difficulty_level: 1,
    domain: 'programming'
  },
  {
    skill_id: 'python_loops',
    parent_skills: ['python_variables'],
    child_skills: ['python_functions'],
    difficulty_level: 3,
    domain: 'programming'
  },
  {
    skill_id: 'python_functions',
    parent_skills: ['python_variables', 'python_loops'],
    child_skills: [],
    difficulty_level: 5,
    domain: 'programming'
  }
]);

// Sample learner profiles
db.learner_profiles.insertMany([
  {
    learner_id: 'demo_learner_1',
    competencies: {},
    learning_preferences: {
      preferred_difficulty: 'medium',
      learning_style: 'visual'
    },
    performance_history: [],
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    learner_id: 'demo_learner_2',
    competencies: {},
    learning_preferences: {
      preferred_difficulty: 'challenging',
      learning_style: 'hands-on'
    },
    performance_history: [],
    created_at: new Date(),
    updated_at: new Date()
  }
]);

print('Database initialization completed successfully!');
print('Collections created: competencies, performance_events, skill_parameters, skill_hierarchies, learner_profiles');
print('Indexes created for optimal query performance');
print('Sample data inserted for testing');
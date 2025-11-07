// MongoDB initialization script for Adaptive Learning System

// Switch to the adaptive_learning database
db = db.getSiblingDB('adaptive_learning');

// Create collections with validation schemas
db.createCollection('learner_interactions', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['learner_id', 'activity_id', 'activity_type', 'interaction_type', 'competency_ids', 'completed_at'],
            properties: {
                learner_id: { bsonType: 'string' },
                activity_id: { bsonType: 'string' },
                activity_type: { enum: ['quiz', 'coding_challenge', 'interactive_exercise', 'assessment'] },
                interaction_type: { enum: ['attempt', 'completion', 'hint_request', 'submission', 'review'] },
                competency_ids: { bsonType: 'array', items: { bsonType: 'string' } },
                score: { bsonType: 'double', minimum: 0.0, maximum: 1.0 },
                is_correct: { bsonType: 'bool' },
                attempts: { bsonType: 'int', minimum: 1 },
                time_spent: { bsonType: 'double', minimum: 0.0 },
                hints_used: { bsonType: 'int', minimum: 0 },
                completed_at: { bsonType: 'date' },
                created_at: { bsonType: 'date' }
            }
        }
    }
});

db.createCollection('mastery_levels', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['learner_id', 'competency_id', 'current_mastery', 'created_at'],
            properties: {
                learner_id: { bsonType: 'string' },
                competency_id: { bsonType: 'string' },
                current_mastery: { bsonType: 'double', minimum: 0.0, maximum: 1.0 },
                total_interactions: { bsonType: 'int', minimum: 0 },
                correct_interactions: { bsonType: 'int', minimum: 0 },
                is_mastered: { bsonType: 'bool' },
                created_at: { bsonType: 'date' },
                updated_at: { bsonType: 'date' }
            }
        }
    }
});

db.createCollection('micro_competencies', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['competency_id', 'name', 'category', 'difficulty_level'],
            properties: {
                competency_id: { bsonType: 'string' },
                name: { bsonType: 'string' },
                description: { bsonType: 'string' },
                category: { bsonType: 'string' },
                subcategory: { bsonType: 'string' },
                difficulty_level: { enum: ['beginner', 'intermediate', 'advanced', 'expert'] },
                prerequisites: { bsonType: 'array', items: { bsonType: 'string' } }
            }
        }
    }
});

// Create indexes for optimal performance
db.learner_interactions.createIndex({ 'learner_id': 1, 'completed_at': -1 });
db.learner_interactions.createIndex({ 'competency_ids': 1, 'completed_at': -1 });
db.learner_interactions.createIndex({ 'activity_id': 1 });
db.learner_interactions.createIndex({ 'session_id': 1 });

db.mastery_levels.createIndex({ 'learner_id': 1, 'competency_id': 1 }, { unique: true });
db.mastery_levels.createIndex({ 'learner_id': 1, 'current_mastery': -1 });
db.mastery_levels.createIndex({ 'competency_id': 1, 'current_mastery': -1 });

db.micro_competencies.createIndex({ 'competency_id': 1 }, { unique: true });
db.micro_competencies.createIndex({ 'category': 1, 'subcategory': 1 });

// Insert sample competencies for testing
db.micro_competencies.insertMany([
    {
        competency_id: 'arrays_basic',
        name: 'Basic Array Operations',
        description: 'Understanding array creation, indexing, and basic operations',
        category: 'data_structures',
        subcategory: 'arrays',
        difficulty_level: 'beginner',
        prerequisites: [],
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        competency_id: 'arrays_traversal',
        name: 'Array Traversal',
        description: 'Iterating through arrays using loops and iterators',
        category: 'data_structures',
        subcategory: 'arrays',
        difficulty_level: 'beginner',
        prerequisites: ['arrays_basic'],
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        competency_id: 'sorting_bubble',
        name: 'Bubble Sort Algorithm',
        description: 'Understanding and implementing bubble sort',
        category: 'algorithms',
        subcategory: 'sorting',
        difficulty_level: 'intermediate',
        prerequisites: ['arrays_basic', 'arrays_traversal'],
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        competency_id: 'binary_search',
        name: 'Binary Search Algorithm',
        description: 'Understanding and implementing binary search on sorted arrays',
        category: 'algorithms',
        subcategory: 'searching',
        difficulty_level: 'intermediate',
        prerequisites: ['arrays_basic', 'arrays_traversal'],
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        competency_id: 'linked_lists_basic',
        name: 'Basic Linked List Operations',
        description: 'Understanding linked list structure and basic operations',
        category: 'data_structures',
        subcategory: 'linked_lists',
        difficulty_level: 'intermediate',
        prerequisites: ['arrays_basic'],
        created_at: new Date(),
        updated_at: new Date()
    }
]);

print('Adaptive Learning System database initialized successfully!');
print('Collections created: learner_interactions, mastery_levels, micro_competencies');
print('Sample competencies inserted for testing');
print('Indexes created for optimal performance');
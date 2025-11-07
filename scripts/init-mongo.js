// MongoDB initialization script for Adaptive Learning System

// Switch to the adaptive learning database
db = db.getSiblingDB('adaptive_learning');

// Create collections with validation
db.createCollection('learners', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["username", "email", "created_at"],
            properties: {
                username: { bsonType: "string" },
                email: { bsonType: "string" },
                demographics: { bsonType: "object" },
                preferences: { bsonType: "object" },
                created_at: { bsonType: "date" }
            }
        }
    }
});

db.createCollection('competencies', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["name", "description"],
            properties: {
                name: { bsonType: "string" },
                description: { bsonType: "string" },
                related_concepts: { bsonType: "array" }
            }
        }
    }
});

db.createCollection('challenges', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["title", "description", "competencies", "difficulty_level", "challenge_type"],
            properties: {
                title: { bsonType: "string" },
                description: { bsonType: "string" },
                competencies: { bsonType: "array" },
                difficulty_level: { bsonType: "number", minimum: 0, maximum: 1 },
                challenge_type: { bsonType: "string" },
                estimated_duration: { bsonType: "number" },
                prerequisites: { bsonType: "array" }
            }
        }
    }
});

// Insert sample competencies
db.competencies.insertMany([
    {
        name: "Arrays and Lists",
        description: "Understanding and manipulating arrays and list data structures",
        related_concepts: []
    },
    {
        name: "Recursion",
        description: "Recursive problem solving and algorithm design",
        related_concepts: []
    },
    {
        name: "Binary Trees",
        description: "Tree data structures and traversal algorithms",
        related_concepts: []
    },
    {
        name: "Sorting Algorithms",
        description: "Various sorting algorithms and their complexities",
        related_concepts: []
    },
    {
        name: "Graph Algorithms",
        description: "Graph traversal and shortest path algorithms",
        related_concepts: []
    }
]);

// Get competency IDs for challenges
const arrayCompId = db.competencies.findOne({name: "Arrays and Lists"})._id;
const recursionCompId = db.competencies.findOne({name: "Recursion"})._id;
const treeCompId = db.competencies.findOne({name: "Binary Trees"})._id;
const sortingCompId = db.competencies.findOne({name: "Sorting Algorithms"})._id;
const graphCompId = db.competencies.findOne({name: "Graph Algorithms"})._id;

// Insert sample challenges
db.challenges.insertMany([
    {
        title: "Array Rotation",
        description: "Implement various array rotation algorithms",
        competencies: [arrayCompId],
        difficulty_level: 0.4,
        estimated_duration: 30,
        challenge_type: "coding",
        prerequisites: []
    },
    {
        title: "Recursive Fibonacci",
        description: "Implement Fibonacci sequence using recursion",
        competencies: [recursionCompId],
        difficulty_level: 0.3,
        estimated_duration: 25,
        challenge_type: "coding",
        prerequisites: []
    },
    {
        title: "Binary Tree Traversal",
        description: "Implement in-order, pre-order, and post-order traversals",
        competencies: [treeCompId, recursionCompId],
        difficulty_level: 0.6,
        estimated_duration: 45,
        challenge_type: "coding",
        prerequisites: [recursionCompId]
    },
    {
        title: "Merge Sort Implementation",
        description: "Implement the merge sort algorithm",
        competencies: [sortingCompId, recursionCompId],
        difficulty_level: 0.7,
        estimated_duration: 50,
        challenge_type: "coding",
        prerequisites: [arrayCompId, recursionCompId]
    },
    {
        title: "Breadth-First Search",
        description: "Implement BFS for graph traversal",
        competencies: [graphCompId],
        difficulty_level: 0.5,
        estimated_duration: 40,
        challenge_type: "coding",
        prerequisites: [arrayCompId]
    },
    {
        title: "Dynamic Programming - Coin Change",
        description: "Solve the coin change problem using dynamic programming",
        competencies: [recursionCompId],
        difficulty_level: 0.8,
        estimated_duration: 60,
        challenge_type: "coding",
        prerequisites: [recursionCompId]
    }
]);

// Create indexes for performance
db.learners.createIndex({ "email": 1 }, { unique: true });
db.learners.createIndex({ "username": 1 }, { unique: true });

db.learner_competencies.createIndex({ "learner_id": 1, "competency_id": 1 }, { unique: true });
db.learner_competencies.createIndex({ "learner_id": 1, "mastery_level": -1 });

db.learner_activity_logs.createIndex({ "learner_id": 1, "timestamp": -1 });
db.learner_activity_logs.createIndex({ "activity_type": 1, "timestamp": -1 });

db.challenges.createIndex({ "competencies": 1, "difficulty_level": 1 });
db.challenges.createIndex({ "challenge_type": 1 });

db.learner_progress.createIndex({ "learner_id": 1, "content_item_id": 1 }, { unique: true });

db.difficulty_feedback.createIndex({ "learner_id": 1, "challenge_id": 1, "submitted_at": -1 });

db.recommendation_history.createIndex({ "learner_id": 1, "timestamp": -1 });

print("✅ MongoDB initialization complete!");
print("📊 Sample data inserted:");
print("   - " + db.competencies.countDocuments({}) + " competencies");
print("   - " + db.challenges.countDocuments({}) + " challenges");
print("🔍 Indexes created for optimal performance");
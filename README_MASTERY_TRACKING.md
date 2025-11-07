# Mastery Tracking System Implementation

## Overview

This document describes the implementation of the Mastery Tracking System (STORY-002) for the Adaptive Learning System. The system accurately tracks learner mastery of programming and data structure concepts at a granular level using Bayesian Knowledge Tracing (BKT) algorithms.

## Features Implemented

### ✅ Core Requirements Met

1. **System logs learner interactions with activities** - Comprehensive interaction logging with detailed metadata
2. **System updates mastery levels for micro-competencies** - Real-time BKT-based mastery updates
3. **Learner can view detailed progress reports** - Rich progress reports with analytics and insights
4. **Mastery updates use Bayesian Knowledge Tracing (BKT) algorithm** - Full BKT implementation with configurable parameters
5. **Data is updated in near real-time** - Immediate processing with background analytics updates

## Architecture

### Components

```
src/
├── models/
│   └── mastery.py              # Pydantic models for all mastery tracking data
├── core/
│   └── bkt_engine.py           # Bayesian Knowledge Tracing algorithm implementation
├── db/
│   └── mastery_repository.py   # Database operations for mastery data
├── api/
│   └── mastery_endpoints.py    # FastAPI endpoints for mastery tracking
├── utils/
│   └── dependencies.py         # Dependency injection for FastAPI
└── main.py                     # Main FastAPI application
```

### Data Models

#### LearnerInteraction
Captures detailed information about learner interactions with activities:
- Activity metadata (type, difficulty, competencies)
- Performance data (score, correctness, attempts, time spent)
- Context information (session, hints used, metadata)

#### MasteryLevel
Tracks learner mastery for specific competencies:
- Current mastery probability (0.0 to 1.0)
- BKT parameters (prior knowledge, learning rate, slip/guess probabilities)
- Performance statistics (total/correct interactions, average score)
- Mastery status and achievement timestamps

#### MicroCompetency
Defines granular skills and knowledge components:
- Hierarchical categorization (category, subcategory)
- Difficulty levels and prerequisites
- Descriptive metadata

## API Endpoints

### Core Endpoints

#### POST `/api/v1/mastery/interactions`
Log a learner interaction and update mastery levels.

**Request Body:**
```json
{
  "learner_id": "learner_001",
  "activity_id": "quiz_arrays_001",
  "activity_type": "quiz",
  "interaction_type": "completion",
  "competency_ids": ["arrays_basic", "arrays_traversal"],
  "score": 0.85,
  "is_correct": true,
  "attempts": 1,
  "time_spent": 120.5,
  "hints_used": 0,
  "difficulty_level": "intermediate",
  "session_id": "session_123",
  "metadata": {
    "browser": "Chrome",
    "device": "desktop"
  }
}
```

**Response:**
```json
{
  "learner_id": "learner_001",
  "updated_competencies": ["arrays_basic", "arrays_traversal"],
  "new_mastery_levels": {
    "arrays_basic": 0.72,
    "arrays_traversal": 0.68
  },
  "newly_mastered": [],
  "processing_time": 0.045,
  "timestamp": "2025-01-27T10:30:00Z"
}
```

#### GET `/api/v1/mastery/progress/{learner_id}`
Get comprehensive progress report for a learner.

**Response:**
```json
{
  "learner_id": "learner_001",
  "generated_at": "2025-01-27T10:30:00Z",
  "total_competencies": 5,
  "mastered_competencies": 2,
  "mastery_percentage": 40.0,
  "competency_mastery": [...],
  "recent_interactions": [...],
  "performance_trend": [...],
  "recommended_activities": [...],
  "focus_areas": [...]
}
```

#### GET `/api/v1/mastery/mastery/{learner_id}/{competency_id}`
Get specific mastery level for a learner-competency pair.

#### GET `/api/v1/mastery/analytics/dashboard/{learner_id}`
Get dashboard data with advanced analytics and insights.

### Analytics Endpoints

#### GET `/api/v1/mastery/interactions/{learner_id}`
Get learner interactions with filtering options.

#### GET `/api/v1/mastery/competencies/{competency_id}/stats`
Get performance statistics for a competency across all learners.

## Bayesian Knowledge Tracing (BKT) Implementation

### Algorithm Overview

The BKT engine implements the standard four-parameter BKT model:

- **P(L₀)** - Prior knowledge: Initial probability of knowing the skill
- **P(T)** - Learning rate: Probability of learning the skill
- **P(S)** - Slip probability: Probability of making a mistake despite knowing
- **P(G)** - Guess probability: Probability of guessing correctly

### Update Formula

For correct responses:
```
P(L_{n+1} = 1 | correct) = [P(L_n = 1) × (1 - P(S))] / [P(L_n = 1) × (1 - P(S)) + (1 - P(L_n = 1)) × P(G)]
```

For incorrect responses:
```
P(L_{n+1} = 1 | incorrect) = [P(L_n = 1) × P(S)] / [P(L_n = 1) × P(S) + (1 - P(L_n = 1)) × (1 - P(G))]
```

Then apply learning rate:
```
P(L_{n+1}) = P(L_{n+1} | evidence) + (1 - P(L_{n+1} | evidence)) × P(T)
```

### Advanced Features

- **Confidence Intervals**: Wilson score intervals for mastery probability
- **Learning Velocity**: Rate of mastery improvement over time
- **Practice Recommendations**: Intensity suggestions based on current mastery
- **Batch Processing**: Efficient updates for multiple interactions

## Database Schema

### Collections

#### learner_interactions
```javascript
{
  _id: ObjectId,
  learner_id: String,
  activity_id: String,
  activity_type: String, // enum: quiz, coding_challenge, etc.
  interaction_type: String, // enum: attempt, completion, etc.
  competency_ids: [String],
  score: Number, // 0.0 to 1.0
  is_correct: Boolean,
  attempts: Number,
  time_spent: Number,
  hints_used: Number,
  difficulty_level: String,
  session_id: String,
  metadata: Object,
  started_at: Date,
  completed_at: Date,
  created_at: Date
}
```

#### mastery_levels
```javascript
{
  _id: ObjectId,
  learner_id: String,
  competency_id: String,
  current_mastery: Number, // 0.0 to 1.0
  bkt_parameters: {
    prior_knowledge: Number,
    learning_rate: Number,
    slip_probability: Number,
    guess_probability: Number
  },
  total_interactions: Number,
  correct_interactions: Number,
  average_score: Number,
  recent_performance: [Number],
  confidence_level: Number,
  mastery_threshold: Number,
  is_mastered: Boolean,
  first_interaction: Date,
  last_interaction: Date,
  mastery_achieved_at: Date,
  created_at: Date,
  updated_at: Date
}
```

#### micro_competencies
```javascript
{
  _id: ObjectId,
  competency_id: String,
  name: String,
  description: String,
  category: String,
  subcategory: String,
  prerequisites: [String],
  difficulty_level: String,
  created_at: Date,
  updated_at: Date
}
```

### Indexes

Optimized indexes for common query patterns:
- Learner interactions by learner and timestamp
- Mastery levels by learner-competency pairs
- Competency performance aggregations

## Setup and Deployment

### Prerequisites

- Python 3.11+
- MongoDB 4.4+
- Docker (optional)

### Local Development

1. **Clone and setup:**
```bash
git clone <repository-url>
cd adaptive-learning-system
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your MongoDB connection string
```

3. **Initialize database:**
```bash
# Start MongoDB (if using Docker)
docker-compose up mongodb -d

# Initialize with sample data
python scripts/sample_data_generator.py
```

4. **Run the application:**
```bash
uvicorn src.main:app --reload
```

5. **Access API documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build individual container
docker build -t mastery-tracking-api .
docker run -p 8000:8000 -e MONGODB_URI=<your-uri> mastery-tracking-api
```

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test files
pytest tests/test_bkt_engine.py
pytest tests/test_api_endpoints.py
```

### Test Coverage

The test suite covers:
- BKT algorithm correctness and edge cases
- API endpoint functionality and error handling
- Database operations and data validation
- Integration scenarios and performance

## Performance Considerations

### Real-time Processing

- **Immediate Updates**: Mastery levels updated synchronously during interaction logging
- **Background Analytics**: Heavy analytics computations run asynchronously
- **Caching Strategy**: Frequently accessed data cached for performance
- **Batch Processing**: Support for bulk interaction processing

### Scalability

- **Database Indexes**: Optimized for common query patterns
- **Connection Pooling**: Efficient database connection management
- **Horizontal Scaling**: Stateless API design supports multiple instances
- **Monitoring**: Built-in performance metrics and health checks

## Monitoring and Analytics

### Metrics Tracked

- **Processing Time**: Request processing duration
- **Mastery Changes**: Rate of mastery level updates
- **Interaction Volume**: Number of interactions per time period
- **Error Rates**: API error frequency and types

### Health Checks

- **API Health**: `/health` endpoint for service monitoring
- **Database Connectivity**: MongoDB connection status
- **Performance Metrics**: Response time tracking

## Security Considerations

### Data Protection

- **Input Validation**: Comprehensive request validation using Pydantic
- **SQL Injection Prevention**: MongoDB queries use parameterized operations
- **Rate Limiting**: Configurable request rate limits
- **CORS Configuration**: Proper cross-origin request handling

### Privacy Compliance

- **Data Minimization**: Only necessary data collected and stored
- **Anonymization**: Support for anonymized learner identifiers
- **Audit Trail**: Comprehensive logging for compliance requirements
- **Data Retention**: Configurable data retention policies

## Future Enhancements

### Planned Features

1. **Advanced Analytics**
   - Predictive mastery modeling
   - Learning path optimization
   - Comparative performance analysis

2. **Integration Capabilities**
   - External assessment system integration
   - Learning management system APIs
   - Real-time notification systems

3. **Enhanced BKT Models**
   - Multi-skill BKT implementation
   - Adaptive parameter tuning
   - Contextual factor integration

4. **Performance Optimizations**
   - Redis caching layer
   - Event-driven architecture
   - Stream processing for real-time analytics

## Troubleshooting

### Common Issues

1. **MongoDB Connection Errors**
   - Verify MONGODB_URI environment variable
   - Check network connectivity and authentication
   - Ensure database exists and user has permissions

2. **Slow API Responses**
   - Check database indexes are created
   - Monitor query performance
   - Consider caching frequently accessed data

3. **BKT Parameter Issues**
   - Verify parameters are within valid ranges (0.0 to 1.0)
   - Check for division by zero scenarios
   - Review interaction data quality

### Debugging

- **Logging**: Comprehensive logging at INFO level
- **Error Tracking**: Detailed error messages and stack traces
- **Performance Profiling**: Built-in request timing
- **Database Monitoring**: Query performance tracking

## Contributing

### Development Guidelines

1. **Code Style**: Follow PEP 8 and use type hints
2. **Testing**: Maintain >90% test coverage
3. **Documentation**: Update docstrings and API documentation
4. **Performance**: Consider scalability in all implementations

### Pull Request Process

1. Create feature branch from main
2. Implement changes with tests
3. Update documentation
4. Submit pull request with detailed description
5. Address review feedback

---

This implementation successfully delivers all requirements for STORY-002: Mastery Tracking System, providing a robust, scalable, and accurate system for tracking learner mastery using advanced Bayesian Knowledge Tracing algorithms.
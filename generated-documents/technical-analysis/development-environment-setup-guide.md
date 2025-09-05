# Development Environment Setup Guide
**Adaptive Learning System**

**Version:** 1.0  
**Date:** January 2025  
**Target Audience:** Developers, DevOps Engineers  

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup Instructions](#detailed-setup-instructions)
4. [IDE Configuration](#ide-configuration)
5. [Database Setup](#database-setup)
6. [Testing Environment](#testing-environment)
7. [Troubleshooting](#troubleshooting)
8. [Development Workflow](#development-workflow)

---

## Prerequisites

### System Requirements
- **Operating System:** Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **RAM:** Minimum 8GB, Recommended 16GB
- **Storage:** 20GB free space
- **Network:** Stable internet connection for package downloads

### Required Software

#### Core Tools
```bash
# Docker Desktop (includes Docker Compose)
# Download from: https://www.docker.com/products/docker-desktop

# Git
# Download from: https://git-scm.com/downloads

# Python 3.11+ (for local development)
# Download from: https://www.python.org/downloads/

# Node.js 18+ (for tooling and scripts)
# Download from: https://nodejs.org/
```

#### Verification Commands
```bash
# Verify installations
docker --version          # Should show 20.0+
docker-compose --version  # Should show 2.0+
git --version             # Should show 2.30+
python --version          # Should show 3.11+
node --version            # Should show 18.0+
npm --version             # Should show 8.0+
```

---

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/organization/adaptive-learning-system.git
cd adaptive-learning-system
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables (see configuration section below)
# Use your preferred text editor
nano .env  # or vim .env or code .env
```

### 3. Start Development Environment
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Verify services are running
docker-compose ps

# View logs
docker-compose logs -f api
```

### 4. Access Application
- **API Documentation:** http://localhost:8000/docs
- **API Base URL:** http://localhost:8000/api/v1
- **MongoDB:** localhost:27017
- **Redis:** localhost:6379

---

## Detailed Setup Instructions

### Environment Configuration

#### .env File Configuration
```bash
# Application Settings
ENVIRONMENT=development
DEBUG=true
API_VERSION=v1
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration
MONGODB_URL=mongodb://mongo:27017/adaptive_learning_dev
MONGODB_DATABASE=adaptive_learning_dev

# Cache Configuration
REDIS_URL=redis://redis:6379/0

# Security Settings
JWT_SECRET_KEY=dev-jwt-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# External APIs (Development)
TALENTQ_API_KEY=dev-api-key
TALENTQ_API_URL=https://api-dev.talentq.com/v1

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=detailed

# Development Features
ENABLE_CORS=true
ENABLE_DEBUG_TOOLBAR=true
```

### Docker Compose Configuration

#### docker-compose.dev.yml
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - /app/__pycache__
      - /app/.pytest_cache
    environment:
      - ENVIRONMENT=development
      - MONGODB_URL=mongodb://mongo:27017/adaptive_learning_dev
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - mongo
      - redis
    restart: unless-stopped
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
      - ./scripts/mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    environment:
      - MONGO_INITDB_DATABASE=adaptive_learning_dev
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  mongo-express:
    image: mongo-express:latest
    ports:
      - "8081:8081"
    environment:
      - ME_CONFIG_MONGODB_SERVER=mongo
      - ME_CONFIG_MONGODB_PORT=27017
      - ME_CONFIG_BASICAUTH_USERNAME=admin
      - ME_CONFIG_BASICAUTH_PASSWORD=admin123
    depends_on:
      - mongo
    restart: unless-stopped

volumes:
  mongo_data:
  redis_data:
```

#### Dockerfile.dev
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Development command (overridden in docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## IDE Configuration

### Visual Studio Code

#### Required Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.pylint",
    "ms-python.isort",
    "ms-azuretools.vscode-docker",
    "mongodb.mongodb-vscode",
    "eamodio.gitlens",
    "humao.rest-client",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml"
  ]
}
```

#### Workspace Settings (.vscode/settings.json)
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/node_modules": true,
    "**/.git": false
  },
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "python.linting.pylintArgs": [
    "--load-plugins=pylint_django",
    "--django-settings-module=settings"
  ]
}
```

#### Launch Configuration (.vscode/launch.json)
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal",
      "env": {
        "ENVIRONMENT": "development"
      }
    },
    {
      "name": "Python: Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

### PyCharm Configuration

#### Project Structure
```
adaptive-learning-system/
├── .idea/                 # PyCharm configuration
├── app/                   # Application source code
├── tests/                 # Test files
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
└── docker-compose.dev.yml # Development environment
```

#### Run Configurations
1. **FastAPI Server**
   - Script path: `main.py`
   - Parameters: `--host 0.0.0.0 --port 8000 --reload`
   - Environment variables: Load from `.env`

2. **Pytest**
   - Target: `tests/`
   - Additional arguments: `-v --cov=app`

---

## Database Setup

### MongoDB Development Database

#### Initialization Script (scripts/mongo-init.js)
```javascript
// Initialize development database
db = db.getSiblingDB('adaptive_learning_dev');

// Create collections with validation
db.createCollection('learners', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['username', 'email', 'created_at'],
      properties: {
        username: { bsonType: 'string' },
        email: { bsonType: 'string' },
        created_at: { bsonType: 'date' }
      }
    }
  }
});

// Create indexes
db.learners.createIndex({ 'email': 1 }, { unique: true });
db.learners.createIndex({ 'username': 1 }, { unique: true });

// Insert sample data
db.learners.insertMany([
  {
    username: 'test_learner',
    email: 'test@example.com',
    demographics: { age: 25, location: 'US' },
    preferences: { learning_style: 'visual' },
    created_at: new Date()
  },
  {
    username: 'demo_user',
    email: 'demo@example.com',
    demographics: { age: 30, location: 'UK' },
    preferences: { learning_style: 'kinesthetic' },
    created_at: new Date()
  }
]);

print('Development database initialized successfully');
```

#### Database Management Commands
```bash
# Connect to MongoDB container
docker-compose exec mongo mongosh adaptive_learning_dev

# Backup development database
docker-compose exec mongo mongodump --db adaptive_learning_dev --out /tmp/backup

# Restore database
docker-compose exec mongo mongorestore --db adaptive_learning_dev /tmp/backup/adaptive_learning_dev

# View database logs
docker-compose logs mongo
```

### Sample Data Loading

#### Load Sample Data Script (scripts/load_sample_data.py)
```python
#!/usr/bin/env python3
"""Load sample data for development environment."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os

async def load_sample_data():
    """Load sample data into development database."""
    client = AsyncIOMotorClient(os.getenv('MONGODB_URL', 'mongodb://localhost:27017'))
    db = client.adaptive_learning_dev
    
    # Sample competencies
    competencies = [
        {'name': 'Recursion', 'description': 'Understanding recursive algorithms'},
        {'name': 'Dynamic Programming', 'description': 'Optimization using memoization'},
        {'name': 'Graph Traversal', 'description': 'BFS and DFS algorithms'}
    ]
    
    await db.competencies.insert_many(competencies)
    
    # Sample content modules
    modules = [
        {
            'title': 'Introduction to Recursion',
            'description': 'Basic concepts of recursive programming',
            'competencies': ['Recursion']
        }
    ]
    
    await db.content_modules.insert_many(modules)
    
    print("Sample data loaded successfully")

if __name__ == '__main__':
    asyncio.run(load_sample_data())
```

---

## Testing Environment

### Test Configuration

#### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --strict-config
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    api: API endpoint tests
```

#### Test Database Setup
```python
# tests/conftest.py
import pytest
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.database import get_database

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def test_db():
    """Create test database."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.adaptive_learning_test
    
    # Clean database before test
    await db.drop_collection("learners")
    await db.drop_collection("competencies")
    
    yield db
    
    # Clean up after test
    await client.drop_database("adaptive_learning_test")
    client.close()
```

### Running Tests

#### Test Commands
```bash
# Run all tests
docker-compose exec api pytest

# Run specific test file
docker-compose exec api pytest tests/test_learners.py

# Run with coverage
docker-compose exec api pytest --cov=app --cov-report=html

# Run only unit tests
docker-compose exec api pytest -m unit

# Run tests in parallel
docker-compose exec api pytest -n auto

# Run tests with verbose output
docker-compose exec api pytest -v -s
```

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Error: Port 8000 is already in use
# Solution: Kill process using the port
lsof -ti:8000 | xargs kill -9

# Or use different port
docker-compose -f docker-compose.dev.yml up -d --scale api=0
docker-compose -f docker-compose.dev.yml run --service-ports -p 8001:8000 api
```

#### 2. MongoDB Connection Issues
```bash
# Check MongoDB container status
docker-compose ps mongo

# View MongoDB logs
docker-compose logs mongo

# Restart MongoDB
docker-compose restart mongo

# Connect to MongoDB shell
docker-compose exec mongo mongosh
```

#### 3. Python Dependencies Issues
```bash
# Rebuild API container
docker-compose build api

# Clear Python cache
docker-compose exec api find . -name "*.pyc" -delete
docker-compose exec api find . -name "__pycache__" -type d -exec rm -rf {} +

# Reinstall dependencies
docker-compose exec api pip install -r requirements-dev.txt
```

#### 4. Volume Permission Issues (Linux/macOS)
```bash
# Fix volume permissions
sudo chown -R $USER:$USER .
chmod -R 755 .

# Or run with user mapping
docker-compose -f docker-compose.dev.yml run --user $(id -u):$(id -g) api
```

### Debug Mode

#### Enable Debug Logging
```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or modify .env file
echo "LOG_LEVEL=DEBUG" >> .env

# Restart services
docker-compose restart
```

#### Debug API Requests
```bash
# Use curl for API testing
curl -X GET "http://localhost:8000/api/v1/health" -H "accept: application/json"

# Use httpie (install with: pip install httpie)
http GET localhost:8000/api/v1/health

# View API documentation
open http://localhost:8000/docs
```

---

## Development Workflow

### Daily Development Process

#### 1. Start Development Session
```bash
# Pull latest changes
git pull origin main

# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# Check service health
curl http://localhost:8000/health
```

#### 2. Code Development
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and test
docker-compose exec api pytest tests/

# Format code
docker-compose exec api black .
docker-compose exec api isort .
```

#### 3. Testing and Validation
```bash
# Run full test suite
docker-compose exec api pytest --cov=app

# Run linting
docker-compose exec api pylint app/

# Test API endpoints
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "email": "test@example.com", "password": "password123"}'
```

#### 4. Commit and Push
```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add user registration endpoint"

# Push to remote
git push origin feature/new-feature
```

### Code Quality Checks

#### Pre-commit Hooks (.pre-commit-config.yaml)
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
```

#### Install Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

---

## Additional Resources

### Documentation Links
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Motor Documentation](https://motor.readthedocs.io/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Pytest Documentation](https://docs.pytest.org/)

### Useful Commands Reference
```bash
# Docker commands
docker-compose up -d              # Start services in background
docker-compose down               # Stop and remove containers
docker-compose logs -f [service]  # Follow logs for specific service
docker-compose exec [service] sh  # Execute shell in container
docker-compose build [service]    # Rebuild specific service

# Database commands
mongosh                           # Connect to MongoDB
db.collection.find()             # Query collection
db.collection.createIndex()      # Create index
db.stats()                       # Database statistics

# Python commands
pip freeze > requirements.txt     # Export dependencies
python -m pytest                 # Run tests
python -m black .                # Format code
python -m isort .                # Sort imports
```

---

**Support:** For technical issues, please create an issue in the project repository or contact the development team.

**Last Updated:** January 2025  
**Version:** 1.0
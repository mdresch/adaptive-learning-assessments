# Learner Profile Management API Documentation

## Overview

The Learner Profile Management API provides comprehensive functionality for managing learner profiles in the Adaptive Learning System. This API supports user registration, authentication, profile management, and personalization features.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

The API uses JWT (JSON Web Token) based authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Register Learner

**POST** `/learners/register`

Creates a new learner profile with comprehensive demographic, learning preference, and accessibility information.

#### Request Body

```json
{
  "email": "learner@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePass123",
  "username": "johndoe",
  "demographics": {
    "age": 25,
    "education_level": "bachelor",
    "country": "United States",
    "timezone": "America/New_York",
    "preferred_language": "en"
  },
  "learning_preferences": {
    "learning_styles": ["visual", "kinesthetic"],
    "session_duration_preference": 30,
    "difficulty_preference": "adaptive"
  },
  "programming_experience": {
    "overall_experience": "beginner",
    "languages_known": ["python", "javascript"],
    "years_of_experience": 1,
    "professional_experience": false
  },
  "accessibility_settings": {
    "enabled_features": ["large_text"],
    "font_size_multiplier": 1.2,
    "contrast_preference": "normal"
  },
  "goals": ["Learn data structures", "Prepare for interviews"],
  "interests": ["algorithms", "web development"]
}
```

#### Response (201 Created)

```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "learner@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "demographics": {
    "age": 25,
    "education_level": "bachelor",
    "country": "United States",
    "timezone": "America/New_York",
    "preferred_language": "en"
  },
  "learning_preferences": {
    "learning_styles": ["visual", "kinesthetic"],
    "session_duration_preference": 30,
    "difficulty_preference": "adaptive"
  },
  "programming_experience": {
    "overall_experience": "beginner",
    "languages_known": ["python", "javascript"],
    "years_of_experience": 1,
    "professional_experience": false
  },
  "accessibility_settings": {
    "enabled_features": ["large_text"],
    "font_size_multiplier": 1.2,
    "contrast_preference": "normal"
  },
  "goals": ["Learn data structures", "Prepare for interviews"],
  "interests": ["algorithms", "web development"],
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_login": null,
  "profile_completion_percentage": 85.0
}
```

### 2. Login

**POST** `/learners/login`

Authenticates a learner and returns a JWT access token.

#### Request Body (Form Data)

```
username: learner@example.com
password: SecurePass123
```

#### Response (200 OK)

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 3. Get Current Profile

**GET** `/learners/me`

Retrieves the authenticated learner's complete profile information.

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Response (200 OK)

```json
{
  "id": "507f1f77bcf86cd799439011",
  "email": "learner@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "demographics": {
    "age": 25,
    "education_level": "bachelor",
    "country": "United States"
  },
  "learning_preferences": {
    "learning_styles": ["visual", "kinesthetic"],
    "session_duration_preference": 30
  },
  "programming_experience": {
    "overall_experience": "beginner",
    "languages_known": ["python", "javascript"]
  },
  "accessibility_settings": {
    "enabled_features": ["large_text"],
    "font_size_multiplier": 1.2
  },
  "goals": ["Learn data structures"],
  "interests": ["algorithms"],
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T11:00:00Z",
  "profile_completion_percentage": 85.0
}
```

### 4. Update Profile

**PUT** `/learners/me`

Updates the authenticated learner's profile. Changes immediately influence learning path personalization.

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Request Body

```json
{
  "first_name": "Jane",
  "demographics": {
    "age": 30,
    "education_level": "master"
  },
  "learning_preferences": {
    "learning_styles": ["visual", "auditory"],
    "session_duration_preference": 45
  },
  "programming_experience": {
    "overall_experience": "intermediate",
    "languages_known": ["python", "javascript", "java"],
    "years_of_experience": 3
  },
  "accessibility_settings": {
    "enabled_features": ["large_text", "high_contrast"],
    "font_size_multiplier": 1.5
  },
  "goals": ["Master algorithms", "Get a senior developer job"],
  "interests": ["machine learning", "system design"]
}
```

#### Response (200 OK)

Returns the updated profile with the same structure as the GET endpoint.

### 5. Get Profile by ID

**GET** `/learners/{learner_id}`

Retrieves a specific learner's profile by ID. Currently restricted to the learner's own profile.

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Response (200 OK)

Same structure as GET `/learners/me`.

### 6. Delete Profile

**DELETE** `/learners/me`

Performs a soft delete of the authenticated learner's profile (marks as inactive).

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Response (204 No Content)

No response body.

### 7. Get Profile Completion Statistics

**GET** `/learners/stats/completion`

Returns detailed information about profile completion status and suggestions for improvement.

#### Headers
```
Authorization: Bearer <jwt_token>
```

#### Response (200 OK)

```json
{
  "completion_percentage": 85.0,
  "is_complete": true,
  "missing_fields": ["interests"],
  "suggestions": [
    "Add your interests to discover relevant learning content"
  ],
  "total_fields": 8,
  "completed_fields": 7
}
```

## Data Models

### Education Levels

- `high_school`
- `associate`
- `bachelor`
- `master`
- `doctorate`
- `bootcamp`
- `self_taught`
- `other`

### Learning Styles

- `visual`
- `auditory`
- `kinesthetic`
- `reading_writing`
- `multimodal`

### Programming Experience Levels

- `none`
- `beginner`
- `intermediate`
- `advanced`
- `expert`

### Accessibility Features

- `screen_reader`
- `high_contrast`
- `large_text`
- `keyboard_navigation`
- `reduced_motion`
- `audio_descriptions`
- `captions`

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Email address already exists"
}
```

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden

```json
{
  "detail": "Access denied: Can only access your own profile"
}
```

### 404 Not Found

```json
{
  "detail": "Learner profile not found"
}
```

### 422 Validation Error

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Security Considerations

1. **Password Requirements**: Passwords must be at least 8 characters with uppercase, lowercase, and numeric characters.
2. **JWT Tokens**: Tokens expire after 30 minutes by default.
3. **Data Privacy**: Learners can only access their own profile data.
4. **Soft Deletion**: Profile deletion preserves learning history while preventing access.

## Rate Limiting

Currently no rate limiting is implemented, but it's recommended for production deployments.

## Pagination

Search endpoints support pagination with `skip` and `limit` parameters:

- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 20, max: 100)

## Health Check

**GET** `/health`

Returns system health status including database connectivity.

```json
{
  "status": "healthy",
  "service": "Adaptive Learning System",
  "version": "1.0.0",
  "database": "connected"
}
```
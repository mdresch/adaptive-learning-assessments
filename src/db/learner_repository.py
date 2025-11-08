"""
Learner Profile Repository

This module provides data access layer for learner profile operations
including CRUD operations and profile management functionality.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorCollection

from ..models.learner_profile import (
    LearnerProfile,
    LearnerProfileCreate,
    LearnerProfileUpdate,
    LearnerProfileResponse
)
from ..utils.security import get_password_hash, verify_password


class LearnerRepository:
    """Repository for learner profile data operations"""
    
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection
    
    async def create_indexes(self):
        """Create database indexes for optimal performance"""
        await self.collection.create_index("email", unique=True)
        await self.collection.create_index("username", unique=True, sparse=True)
        await self.collection.create_index("created_at")
        await self.collection.create_index("is_active")
        await self.collection.create_index([
            ("demographics.country", 1),
            ("programming_experience.overall_experience", 1)
        ])
    
    async def create_learner_profile(self, profile_data: LearnerProfileCreate) -> LearnerProfile:
        """Create a new learner profile"""
        try:
            # Hash the password
            hashed_password = get_password_hash(profile_data.password)
            
            # Convert to dict and remove password, add hashed version
            profile_dict = profile_data.dict(exclude={"password"})
            profile_dict["hashed_password"] = hashed_password
            profile_dict["created_at"] = datetime.utcnow()
            profile_dict["updated_at"] = datetime.utcnow()
            profile_dict["profile_completion_percentage"] = self._calculate_completion_percentage(profile_dict)
            
            # Insert into database
            result = await self.collection.insert_one(profile_dict)
            
            # Retrieve and return the created profile
            created_profile = await self.collection.find_one({"_id": result.inserted_id})
            return LearnerProfile(**created_profile)
            
        except DuplicateKeyError as e:
            if "email" in str(e):
                raise ValueError("Email address already exists")
            elif "username" in str(e):
                raise ValueError("Username already exists")
            else:
                raise ValueError("Duplicate key error")
    
    async def get_learner_by_id(self, learner_id: str) -> Optional[LearnerProfile]:
        """Get learner profile by ID"""
        try:
            object_id = ObjectId(learner_id)
            profile_data = await self.collection.find_one({"_id": object_id, "is_active": True})
            
            if profile_data:
                return LearnerProfile(**profile_data)
            return None
            
        except Exception:
            return None
    
    async def get_learner_by_email(self, email: str) -> Optional[LearnerProfile]:
        """Get learner profile by email"""
        profile_data = await self.collection.find_one({"email": email.lower(), "is_active": True})
        
        if profile_data:
            return LearnerProfile(**profile_data)
        return None
    
    async def get_learner_by_username(self, username: str) -> Optional[LearnerProfile]:
        """Get learner profile by username"""
        profile_data = await self.collection.find_one({"username": username.lower(), "is_active": True})
        
        if profile_data:
            return LearnerProfile(**profile_data)
        return None
    
    async def update_learner_profile(self, learner_id: str, update_data: LearnerProfileUpdate) -> Optional[LearnerProfile]:
        """Update learner profile"""
        try:
            object_id = ObjectId(learner_id)
            
            # Convert update data to dict, excluding None values
            update_dict = update_data.dict(exclude_unset=True, exclude_none=True)
            
            if not update_dict:
                # No updates to apply
                return await self.get_learner_by_id(learner_id)
            
            # Add updated timestamp
            update_dict["updated_at"] = datetime.utcnow()
            
            # Update the profile
            result = await self.collection.update_one(
                {"_id": object_id, "is_active": True},
                {"$set": update_dict}
            )
            
            if result.modified_count == 0:
                return None
            
            # Recalculate completion percentage
            updated_profile = await self.collection.find_one({"_id": object_id})
            completion_percentage = self._calculate_completion_percentage(updated_profile)
            
            await self.collection.update_one(
                {"_id": object_id},
                {"$set": {"profile_completion_percentage": completion_percentage}}
            )
            
            # Return updated profile
            return await self.get_learner_by_id(learner_id)
            
        except Exception:
            return None
    
    async def delete_learner_profile(self, learner_id: str) -> bool:
        """Soft delete learner profile (mark as inactive)"""
        try:
            object_id = ObjectId(learner_id)
            
            result = await self.collection.update_one(
                {"_id": object_id, "is_active": True},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception:
            return False
    
    async def authenticate_learner(self, email: str, password: str) -> Optional[LearnerProfile]:
        """Authenticate learner with email and password"""
        profile_data = await self.collection.find_one({"email": email.lower(), "is_active": True})
        
        if not profile_data:
            return None
        
        if not verify_password(password, profile_data.get("hashed_password", "")):
            return None
        
        # Update last login
        await self.collection.update_one(
            {"_id": profile_data["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        return LearnerProfile(**profile_data)
    
    async def search_learners(self, 
                            skip: int = 0, 
                            limit: int = 20, 
                            filters: Optional[Dict[str, Any]] = None) -> List[LearnerProfile]:
        """Search learners with pagination and filters"""
        query = {"is_active": True}
        
        if filters:
            # Add search filters
            if "country" in filters:
                query["demographics.country"] = filters["country"]
            if "education_level" in filters:
                query["demographics.education_level"] = filters["education_level"]
            if "experience_level" in filters:
                query["programming_experience.overall_experience"] = filters["experience_level"]
            if "search_text" in filters:
                # Text search in name and email - escape regex special characters
                import re
                search_text = re.escape(filters["search_text"])
                query["$or"] = [
                    {"first_name": {"$regex": search_text, "$options": "i"}},
                    {"last_name": {"$regex": search_text, "$options": "i"}},
                    {"email": {"$regex": search_text, "$options": "i"}}
                ]
        
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        profiles = []
        
        async for profile_data in cursor:
            profiles.append(LearnerProfile(**profile_data))
        
        return profiles
    
    async def get_learner_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Get total count of learners matching filters"""
        query = {"is_active": True}
        
        if filters:
            if "country" in filters:
                query["demographics.country"] = filters["country"]
            if "education_level" in filters:
                query["demographics.education_level"] = filters["education_level"]
            if "experience_level" in filters:
                query["programming_experience.overall_experience"] = filters["experience_level"]
        
        return await self.collection.count_documents(query)
    
    async def update_last_login(self, learner_id: str) -> bool:
        """Update last login timestamp"""
        try:
            object_id = ObjectId(learner_id)
            
            result = await self.collection.update_one(
                {"_id": object_id, "is_active": True},
                {"$set": {"last_login": datetime.utcnow()}}
            )
            
            return result.modified_count > 0
            
        except Exception:
            return False
    
    def _calculate_completion_percentage(self, profile_data: Dict[str, Any]) -> float:
        """Calculate profile completion percentage"""
        total_fields = 0
        completed_fields = 0
        
        # Required fields
        required_fields = ["email", "first_name", "last_name"]
        for field in required_fields:
            total_fields += 1
            if profile_data.get(field):
                completed_fields += 1
        
        # Demographics fields
        demographics = profile_data.get("demographics", {})
        demo_fields = ["age", "education_level", "country", "timezone"]
        for field in demo_fields:
            total_fields += 1
            if demographics.get(field):
                completed_fields += 1
        
        # Learning preferences
        learning_prefs = profile_data.get("learning_preferences", {})
        if learning_prefs.get("learning_styles"):
            completed_fields += 1
        total_fields += 1
        
        # Programming experience
        prog_exp = profile_data.get("programming_experience", {})
        if prog_exp.get("overall_experience") and prog_exp.get("overall_experience") != "none":
            completed_fields += 1
        total_fields += 1
        
        # Goals and interests
        if profile_data.get("goals"):
            completed_fields += 1
        total_fields += 1
        
        if profile_data.get("interests"):
            completed_fields += 1
        total_fields += 1
        
        return round((completed_fields / total_fields) * 100, 2) if total_fields > 0 else 0.0
"""
Learner Repository

This module provides data access methods for learner profiles,
handling CRUD operations and database interactions.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.learner import (
    LearnerProfile, 
    LearnerProfileUpdate, 
    LearnerProfileResponse,
    SelfReportedData
)

logger = logging.getLogger(__name__)


class LearnerRepository:
    """Repository class for learner profile data operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.collection = database.learners
    
    async def create_learner_profile(self, learner_data: LearnerProfile) -> str:
        """
        Create a new learner profile
        
        Args:
            learner_data: LearnerProfile object containing profile information
            
        Returns:
            str: The ID of the created learner profile
            
        Raises:
            DuplicateKeyError: If username or email already exists
            Exception: For other database errors
        """
        try:
            # Ensure updated_at is set to current time
            learner_data.updated_at = datetime.utcnow()
            
            # Convert to dict and handle ObjectId
            learner_dict = learner_data.dict(by_alias=True, exclude_unset=True)
            
            # Insert the document
            result = await self.collection.insert_one(learner_dict)
            
            logger.info(f"Created learner profile with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error creating learner profile: {e}")
            if "username" in str(e):
                raise ValueError("Username already exists")
            elif "email" in str(e):
                raise ValueError("Email already exists")
            else:
                raise ValueError("Duplicate key error")
        except Exception as e:
            logger.error(f"Error creating learner profile: {e}")
            raise
    
    async def get_learner_profile_by_id(self, learner_id: str) -> Optional[LearnerProfileResponse]:
        """
        Retrieve a learner profile by ID
        
        Args:
            learner_id: The learner's unique identifier
            
        Returns:
            LearnerProfileResponse object or None if not found
        """
        try:
            if not ObjectId.is_valid(learner_id):
                return None
            
            learner_doc = await self.collection.find_one({"_id": ObjectId(learner_id)})
            
            if learner_doc:
                # Convert ObjectId to string for response
                learner_doc["id"] = str(learner_doc["_id"])
                del learner_doc["_id"]
                
                # Remove sensitive fields
                sensitive_fields = ["hashed_password", "privacy_consent", "data_processing_consent", "marketing_consent"]
                for field in sensitive_fields:
                    learner_doc.pop(field, None)
                
                return LearnerProfileResponse(**learner_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving learner profile {learner_id}: {e}")
            raise
    
    async def get_learner_profile_by_username(self, username: str) -> Optional[LearnerProfile]:
        """
        Retrieve a learner profile by username
        
        Args:
            username: The learner's username
            
        Returns:
            LearnerProfile object or None if not found
        """
        try:
            learner_doc = await self.collection.find_one({"username": username})
            
            if learner_doc:
                # Convert ObjectId to string
                learner_doc["id"] = str(learner_doc["_id"])
                del learner_doc["_id"]
                
                return LearnerProfile(**learner_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving learner profile by username {username}: {e}")
            raise
    
    async def get_learner_profile_by_email(self, email: str) -> Optional[LearnerProfile]:
        """
        Retrieve a learner profile by email
        
        Args:
            email: The learner's email address
            
        Returns:
            LearnerProfile object or None if not found
        """
        try:
            learner_doc = await self.collection.find_one({"email": email})
            
            if learner_doc:
                # Convert ObjectId to string
                learner_doc["id"] = str(learner_doc["_id"])
                del learner_doc["_id"]
                
                return LearnerProfile(**learner_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving learner profile by email {email}: {e}")
            raise
    
    async def update_learner_profile(self, learner_id: str, update_data: LearnerProfileUpdate) -> bool:
        """
        Update a learner profile
        
        Args:
            learner_id: The learner's unique identifier
            update_data: LearnerProfileUpdate object containing fields to update
            
        Returns:
            bool: True if update was successful, False if learner not found
        """
        try:
            if not ObjectId.is_valid(learner_id):
                return False
            
            # Prepare update document
            update_dict = update_data.dict(exclude_unset=True, exclude_none=True)
            
            if not update_dict:
                return True  # No changes to make
            
            # Always update the updated_at timestamp
            update_dict["updated_at"] = datetime.utcnow()
            
            # Perform the update
            result = await self.collection.update_one(
                {"_id": ObjectId(learner_id)},
                {"$set": update_dict}
            )
            
            if result.matched_count == 0:
                logger.warning(f"No learner found with ID: {learner_id}")
                return False
            
            logger.info(f"Updated learner profile {learner_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating learner profile {learner_id}: {e}")
            raise
    
    async def add_self_reported_data(self, learner_id: str, self_reported_data: SelfReportedData) -> bool:
        """
        Add self-reported data to a learner profile
        
        Args:
            learner_id: The learner's unique identifier
            self_reported_data: SelfReportedData object to add
            
        Returns:
            bool: True if addition was successful, False if learner not found
        """
        try:
            if not ObjectId.is_valid(learner_id):
                return False
            
            # Convert to dict
            data_dict = self_reported_data.dict()
            
            # Add to the self_reported_data array and update timestamp
            result = await self.collection.update_one(
                {"_id": ObjectId(learner_id)},
                {
                    "$push": {"self_reported_data": data_dict},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
            if result.matched_count == 0:
                logger.warning(f"No learner found with ID: {learner_id}")
                return False
            
            logger.info(f"Added self-reported data to learner profile {learner_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding self-reported data to learner {learner_id}: {e}")
            raise
    
    async def update_last_login(self, learner_id: str) -> bool:
        """
        Update the last login timestamp for a learner
        
        Args:
            learner_id: The learner's unique identifier
            
        Returns:
            bool: True if update was successful, False if learner not found
        """
        try:
            if not ObjectId.is_valid(learner_id):
                return False
            
            current_time = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(learner_id)},
                {
                    "$set": {
                        "last_login": current_time,
                        "updated_at": current_time
                    }
                }
            )
            
            return result.matched_count > 0
            
        except Exception as e:
            logger.error(f"Error updating last login for learner {learner_id}: {e}")
            raise
    
    async def deactivate_learner_profile(self, learner_id: str) -> bool:
        """
        Deactivate a learner profile (soft delete)
        
        Args:
            learner_id: The learner's unique identifier
            
        Returns:
            bool: True if deactivation was successful, False if learner not found
        """
        try:
            if not ObjectId.is_valid(learner_id):
                return False
            
            result = await self.collection.update_one(
                {"_id": ObjectId(learner_id)},
                {
                    "$set": {
                        "is_active": False,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.matched_count == 0:
                logger.warning(f"No learner found with ID: {learner_id}")
                return False
            
            logger.info(f"Deactivated learner profile {learner_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating learner profile {learner_id}: {e}")
            raise
    
    async def get_learners_by_criteria(self, 
                                     skip: int = 0, 
                                     limit: int = 100,
                                     is_active: Optional[bool] = None,
                                     education_level: Optional[str] = None,
                                     programming_experience: Optional[str] = None) -> List[LearnerProfileResponse]:
        """
        Retrieve learners based on criteria with pagination
        
        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            is_active: Filter by active status
            education_level: Filter by education level
            programming_experience: Filter by programming experience level
            
        Returns:
            List of LearnerProfileResponse objects
        """
        try:
            # Build query filter
            query_filter = {}
            
            if is_active is not None:
                query_filter["is_active"] = is_active
            
            if education_level:
                query_filter["demographics.education_level"] = education_level
            
            if programming_experience:
                query_filter["programming_experience.overall_level"] = programming_experience
            
            # Execute query with pagination
            cursor = self.collection.find(query_filter).skip(skip).limit(limit)
            learner_docs = await cursor.to_list(length=limit)
            
            # Convert to response objects
            learners = []
            for doc in learner_docs:
                # Convert ObjectId to string
                doc["id"] = str(doc["_id"])
                del doc["_id"]
                
                # Remove sensitive fields
                sensitive_fields = ["hashed_password", "privacy_consent", "data_processing_consent", "marketing_consent"]
                for field in sensitive_fields:
                    doc.pop(field, None)
                
                learners.append(LearnerProfileResponse(**doc))
            
            return learners
            
        except Exception as e:
            logger.error(f"Error retrieving learners by criteria: {e}")
            raise
    
    async def count_learners(self, is_active: Optional[bool] = None) -> int:
        """
        Count total number of learners
        
        Args:
            is_active: Filter by active status
            
        Returns:
            int: Total count of learners
        """
        try:
            query_filter = {}
            if is_active is not None:
                query_filter["is_active"] = is_active
            
            count = await self.collection.count_documents(query_filter)
            return count
            
        except Exception as e:
            logger.error(f"Error counting learners: {e}")
            raise
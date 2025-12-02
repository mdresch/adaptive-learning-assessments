"""
Template Analytics Repository

This module provides data access methods for template analytics functionality,
including template entity profiles and document domain inference.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError

from ..models.template_analytics import (
    TemplateEntityProfile,
    TemplateEntityProfileCreate,
    TemplateEntityProfileUpdate,
    DocumentDomainInference,
    DocumentDomainInferenceCreate,
    DocumentDomainInferenceUpdate,
    TemplateAnalyticsAggregation,
    DomainAnalyticsAggregation,
    DomainCategory,
    TemplateType
)

logger = logging.getLogger(__name__)


class TemplateAnalyticsRepository:
    """Repository for template analytics operations"""

    def __init__(self, template_collection: AsyncIOMotorCollection, domain_collection: AsyncIOMotorCollection):
        self.template_collection = template_collection
        self.domain_collection = domain_collection

    async def create_indexes(self):
        """Create necessary indexes for optimal query performance"""
        try:
            # Template entity profile indexes
            await self.template_collection.create_index([("template_id", ASCENDING)], unique=True)
            await self.template_collection.create_index([("template_type", ASCENDING)])
            await self.template_collection.create_index([("is_active", ASCENDING)])
            await self.template_collection.create_index([("effectiveness_score", DESCENDING)])
            await self.template_collection.create_index([("usage_metrics.total_uses", DESCENDING)])
            await self.template_collection.create_index([("domain_associations.domain", ASCENDING)])
            await self.template_collection.create_index([("tags", ASCENDING)])
            await self.template_collection.create_index([("created_at", DESCENDING)])
            
            # Text index for template search
            await self.template_collection.create_index([
                ("template_name", TEXT),
                ("description", TEXT),
                ("tags", TEXT)
            ])

            # Document domain inference indexes
            await self.domain_collection.create_index([("document_id", ASCENDING)], unique=True)
            await self.domain_collection.create_index([("inferred_primary_domain", ASCENDING)])
            await self.domain_collection.create_index([("confidence_score", DESCENDING)])
            await self.domain_collection.create_index([("document_type", ASCENDING)])
            await self.domain_collection.create_index([("inference_date", DESCENDING)])
            await self.domain_collection.create_index([("secondary_domains.domain", ASCENDING)])

            logger.info("Template analytics indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating template analytics indexes: {e}")
            raise

    # Template Entity Profile Operations

    async def create_template_profile(self, profile_data: TemplateEntityProfileCreate) -> TemplateEntityProfile:
        """Create a new template entity profile"""
        try:
            profile = TemplateEntityProfile(**profile_data.dict())
            result = await self.template_collection.insert_one(profile.dict(by_alias=True))
            profile.id = result.inserted_id
            
            logger.info(f"Created template profile for template_id: {profile.template_id}")
            return profile

        except DuplicateKeyError:
            logger.error(f"Template profile already exists for template_id: {profile_data.template_id}")
            raise ValueError(f"Template profile already exists for template_id: {profile_data.template_id}")
        except Exception as e:
            logger.error(f"Error creating template profile: {e}")
            raise

    async def get_template_profile(self, template_id: str) -> Optional[TemplateEntityProfile]:
        """Get template profile by template_id"""
        try:
            document = await self.template_collection.find_one({"template_id": template_id})
            if document:
                return TemplateEntityProfile(**document)
            return None

        except Exception as e:
            logger.error(f"Error retrieving template profile for {template_id}: {e}")
            raise

    async def update_template_profile(self, template_id: str, update_data: TemplateEntityProfileUpdate) -> Optional[TemplateEntityProfile]:
        """Update template profile"""
        try:
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            if not update_dict:
                return await self.get_template_profile(template_id)

            update_dict["updated_at"] = datetime.utcnow()
            
            result = await self.template_collection.find_one_and_update(
                {"template_id": template_id},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                logger.info(f"Updated template profile for template_id: {template_id}")
                return TemplateEntityProfile(**result)
            return None

        except Exception as e:
            logger.error(f"Error updating template profile for {template_id}: {e}")
            raise

    async def delete_template_profile(self, template_id: str) -> bool:
        """Delete template profile"""
        try:
            result = await self.template_collection.delete_one({"template_id": template_id})
            success = result.deleted_count > 0
            
            if success:
                logger.info(f"Deleted template profile for template_id: {template_id}")
            
            return success

        except Exception as e:
            logger.error(f"Error deleting template profile for {template_id}: {e}")
            raise

    async def update_template_usage(self, template_id: str, usage_data: Dict[str, Any]) -> bool:
        """Update template usage metrics"""
        try:
            update_operations = {
                "$inc": {
                    "usage_metrics.total_uses": usage_data.get("increment_uses", 1)
                },
                "$set": {
                    "usage_metrics.last_used": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }

            # Update other metrics if provided
            if "completion_rate" in usage_data:
                update_operations["$set"]["usage_metrics.completion_rate"] = usage_data["completion_rate"]
            if "average_score" in usage_data:
                update_operations["$set"]["usage_metrics.average_score"] = usage_data["average_score"]
            if "average_time_spent" in usage_data:
                update_operations["$set"]["usage_metrics.average_time_spent"] = usage_data["average_time_spent"]

            result = await self.template_collection.update_one(
                {"template_id": template_id},
                update_operations
            )

            success = result.modified_count > 0
            if success:
                logger.info(f"Updated usage metrics for template_id: {template_id}")
            
            return success

        except Exception as e:
            logger.error(f"Error updating template usage for {template_id}: {e}")
            raise

    async def get_templates_by_domain(self, domain: DomainCategory, limit: int = 50) -> List[TemplateEntityProfile]:
        """Get templates associated with a specific domain"""
        try:
            cursor = self.template_collection.find(
                {"domain_associations.domain": domain.value, "is_active": True}
            ).sort("effectiveness_score", DESCENDING).limit(limit)
            
            templates = []
            async for document in cursor:
                templates.append(TemplateEntityProfile(**document))
            
            return templates

        except Exception as e:
            logger.error(f"Error retrieving templates for domain {domain}: {e}")
            raise

    async def get_top_performing_templates(self, limit: int = 10) -> List[TemplateEntityProfile]:
        """Get top performing templates by effectiveness score"""
        try:
            cursor = self.template_collection.find(
                {"is_active": True}
            ).sort("effectiveness_score", DESCENDING).limit(limit)
            
            templates = []
            async for document in cursor:
                templates.append(TemplateEntityProfile(**document))
            
            return templates

        except Exception as e:
            logger.error(f"Error retrieving top performing templates: {e}")
            raise

    # Document Domain Inference Operations

    async def create_domain_inference(self, inference_data: DocumentDomainInferenceCreate) -> DocumentDomainInference:
        """Create a new document domain inference"""
        try:
            inference = DocumentDomainInference(**inference_data.dict())
            result = await self.domain_collection.insert_one(inference.dict(by_alias=True))
            inference.id = result.inserted_id
            
            logger.info(f"Created domain inference for document_id: {inference.document_id}")
            return inference

        except DuplicateKeyError:
            logger.error(f"Domain inference already exists for document_id: {inference_data.document_id}")
            raise ValueError(f"Domain inference already exists for document_id: {inference_data.document_id}")
        except Exception as e:
            logger.error(f"Error creating domain inference: {e}")
            raise

    async def get_domain_inference(self, document_id: str) -> Optional[DocumentDomainInference]:
        """Get domain inference by document_id"""
        try:
            document = await self.domain_collection.find_one({"document_id": document_id})
            if document:
                return DocumentDomainInference(**document)
            return None

        except Exception as e:
            logger.error(f"Error retrieving domain inference for {document_id}: {e}")
            raise

    async def update_domain_inference(self, document_id: str, update_data: DocumentDomainInferenceUpdate) -> Optional[DocumentDomainInference]:
        """Update domain inference"""
        try:
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            if not update_dict:
                return await self.get_domain_inference(document_id)

            update_dict["updated_at"] = datetime.utcnow()
            
            result = await self.domain_collection.find_one_and_update(
                {"document_id": document_id},
                {"$set": update_dict},
                return_document=True
            )
            
            if result:
                logger.info(f"Updated domain inference for document_id: {document_id}")
                return DocumentDomainInference(**result)
            return None

        except Exception as e:
            logger.error(f"Error updating domain inference for {document_id}: {e}")
            raise

    async def get_documents_by_domain(self, domain: DomainCategory, min_confidence: float = 0.7, limit: int = 50) -> List[DocumentDomainInference]:
        """Get documents by inferred domain with minimum confidence"""
        try:
            cursor = self.domain_collection.find({
                "inferred_primary_domain": domain.value,
                "confidence_score": {"$gte": min_confidence}
            }).sort("confidence_score", DESCENDING).limit(limit)
            
            documents = []
            async for document in cursor:
                documents.append(DocumentDomainInference(**document))
            
            return documents

        except Exception as e:
            logger.error(f"Error retrieving documents for domain {domain}: {e}")
            raise

    # Analytics and Aggregation Operations

    async def get_template_analytics(self, days_back: int = 30) -> TemplateAnalyticsAggregation:
        """Get comprehensive template analytics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Aggregate template statistics
            pipeline = [
                {"$match": {"created_at": {"$gte": start_date}}},
                {"$group": {
                    "_id": None,
                    "total_templates": {"$sum": 1},
                    "active_templates": {"$sum": {"$cond": ["$is_active", 1, 0]}},
                    "avg_effectiveness": {"$avg": "$effectiveness_score"},
                    "templates_by_type": {"$push": "$template_type"},
                    "templates_by_domain": {"$push": "$domain_associations.domain"}
                }}
            ]
            
            result = await self.template_collection.aggregate(pipeline).to_list(1)
            
            if not result:
                return TemplateAnalyticsAggregation(
                    total_templates=0,
                    active_templates=0,
                    templates_by_type={},
                    templates_by_domain={},
                    average_effectiveness=0.0,
                    top_performing_templates=[],
                    usage_trends={}
                )
            
            data = result[0]
            
            # Count templates by type
            type_counts = {}
            for template_type in data.get("templates_by_type", []):
                type_counts[template_type] = type_counts.get(template_type, 0) + 1
            
            # Count templates by domain (flatten nested arrays)
            domain_counts = {}
            for domain_list in data.get("templates_by_domain", []):
                if isinstance(domain_list, list):
                    for domain in domain_list:
                        domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            # Get top performing templates
            top_templates = await self.get_top_performing_templates(5)
            top_templates_data = [
                {
                    "template_id": t.template_id,
                    "template_name": t.template_name,
                    "effectiveness_score": t.effectiveness_score,
                    "total_uses": t.usage_metrics.total_uses
                }
                for t in top_templates
            ]
            
            return TemplateAnalyticsAggregation(
                total_templates=data.get("total_templates", 0),
                active_templates=data.get("active_templates", 0),
                templates_by_type=type_counts,
                templates_by_domain=domain_counts,
                average_effectiveness=data.get("avg_effectiveness", 0.0),
                top_performing_templates=top_templates_data,
                usage_trends={}  # TODO: Implement usage trends calculation
            )

        except Exception as e:
            logger.error(f"Error getting template analytics: {e}")
            raise

    async def get_domain_analytics(self, days_back: int = 30) -> DomainAnalyticsAggregation:
        """Get comprehensive domain analytics"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Aggregate domain statistics
            pipeline = [
                {"$match": {"inference_date": {"$gte": start_date}}},
                {"$group": {
                    "_id": None,
                    "total_documents": {"$sum": 1},
                    "avg_confidence": {"$avg": "$confidence_score"},
                    "high_confidence_docs": {"$sum": {"$cond": [{"$gte": ["$confidence_score", 0.8]}, 1, 0]}},
                    "domains": {"$push": "$inferred_primary_domain"}
                }}
            ]
            
            result = await self.domain_collection.aggregate(pipeline).to_list(1)
            
            if not result:
                return DomainAnalyticsAggregation(
                    total_documents=0,
                    domain_distribution={},
                    average_confidence=0.0,
                    high_confidence_documents=0,
                    domain_trends={},
                    content_feature_stats={}
                )
            
            data = result[0]
            
            # Count documents by domain
            domain_counts = {}
            for domain in data.get("domains", []):
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            return DomainAnalyticsAggregation(
                total_documents=data.get("total_documents", 0),
                domain_distribution=domain_counts,
                average_confidence=data.get("avg_confidence", 0.0),
                high_confidence_documents=data.get("high_confidence_docs", 0),
                domain_trends={},  # TODO: Implement domain trends calculation
                content_feature_stats={}  # TODO: Implement content feature statistics
            )

        except Exception as e:
            logger.error(f"Error getting domain analytics: {e}")
            raise

    async def search_templates(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 20) -> List[TemplateEntityProfile]:
        """Search templates by text query and filters"""
        try:
            search_filter = {"$text": {"$search": query}}
            
            if filters:
                if "template_type" in filters:
                    search_filter["template_type"] = filters["template_type"]
                if "domain" in filters:
                    search_filter["domain_associations.domain"] = filters["domain"]
                if "is_active" in filters:
                    search_filter["is_active"] = filters["is_active"]
                if "min_effectiveness" in filters:
                    search_filter["effectiveness_score"] = {"$gte": filters["min_effectiveness"]}
            
            cursor = self.template_collection.find(search_filter).limit(limit)
            
            templates = []
            async for document in cursor:
                templates.append(TemplateEntityProfile(**document))
            
            return templates

        except Exception as e:
            logger.error(f"Error searching templates: {e}")
            raise
"""
Template Analytics API Routes

This module provides REST API endpoints for template analytics functionality,
including template entity profiles and document domain inference.
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import JSONResponse

from ..db.database import get_database
from ..db.template_analytics_repository import TemplateAnalyticsRepository
from ..core.domain_inference_engine import DomainInferenceEngine
from ..models.template_analytics import (
    TemplateEntityProfile,
    TemplateEntityProfileCreate,
    TemplateEntityProfileUpdate,
    TemplateEntityProfileResponse,
    DocumentDomainInference,
    DocumentDomainInferenceCreate,
    DocumentDomainInferenceUpdate,
    DocumentDomainInferenceResponse,
    TemplateAnalyticsAggregation,
    DomainAnalyticsAggregation,
    DomainCategory,
    TemplateType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/template-analytics", tags=["Template Analytics"])

# Dependency to get repository
async def get_template_analytics_repository(db=Depends(get_database)) -> TemplateAnalyticsRepository:
    """Get template analytics repository instance"""
    template_collection = db.get_collection("template_entity_profiles")
    domain_collection = db.get_collection("document_domain_inferences")
    return TemplateAnalyticsRepository(template_collection, domain_collection)

# Dependency to get domain inference engine
def get_domain_inference_engine() -> DomainInferenceEngine:
    """Get domain inference engine instance"""
    return DomainInferenceEngine()


# Template Entity Profile Endpoints

@router.post("/templates", response_model=TemplateEntityProfileResponse, status_code=201)
async def create_template_profile(
    profile_data: TemplateEntityProfileCreate,
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """Create a new template entity profile"""
    try:
        profile = await repository.create_template_profile(profile_data)
        return TemplateEntityProfileResponse(
            id=str(profile.id),
            template_id=profile.template_id,
            template_name=profile.template_name,
            template_type=profile.template_type.value,
            description=profile.description,
            domain_associations=profile.domain_associations,
            usage_metrics=profile.usage_metrics,
            effectiveness_score=profile.effectiveness_score,
            tags=profile.tags,
            is_active=profile.is_active,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating template profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/templates/{template_id}", response_model=TemplateEntityProfileResponse)
async def get_template_profile(
    template_id: str,
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """Get template profile by template ID"""
    try:
        profile = await repository.get_template_profile(template_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Template profile not found")
        
        return TemplateEntityProfileResponse(
            id=str(profile.id),
            template_id=profile.template_id,
            template_name=profile.template_name,
            template_type=profile.template_type.value,
            description=profile.description,
            domain_associations=profile.domain_associations,
            usage_metrics=profile.usage_metrics,
            effectiveness_score=profile.effectiveness_score,
            tags=profile.tags,
            is_active=profile.is_active,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving template profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/templates/{template_id}", response_model=TemplateEntityProfileResponse)
async def update_template_profile(
    template_id: str,
    update_data: TemplateEntityProfileUpdate,
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """Update template profile"""
    try:
        profile = await repository.update_template_profile(template_id, update_data)
        if not profile:
            raise HTTPException(status_code=404, detail="Template profile not found")
        
        return TemplateEntityProfileResponse(
            id=str(profile.id),
            template_id=profile.template_id,
            template_name=profile.template_name,
            template_type=profile.template_type.value,
            description=profile.description,
            domain_associations=profile.domain_associations,
            usage_metrics=profile.usage_metrics,
            effectiveness_score=profile.effectiveness_score,
            tags=profile.tags,
            is_active=profile.is_active,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating template profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template_profile(
    template_id: str,
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """Delete template profile"""
    try:
        success = await repository.delete_template_profile(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template profile not found")
        
        return JSONResponse(status_code=204, content=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting template profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/templates/{template_id}/track-usage", status_code=200)
async def track_template_usage(
    template_id: str,
    usage_data: Dict[str, Any] = Body(...),
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """Track template usage and update metrics"""
    try:
        success = await repository.update_template_usage(template_id, usage_data)
        if not success:
            raise HTTPException(status_code=404, detail="Template profile not found")
        
        return {"message": "Usage tracked successfully", "template_id": template_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking template usage: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/templates", response_model=List[TemplateEntityProfileResponse])
async def list_templates(
    domain: Optional[DomainCategory] = Query(None, description="Filter by domain"),
    template_type: Optional[TemplateType] = Query(None, description="Filter by template type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """List templates with optional filters"""
    try:
        if domain:
            templates = await repository.get_templates_by_domain(domain, limit)
        else:
            # For now, get top performing templates if no domain specified
            templates = await repository.get_top_performing_templates(limit)
        
        return [
            TemplateEntityProfileResponse(
                id=str(template.id),
                template_id=template.template_id,
                template_name=template.template_name,
                template_type=template.template_type.value,
                description=template.description,
                domain_associations=template.domain_associations,
                usage_metrics=template.usage_metrics,
                effectiveness_score=template.effectiveness_score,
                tags=template.tags,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            for template in templates
        ]
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/templates/search", response_model=List[TemplateEntityProfileResponse])
async def search_templates(
    q: str = Query(..., description="Search query"),
    template_type: Optional[TemplateType] = Query(None, description="Filter by template type"),
    domain: Optional[DomainCategory] = Query(None, description="Filter by domain"),
    min_effectiveness: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum effectiveness score"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results"),
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """Search templates by text query"""
    try:
        filters = {}
        if template_type:
            filters["template_type"] = template_type.value
        if domain:
            filters["domain"] = domain.value
        if min_effectiveness is not None:
            filters["min_effectiveness"] = min_effectiveness
        
        templates = await repository.search_templates(q, filters, limit)
        
        return [
            TemplateEntityProfileResponse(
                id=str(template.id),
                template_id=template.template_id,
                template_name=template.template_name,
                template_type=template.template_type.value,
                description=template.description,
                domain_associations=template.domain_associations,
                usage_metrics=template.usage_metrics,
                effectiveness_score=template.effectiveness_score,
                tags=template.tags,
                is_active=template.is_active,
                created_at=template.created_at,
                updated_at=template.updated_at
            )
            for template in templates
        ]
    except Exception as e:
        logger.error(f"Error searching templates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Document Domain Inference Endpoints

@router.post("/documents/domain-inference", response_model=DocumentDomainInferenceResponse, status_code=201)
async def create_domain_inference(
    inference_data: DocumentDomainInferenceCreate,
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """Create a new document domain inference"""
    try:
        inference = await repository.create_domain_inference(inference_data)
        return DocumentDomainInferenceResponse(
            id=str(inference.id),
            document_id=inference.document_id,
            document_type=inference.document_type,
            inferred_primary_domain=inference.inferred_primary_domain.value,
            confidence_score=inference.confidence_score,
            secondary_domains=inference.secondary_domains,
            manual_override=inference.manual_override.value if inference.manual_override else None,
            inference_date=inference.inference_date,
            updated_at=inference.updated_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating domain inference: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents/{document_id}/domain", response_model=DocumentDomainInferenceResponse)
async def get_document_domain(
    document_id: str,
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """Get domain inference for a document"""
    try:
        inference = await repository.get_domain_inference(document_id)
        if not inference:
            raise HTTPException(status_code=404, detail="Domain inference not found")
        
        return DocumentDomainInferenceResponse(
            id=str(inference.id),
            document_id=inference.document_id,
            document_type=inference.document_type,
            inferred_primary_domain=inference.inferred_primary_domain.value,
            confidence_score=inference.confidence_score,
            secondary_domains=inference.secondary_domains,
            manual_override=inference.manual_override.value if inference.manual_override else None,
            inference_date=inference.inference_date,
            updated_at=inference.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving domain inference: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/documents/{document_id}/domain", response_model=DocumentDomainInferenceResponse)
async def update_domain_inference(
    document_id: str,
    update_data: DocumentDomainInferenceUpdate,
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """Update document domain inference"""
    try:
        inference = await repository.update_domain_inference(document_id, update_data)
        if not inference:
            raise HTTPException(status_code=404, detail="Domain inference not found")
        
        return DocumentDomainInferenceResponse(
            id=str(inference.id),
            document_id=inference.document_id,
            document_type=inference.document_type,
            inferred_primary_domain=inference.inferred_primary_domain.value,
            confidence_score=inference.confidence_score,
            secondary_domains=inference.secondary_domains,
            manual_override=inference.manual_override.value if inference.manual_override else None,
            inference_date=inference.inference_date,
            updated_at=inference.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating domain inference: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documents/infer-domain", response_model=DocumentDomainInferenceResponse, status_code=201)
async def infer_document_domain(
    document_data: Dict[str, Any] = Body(...),
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository),
    engine: DomainInferenceEngine = Depends(get_domain_inference_engine)
):
    """Automatically infer domain for a document"""
    try:
        document_id = document_data.get("document_id")
        content = document_data.get("content", "")
        document_type = document_data.get("document_type", "unknown")
        metadata = document_data.get("metadata", {})
        
        if not document_id:
            raise HTTPException(status_code=400, detail="document_id is required")
        
        # Infer domain using the engine
        primary_domain, confidence, secondary_domains = engine.infer_domain(content, metadata)
        
        # Create inference record
        inference_data = DocumentDomainInferenceCreate(
            document_id=document_id,
            document_type=document_type,
            inferred_primary_domain=primary_domain,
            confidence_score=confidence,
            secondary_domains=secondary_domains,
            analysis_metadata={
                "engine_version": "1.0",
                "content_length": len(content),
                "metadata_provided": bool(metadata)
            },
            content_features=engine.analyze_content(content, metadata)
        )
        
        inference = await repository.create_domain_inference(inference_data)
        
        return DocumentDomainInferenceResponse(
            id=str(inference.id),
            document_id=inference.document_id,
            document_type=inference.document_type,
            inferred_primary_domain=inference.inferred_primary_domain.value,
            confidence_score=inference.confidence_score,
            secondary_domains=inference.secondary_domains,
            manual_override=inference.manual_override.value if inference.manual_override else None,
            inference_date=inference.inference_date,
            updated_at=inference.updated_at
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error inferring document domain: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documents/batch-infer-domains")
async def batch_infer_domains(
    documents: List[Dict[str, Any]] = Body(...),
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository),
    engine: DomainInferenceEngine = Depends(get_domain_inference_engine)
):
    """Batch infer domains for multiple documents"""
    try:
        results = engine.batch_infer_domains(documents)
        
        # Create inference records for successful inferences
        created_inferences = []
        errors = []
        
        for doc_id, primary_domain, confidence, secondary_domains in results:
            try:
                # Find the original document data
                doc_data = next((doc for doc in documents if doc.get("id") == doc_id), {})
                
                inference_data = DocumentDomainInferenceCreate(
                    document_id=doc_id,
                    document_type=doc_data.get("document_type", "unknown"),
                    inferred_primary_domain=primary_domain,
                    confidence_score=confidence,
                    secondary_domains=secondary_domains,
                    analysis_metadata={
                        "engine_version": "1.0",
                        "batch_processing": True,
                        "content_length": len(doc_data.get("content", ""))
                    }
                )
                
                inference = await repository.create_domain_inference(inference_data)
                created_inferences.append({
                    "document_id": doc_id,
                    "inferred_domain": primary_domain.value,
                    "confidence": confidence,
                    "inference_id": str(inference.id)
                })
                
            except Exception as e:
                errors.append({
                    "document_id": doc_id,
                    "error": str(e)
                })
        
        return {
            "processed": len(results),
            "successful": len(created_inferences),
            "failed": len(errors),
            "results": created_inferences,
            "errors": errors
        }
        
    except Exception as e:
        logger.error(f"Error in batch domain inference: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Analytics Endpoints

@router.get("/analytics/templates", response_model=TemplateAnalyticsAggregation)
async def get_template_analytics(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """Get comprehensive template analytics"""
    try:
        analytics = await repository.get_template_analytics(days_back)
        return analytics
    except Exception as e:
        logger.error(f"Error getting template analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/analytics/domains", response_model=DomainAnalyticsAggregation)
async def get_domain_analytics(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """Get comprehensive domain analytics"""
    try:
        analytics = await repository.get_domain_analytics(days_back)
        return analytics
    except Exception as e:
        logger.error(f"Error getting domain analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents/by-domain/{domain}", response_model=List[DocumentDomainInferenceResponse])
async def get_documents_by_domain(
    domain: DomainCategory,
    min_confidence: float = Query(0.7, ge=0.0, le=1.0, description="Minimum confidence score"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    repository: TemplateAnalyticsRepository = Depends(get_template_analytics_repository)
):
    """Get documents by inferred domain"""
    try:
        documents = await repository.get_documents_by_domain(domain, min_confidence, limit)
        
        return [
            DocumentDomainInferenceResponse(
                id=str(doc.id),
                document_id=doc.document_id,
                document_type=doc.document_type,
                inferred_primary_domain=doc.inferred_primary_domain.value,
                confidence_score=doc.confidence_score,
                secondary_domains=doc.secondary_domains,
                manual_override=doc.manual_override.value if doc.manual_override else None,
                inference_date=doc.inference_date,
                updated_at=doc.updated_at
            )
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error getting documents by domain: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
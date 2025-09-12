"""
Spatial API endpoints for GIS-enhanced LA system
Adds spatial intelligence while preserving existing functionality
"""
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from db import get_db
from la.models import LAMatter, LASpatialLayer, LAAutomatedAnswer, LAFile
from spatial import spatial_intelligence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/spatial", tags=["spatial"])

@router.get("/matters/{matter_id}/location")
async def get_matter_location(matter_id: str, db: Session = Depends(get_db)):
    """Get spatial location data for a matter"""
    matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    return {
        "matter_id": matter_id,
        "address": matter.address,
        "coordinates": {
            "latitude": matter.latitude,
            "longitude": matter.longitude,
            "easting": matter.easting,
            "northing": matter.northing
        },
        "has_geometry": matter.geometry_wkt is not None,
        "has_centroid": matter.centroid_wkt is not None
    }

@router.get("/matters/{matter_id}/overlays")
async def get_spatial_overlays(matter_id: str, db: Session = Depends(get_db)):
    """Get all spatial overlays for a matter"""
    matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    overlays = db.query(LASpatialLayer).filter(LASpatialLayer.matter_id == matter_id).all()
    
    result = {}
    for overlay in overlays:
        if overlay.layer_type not in result:
            result[overlay.layer_type] = []
        
        result[overlay.layer_type].append({
            "id": overlay.id,
            "source": overlay.source,
            "properties": json.loads(overlay.properties) if overlay.properties else {},
            "confidence": overlay.confidence,
            "created_at": overlay.created_at.isoformat()
        })
    
    return {
        "matter_id": matter_id,
        "overlays": result,
        "total_layers": len(overlays)
    }

@router.get("/matters/{matter_id}/automated-answers")
async def get_automated_answers(matter_id: str, db: Session = Depends(get_db)):
    """Get automated CON29 answers from spatial analysis"""
    matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    answers = db.query(LAAutomatedAnswer).filter(LAAutomatedAnswer.matter_id == matter_id).all()
    
    return {
        "matter_id": matter_id,
        "answers": [
            {
                "question_code": answer.question_code,
                "question_text": answer.question_text,
                "answer": answer.answer,
                "method": answer.method,
                "confidence": answer.confidence,
                "created_at": answer.created_at.isoformat(),
                "has_spatial_evidence": answer.spatial_evidence is not None
            }
            for answer in answers
        ],
        "total_answers": len(answers)
    }

@router.post("/matters/{matter_id}/geocode")
async def geocode_matter_address(matter_id: str, db: Session = Depends(get_db)):
    """Manually trigger geocoding for a matter address"""
    matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    if not matter.address:
        raise HTTPException(status_code=400, detail="Matter has no address to geocode")
    
    try:
        spatial_data = await spatial_intelligence.geocode_address(matter.address)
        if not spatial_data:
            raise HTTPException(status_code=404, detail="Address could not be geocoded")
        
        # Update matter with spatial data
        from geoalchemy2.shape import from_shape
        
        matter.latitude = spatial_data.get("latitude")
        matter.longitude = spatial_data.get("longitude")
        matter.easting = spatial_data.get("easting") 
        matter.northing = spatial_data.get("northing")
        
        if spatial_data.get("centroid"):
            matter.centroid = from_shape(spatial_data["centroid"])
        
        db.commit()
        
        return {
            "matter_id": matter_id,
            "address": matter.address,
            "geocoded": True,
            "coordinates": {
                "latitude": matter.latitude,
                "longitude": matter.longitude,
                "easting": matter.easting,
                "northing": matter.northing
            },
            "confidence": spatial_data.get("confidence", 0.8)
        }
        
    except Exception as e:
        logger.error(f"Geocoding failed for matter {matter_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Geocoding failed: {str(e)}")

@router.post("/matters/{matter_id}/site-plan")
async def upload_site_plan(
    matter_id: str, 
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload site plan and extract property boundary"""
    matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        # Save the uploaded plan
        import os, uuid
        upload_dir = "data/uploads/plans"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_id = str(uuid.uuid4())
        file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create file record
        file_record = LAFile(
            matter_id=matter_id,
            filename=file.filename,
            stored_path=file_path,
            kind="plan",
            content_type=file.content_type,
            file_size=len(contents),
            processing_status="processing"
        )
        db.add(file_record)
        db.commit()
        
        # Extract boundary using computer vision
        boundary = await spatial_intelligence.extract_boundary_from_plan(file_path)
        
        if boundary:
            from geoalchemy2.shape import from_shape
            matter.geometry = from_shape(boundary)
            
            # Create spatial layer record
            spatial_layer = LASpatialLayer(
                matter_id=matter_id,
                layer_type="property_boundary",
                source="plan_extraction",
                geometry=from_shape(boundary),
                properties=json.dumps({
                    "extracted_from": file.filename,
                    "method": "computer_vision"
                }),
                confidence=0.7
            )
            db.add(spatial_layer)
            
            file_record.processing_status = "completed"
            db.commit()
            
            return {
                "matter_id": matter_id,
                "filename": file.filename,
                "boundary_extracted": True,
                "file_id": file_record.id,
                "boundary_points": len(list(boundary.exterior.coords))
            }
        else:
            file_record.processing_status = "failed"
            db.commit()
            
            return {
                "matter_id": matter_id,  
                "filename": file.filename,
                "boundary_extracted": False,
                "file_id": file_record.id,
                "message": "Could not extract boundary from plan"
            }
            
    except Exception as e:
        logger.error(f"Site plan processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Site plan processing failed: {str(e)}")

@router.post("/matters/{matter_id}/analyze")
async def trigger_spatial_analysis(matter_id: str, db: Session = Depends(get_db)):
    """Manually trigger comprehensive spatial analysis for a matter"""
    matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    
    if not (matter.geometry or matter.centroid):
        raise HTTPException(status_code=400, detail="Matter needs geometry or location for spatial analysis")
        
    try:
        from geoalchemy2.shape import to_shape
        from shapely.geometry import Point
        
        # Get the geometry to analyze
        if matter.geometry:
            analysis_geom = to_shape(matter.geometry)
        elif matter.centroid:
            point = to_shape(matter.centroid)
            analysis_geom = point.buffer(0.001)  # 100m buffer
        else:
            raise HTTPException(status_code=400, detail="No geometry available for analysis")
        
        # Get spatial overlays
        overlays = await spatial_intelligence.get_spatial_overlays(
            analysis_geom,
            ["flood_zones", "conservation_areas", "tree_preservation", "planning_constraints", "highways"]
        )
        
        # Generate automated answers
        automated_answers = await spatial_intelligence.generate_con29_answers(matter_id, overlays)
        
        # Persist new spatial layers and answers
        from geoalchemy2.shape import from_shape
        
        # Clear existing automated data for fresh analysis
        db.query(LASpatialLayer).filter(LASpatialLayer.matter_id == matter_id).delete()
        db.query(LAAutomatedAnswer).filter(LAAutomatedAnswer.matter_id == matter_id).delete()
        
        # Save new overlays
        layer_count = 0
        for layer_type, features in overlays.items():
            for feature in features:
                if feature.get("geometry"):
                    spatial_layer = LASpatialLayer(
                        matter_id=matter_id,
                        layer_type=layer_type,
                        source=feature.get("source", "analysis"),
                        geometry=from_shape(feature["geometry"]),
                        properties=json.dumps(feature),
                        confidence=feature.get("confidence", 1.0)
                    )
                    db.add(spatial_layer)
                    layer_count += 1
        
        # Save automated answers
        for answer in automated_answers:
            answer_record = LAAutomatedAnswer(
                matter_id=matter_id,
                question_code=answer.get("question_code", ""),
                question_text=answer.get("question_text", ""),
                answer=answer.get("answer", ""),
                method=answer.get("method", "spatial_analysis"),
                confidence=answer.get("confidence", 1.0),
                spatial_evidence=answer.get("spatial_evidence")
            )
            db.add(answer_record)
        
        db.commit()
        
        return {
            "matter_id": matter_id,
            "analysis_completed": True,
            "spatial_layers_created": layer_count,
            "automated_answers_generated": len(automated_answers),
            "overlays_analyzed": list(overlays.keys())
        }
        
    except Exception as e:
        logger.error(f"Spatial analysis failed for matter {matter_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Spatial analysis failed: {str(e)}")

@router.get("/layers/available")
async def get_available_layers():
    """Get list of available spatial layers for analysis"""
    return {
        "layers": [
            {
                "code": "flood_zones",
                "name": "Flood Risk Zones", 
                "source": "Environment Agency",
                "description": "Flood risk areas from EA flood maps"
            },
            {
                "code": "conservation_areas",
                "name": "Conservation Areas",
                "source": "Local Authority",
                "description": "Designated conservation areas"
            },
            {
                "code": "tree_preservation",
                "name": "Tree Preservation Orders",
                "source": "Local Authority", 
                "description": "Protected trees and woodland"
            },
            {
                "code": "planning_constraints",
                "name": "Planning Constraints",
                "source": "Planning Portal",
                "description": "Planning permissions and constraints"
            },
            {
                "code": "highways",
                "name": "Highways and Transport",
                "source": "OS / Local Authority",
                "description": "Road networks and transport infrastructure"
            }
        ]
    }

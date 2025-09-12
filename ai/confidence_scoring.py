# 🎯 **CONFIDENCE SCORING & QUALITY ASSURANCE SYSTEM**
## *Automated Quality Control for 90%+ Accuracy*

import asyncio
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """Confidence levels for automated processing"""
    VERY_HIGH = "very_high"  # 95%+ - Fully automated
    HIGH = "high"            # 85-94% - Automated with light review
    MEDIUM = "medium"        # 70-84% - Requires review
    LOW = "low"              # 50-69% - Manual processing
    VERY_LOW = "very_low"    # <50% - Full manual review

@dataclass
class QualityMetrics:
    """Quality assessment metrics for document processing"""
    overall_confidence: float
    field_confidences: Dict[str, float]
    processing_quality: float
    data_completeness: float
    cross_validation_score: float
    manual_review_required: bool
    automation_rate: float

class AdvancedConfidenceScoring:
    """Advanced confidence scoring system for LA document processing"""
    
    def __init__(self):
        # Confidence thresholds for different automation levels
        self.automation_thresholds = {
            ConfidenceLevel.VERY_HIGH: 0.95,
            ConfidenceLevel.HIGH: 0.85,
            ConfidenceLevel.MEDIUM: 0.70,
            ConfidenceLevel.LOW: 0.50
        }
        
        # Field importance weights (sum to 1.0)
        self.field_weights = {
            # Critical fields (high impact on legal risk)
            'conservation_area': 0.15,
            'listed_building': 0.15,
            'flood_zone': 0.12,
            'enforcement_notices': 0.12,
            'highway_adoption': 0.10,
            
            # Important fields
            'planning_applications': 0.08,
            'contaminated_land': 0.08,
            'tree_preservation_orders': 0.06,
            
            # Supporting fields  
            'building_regulations': 0.04,
            'utilities_sewers': 0.04,
            'other_constraints': 0.06
        }
        
        # Historical accuracy data for model calibration
        self.historical_accuracy = {}
        self.load_historical_data()
        
    def load_historical_data(self):
        """Load historical accuracy data for confidence calibration"""
        # This would load from database in production
        self.historical_accuracy = {
            'conservation_area': {'total': 1000, 'correct': 920, 'accuracy': 0.92},
            'listed_building': {'total': 800, 'correct': 760, 'accuracy': 0.95},
            'flood_zone': {'total': 1200, 'correct': 1140, 'accuracy': 0.95},
            'enforcement_notices': {'total': 600, 'correct': 480, 'accuracy': 0.80},
            'highway_adoption': {'total': 900, 'correct': 792, 'accuracy': 0.88}
        }
        
    async def calculate_confidence_scores(self, extraction_results: Dict[str, Any],
                                        spatial_results: Optional[Dict] = None,
                                        document_quality: Optional[Dict] = None) -> QualityMetrics:
        """Calculate comprehensive confidence scores for all extracted data"""
        
        try:
            # Calculate individual field confidence scores
            field_confidences = await self._calculate_field_confidences(
                extraction_results, spatial_results, document_quality
            )
            
            # Calculate overall confidence (weighted average)
            overall_confidence = self._calculate_overall_confidence(field_confidences)
            
            # Assess processing quality
            processing_quality = self._assess_processing_quality(document_quality or {})
            
            # Calculate data completeness
            data_completeness = self._calculate_completeness(extraction_results)
            
            # Cross-validate with spatial data
            cross_validation_score = await self._cross_validate_spatial(
                extraction_results, spatial_results
            )
            
            # Determine if manual review is required
            manual_review_required = self._requires_manual_review(
                overall_confidence, field_confidences, processing_quality
            )
            
            # Calculate automation rate achievement
            automation_rate = self._calculate_automation_rate(
                overall_confidence, manual_review_required
            )
            
            quality_metrics = QualityMetrics(
                overall_confidence=overall_confidence,
                field_confidences=field_confidences,
                processing_quality=processing_quality,
                data_completeness=data_completeness,
                cross_validation_score=cross_validation_score,
                manual_review_required=manual_review_required,
                automation_rate=automation_rate
            )
            
            logger.info(f"Confidence scoring complete. Overall: {overall_confidence:.2%}, "
                       f"Automation rate: {automation_rate:.2%}")
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {str(e)}")
            return QualityMetrics(
                overall_confidence=0.0,
                field_confidences={},
                processing_quality=0.0,
                data_completeness=0.0,
                cross_validation_score=0.0,
                manual_review_required=True,
                automation_rate=0.0
            )
            
    async def _calculate_field_confidences(self, extraction_results: Dict,
                                         spatial_results: Optional[Dict],
                                         document_quality: Optional[Dict]) -> Dict[str, float]:
        """Calculate confidence scores for individual fields"""
        
        field_confidences = {}
        
        # Conservation Area confidence
        field_confidences['conservation_area'] = await self._score_conservation_area(
            extraction_results.get('conservation_area', {}),
            spatial_results.get('conservation_constraints', {}) if spatial_results else {},
            document_quality
        )
        
        # Listed Building confidence
        field_confidences['listed_building'] = await self._score_listed_building(
            extraction_results.get('listed_building', {}),
            spatial_results.get('listed_buildings', {}) if spatial_results else {},
            document_quality
        )
        
        # Flood Zone confidence
        field_confidences['flood_zone'] = await self._score_flood_zone(
            extraction_results.get('flood_zone', {}),
            spatial_results.get('flood_risk', {}) if spatial_results else {},
            document_quality
        )
        
        # Planning Applications confidence
        field_confidences['planning_applications'] = await self._score_planning_applications(
            extraction_results.get('planning_applications', {}),
            spatial_results.get('planning_applications', {}) if spatial_results else {},
            document_quality
        )
        
        # Highway Adoption confidence
        field_confidences['highway_adoption'] = await self._score_highway_adoption(
            extraction_results.get('highway_adoption', {}),
            spatial_results.get('road_adoption_status', {}) if spatial_results else {},
            document_quality
        )
        
        # Add other fields...
        remaining_fields = ['enforcement_notices', 'contaminated_land', 'tree_preservation_orders',
                           'building_regulations', 'utilities_sewers']
        
        for field in remaining_fields:
            field_confidences[field] = await self._score_generic_field(
                extraction_results.get(field, {}),
                spatial_results.get(field, {}) if spatial_results else {},
                document_quality,
                field
            )
            
        return field_confidences
        
    async def _score_conservation_area(self, extraction_data: Dict, 
                                     spatial_data: Dict, 
                                     doc_quality: Optional[Dict]) -> float:
        """Score conservation area extraction confidence"""
        
        base_confidence = extraction_data.get('confidence', 0.0)
        
        # Boost confidence if we have supporting evidence
        confidence_boosts = []
        
        # Text evidence quality
        evidence_text = extraction_data.get('evidence_text', [])
        if evidence_text:
            # Strong patterns boost confidence
            strong_patterns = ['conservation area', 'designated', 'CA reference']
            weak_patterns = ['may be', 'possibly', 'check']
            
            strong_matches = sum(1 for text in evidence_text 
                               for pattern in strong_patterns 
                               if pattern.lower() in text.lower())
            weak_matches = sum(1 for text in evidence_text 
                             for pattern in weak_patterns 
                             if pattern.lower() in text.lower())
            
            if strong_matches > weak_matches:
                confidence_boosts.append(0.15)
            elif weak_matches > 0:
                confidence_boosts.append(-0.10)  # Reduce confidence for uncertainty
                
        # Spatial validation boost
        spatial_confirmation = spatial_data.get('conservation_areas', [])
        extraction_present = extraction_data.get('present', False)
        
        if spatial_confirmation and extraction_present:
            confidence_boosts.append(0.20)  # Both sources agree - CA present
        elif not spatial_confirmation and not extraction_present:
            confidence_boosts.append(0.15)  # Both sources agree - no CA
        elif spatial_confirmation != extraction_present:
            confidence_boosts.append(-0.25)  # Sources disagree - needs review
            
        # Document quality impact
        if doc_quality:
            ocr_quality = doc_quality.get('ocr_quality', 0.5)
            if ocr_quality < 0.7:
                confidence_boosts.append(-0.10)
            elif ocr_quality > 0.9:
                confidence_boosts.append(0.05)
                
        # Historical accuracy calibration
        historical = self.historical_accuracy.get('conservation_area', {})
        if historical:
            accuracy_factor = historical['accuracy']
            base_confidence *= accuracy_factor
            
        # Apply boosts and clamp to [0, 1]
        final_confidence = base_confidence + sum(confidence_boosts)
        return max(0.0, min(1.0, final_confidence))
        
    async def _score_flood_zone(self, extraction_data: Dict,
                              spatial_data: Dict,
                              doc_quality: Optional[Dict]) -> float:
        """Score flood zone extraction with high accuracy requirements"""
        
        base_confidence = extraction_data.get('confidence', 0.0)
        confidence_boosts = []
        
        # Flood zone is critical - require high confidence
        extracted_zone = extraction_data.get('flood_zone')
        spatial_zone = spatial_data.get('flood_zone')
        
        if extracted_zone and spatial_zone:
            if extracted_zone == spatial_zone:
                confidence_boosts.append(0.25)  # Strong agreement
            else:
                confidence_boosts.append(-0.30)  # Disagreement - major issue
                
        # Environment Agency data is authoritative
        if spatial_data.get('data_source') == 'Environment Agency':
            if spatial_zone:
                confidence_boosts.append(0.20)  # EA data available
                
        # Risk level consistency check
        extracted_risk = extraction_data.get('risk_level', '').lower()
        spatial_risk = spatial_data.get('flood_risk_level', '').lower()
        
        if extracted_risk and spatial_risk and extracted_risk == spatial_risk:
            confidence_boosts.append(0.15)
            
        # Apply historical calibration
        historical = self.historical_accuracy.get('flood_zone', {})
        if historical:
            base_confidence *= historical['accuracy']
            
        final_confidence = base_confidence + sum(confidence_boosts)
        return max(0.0, min(1.0, final_confidence))
        
    async def _score_planning_applications(self, extraction_data: Dict,
                                         spatial_data: Dict,
                                         doc_quality: Optional[Dict]) -> float:
        """Score planning applications extraction"""
        
        base_confidence = extraction_data.get('confidence', 0.0)
        confidence_boosts = []
        
        # Check application reference format validity
        applications = extraction_data.get('applications', [])
        valid_refs = 0
        total_refs = len(applications)
        
        for app in applications:
            ref = app.get('reference', '')
            # Valid UK planning reference patterns
            if re.match(r'\d{2}/\d{4}/\d{4,6}/[A-Z]{2,4}', ref):
                valid_refs += 1
                
        if total_refs > 0:
            ref_validity_score = valid_refs / total_refs
            confidence_boosts.append(ref_validity_score * 0.20)
            
        # Spatial data cross-validation
        spatial_apps = spatial_data.get('applications', [])
        if spatial_apps and applications:
            # Check for reference overlap
            extracted_refs = {app.get('reference') for app in applications}
            spatial_refs = {app.get('reference') for app in spatial_apps}
            
            overlap = len(extracted_refs & spatial_refs)
            if overlap > 0:
                confidence_boosts.append(0.15)
                
        # Date consistency checks
        recent_apps = [app for app in applications 
                      if self._is_recent_application(app.get('decision_date'))]
        
        if len(recent_apps) == len(applications):
            confidence_boosts.append(0.10)  # All applications are recent
            
        final_confidence = base_confidence + sum(confidence_boosts)
        return max(0.0, min(1.0, final_confidence))
        
    async def _score_generic_field(self, extraction_data: Dict,
                                 spatial_data: Dict,
                                 doc_quality: Optional[Dict],
                                 field_name: str) -> float:
        """Generic confidence scoring for other fields"""
        
        base_confidence = extraction_data.get('confidence', 0.0)
        
        # Apply historical accuracy if available
        historical = self.historical_accuracy.get(field_name, {})
        if historical:
            base_confidence *= historical['accuracy']
        else:
            base_confidence *= 0.80  # Conservative factor for unknown fields
            
        # Document quality impact
        if doc_quality:
            quality_factor = doc_quality.get('overall_quality', 0.8)
            base_confidence *= quality_factor
            
        return max(0.0, min(1.0, base_confidence))
        
    def _calculate_overall_confidence(self, field_confidences: Dict[str, float]) -> float:
        """Calculate weighted overall confidence score"""
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for field, confidence in field_confidences.items():
            weight = self.field_weights.get(field, 0.02)  # Default small weight
            weighted_sum += confidence * weight
            total_weight += weight
            
        if total_weight == 0:
            return 0.0
            
        return weighted_sum / total_weight
        
    def _assess_processing_quality(self, document_quality: Dict) -> float:
        """Assess the quality of document processing"""
        
        quality_factors = []
        
        # OCR quality
        ocr_quality = document_quality.get('ocr_quality', 0.5)
        quality_factors.append(ocr_quality)
        
        # Image quality
        image_quality = document_quality.get('image_quality', 0.5)
        quality_factors.append(image_quality)
        
        # Layout detection quality
        layout_quality = document_quality.get('layout_quality', 0.5)
        quality_factors.append(layout_quality)
        
        # Text extraction completeness
        text_completeness = document_quality.get('text_completeness', 0.5)
        quality_factors.append(text_completeness)
        
        if not quality_factors:
            return 0.5  # Default moderate quality
            
        return sum(quality_factors) / len(quality_factors)
        
    def _calculate_completeness(self, extraction_results: Dict) -> float:
        """Calculate data completeness score"""
        
        required_fields = list(self.field_weights.keys())
        found_fields = 0
        
        for field in required_fields:
            field_data = extraction_results.get(field, {})
            
            # Check if field has meaningful data
            if field_data and (
                field_data.get('present') is not None or
                field_data.get('value') is not None or
                field_data.get('applications') or
                field_data.get('flood_zone')
            ):
                found_fields += 1
                
        return found_fields / len(required_fields) if required_fields else 0.0
        
    async def _cross_validate_spatial(self, extraction_results: Dict,
                                    spatial_results: Optional[Dict]) -> float:
        """Cross-validate extraction results with spatial analysis"""
        
        if not spatial_results:
            return 0.5  # No spatial data for validation
            
        validation_scores = []
        
        # Validate key fields with spatial data
        validation_pairs = [
            ('conservation_area', 'conservation_constraints'),
            ('flood_zone', 'flood_risk'),
            ('planning_applications', 'planning_applications'),
            ('highway_adoption', 'road_adoption_status')
        ]
        
        for extraction_field, spatial_field in validation_pairs:
            score = self._validate_field_pair(
                extraction_results.get(extraction_field, {}),
                spatial_results.get(spatial_field, {})
            )
            validation_scores.append(score)
            
        return sum(validation_scores) / len(validation_scores) if validation_scores else 0.0
        
    def _validate_field_pair(self, extraction_data: Dict, spatial_data: Dict) -> float:
        """Validate a single field between extraction and spatial analysis"""
        
        # Check for presence agreement
        extraction_present = extraction_data.get('present', False)
        spatial_present = len(spatial_data.get('results', [])) > 0
        
        if extraction_present == spatial_present:
            return 0.8  # Agreement on presence/absence
        else:
            return 0.3  # Disagreement requires investigation
            
    def _requires_manual_review(self, overall_confidence: float,
                              field_confidences: Dict[str, float],
                              processing_quality: float) -> bool:
        """Determine if manual review is required"""
        
        # Overall confidence too low
        if overall_confidence < self.automation_thresholds[ConfidenceLevel.HIGH]:
            return True
            
        # Any critical field has low confidence
        critical_fields = ['conservation_area', 'listed_building', 'flood_zone', 'enforcement_notices']
        for field in critical_fields:
            if field_confidences.get(field, 0.0) < self.automation_thresholds[ConfidenceLevel.MEDIUM]:
                return True
                
        # Processing quality issues
        if processing_quality < 0.7:
            return True
            
        return False
        
    def _calculate_automation_rate(self, overall_confidence: float, 
                                 manual_review_required: bool) -> float:
        """Calculate achieved automation rate"""
        
        if manual_review_required:
            return 0.0  # No automation if manual review required
            
        # Map confidence to automation percentage
        if overall_confidence >= self.automation_thresholds[ConfidenceLevel.VERY_HIGH]:
            return 0.98  # 98% automation
        elif overall_confidence >= self.automation_thresholds[ConfidenceLevel.HIGH]:
            return 0.92  # 92% automation
        elif overall_confidence >= self.automation_thresholds[ConfidenceLevel.MEDIUM]:
            return 0.75  # 75% automation - needs review
        else:
            return 0.0   # No automation
            
    def _is_recent_application(self, date_str: Optional[str]) -> bool:
        """Check if planning application is recent (within 5 years)"""
        if not date_str:
            return False
            
        try:
            # Parse various date formats
            date_formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d.%m.%Y']
            
            for fmt in date_formats:
                try:
                    app_date = datetime.strptime(date_str, fmt)
                    years_ago = (datetime.now() - app_date).days / 365.25
                    return years_ago <= 5.0
                except ValueError:
                    continue
                    
        except Exception:
            pass
            
        return False


class AutomationQualityMonitor:
    """Monitor and track automation quality over time"""
    
    def __init__(self):
        self.quality_history = []
        self.accuracy_targets = {
            'overall_automation': 0.90,
            'critical_fields': 0.95,
            'processing_speed': 300  # seconds
        }
        
    async def record_processing_result(self, quality_metrics: QualityMetrics,
                                     processing_time: float,
                                     manual_corrections: Optional[Dict] = None):
        """Record processing results for quality monitoring"""
        
        record = {
            'timestamp': datetime.utcnow(),
            'overall_confidence': quality_metrics.overall_confidence,
            'automation_rate': quality_metrics.automation_rate,
            'processing_time': processing_time,
            'manual_review_required': quality_metrics.manual_review_required,
            'field_confidences': quality_metrics.field_confidences,
            'manual_corrections': manual_corrections or {}
        }
        
        self.quality_history.append(record)
        
        # Analyze trends
        await self._analyze_quality_trends()
        
    async def _analyze_quality_trends(self):
        """Analyze quality trends and suggest improvements"""
        
        if len(self.quality_history) < 10:
            return  # Need more data
            
        recent_records = self.quality_history[-100:]  # Last 100 records
        
        # Calculate average metrics
        avg_automation = sum(r['automation_rate'] for r in recent_records) / len(recent_records)
        avg_confidence = sum(r['overall_confidence'] for r in recent_records) / len(recent_records)
        manual_review_rate = sum(1 for r in recent_records if r['manual_review_required']) / len(recent_records)
        
        logger.info(f"Quality Metrics - Automation: {avg_automation:.2%}, "
                   f"Confidence: {avg_confidence:.2%}, "
                   f"Manual Review Rate: {manual_review_rate:.2%}")
        
        # Identify improvement areas
        if avg_automation < self.accuracy_targets['overall_automation']:
            await self._suggest_automation_improvements(recent_records)
            
    async def _suggest_automation_improvements(self, records: List[Dict]):
        """Suggest improvements based on quality analysis"""
        
        # Identify fields with frequent low confidence
        field_issues = {}
        for record in records:
            for field, confidence in record['field_confidences'].items():
                if confidence < 0.80:
                    field_issues[field] = field_issues.get(field, 0) + 1
                    
        # Log improvement suggestions
        for field, issue_count in sorted(field_issues.items(), key=lambda x: x[1], reverse=True):
            if issue_count > len(records) * 0.2:  # >20% of cases
                logger.warning(f"Field '{field}' has confidence issues in {issue_count}/{len(records)} cases")
                
import re  # Add this import for regex operations
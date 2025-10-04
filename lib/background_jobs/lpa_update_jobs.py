"""
Background Jobs for LPA Data Updates
Handles periodic updates to LPA data, appeals, objections, and planning information
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import os
import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
import sqlite3

from celery import current_task
from ..background_jobs.job_scheduler import celery_app, DomusTask
from ..background_jobs.alert_system import AlertSystem, AlertLevel, AlertChannel
from ..lpa.data_updater import LPADataUpdater
from ..lpa.appeals_processor import AppealsProcessor
from ..lpa.constraints_updater import ConstraintsUpdater
from ..database import get_db_connection

# Initialize services
lpa_data_updater = LPADataUpdater()
appeals_processor = AppealsProcessor()
constraints_updater = ConstraintsUpdater()
alert_system = AlertSystem()

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.lpa_update_jobs.update_all_lpa_data')
def update_all_lpa_data(self, priority_lpas: List[str] = None):
    """
    Update data for all LPAs or priority LPAs
    
    Args:
        priority_lpas: List of LPA codes to prioritize, if None updates all
    """
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting comprehensive LPA data update (task_id: {task_id})")
        
        # Initialize update statistics
        update_stats = {
            'started_at': datetime.utcnow().isoformat(),
            'lpas_processed': 0,
            'lpas_updated': 0,
            'lpas_failed': 0,
            'applications_updated': 0,
            'constraints_updated': 0,
            'policies_updated': 0,
            'errors': []
        }
        
        # Get LPA list
        if priority_lpas:
            lpa_list = priority_lpas
        else:
            lpa_list = _get_all_lpa_codes()
        
        total_lpas = len(lpa_list)
        logger.info(f"Updating {total_lpas} LPAs")
        
        # Process each LPA
        for i, lpa_code in enumerate(lpa_list):
            try:
                # Update progress
                progress = (i / total_lpas) * 90
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'step': f'processing_lpa_{lpa_code}',
                        'progress': progress,
                        'current_lpa': lpa_code,
                        'processed': i,
                        'total': total_lpas
                    }
                )
                
                logger.info(f"Processing LPA: {lpa_code} ({i+1}/{total_lpas})")
                
                # Update individual LPA
                lpa_result = _update_single_lpa(lpa_code)
                
                update_stats['lpas_processed'] += 1
                
                if lpa_result['success']:
                    update_stats['lpas_updated'] += 1
                    update_stats['applications_updated'] += lpa_result.get('applications_updated', 0)
                    update_stats['constraints_updated'] += lpa_result.get('constraints_updated', 0)
                    update_stats['policies_updated'] += lpa_result.get('policies_updated', 0)
                else:
                    update_stats['lpas_failed'] += 1
                    update_stats['errors'].append(f"LPA {lpa_code}: {lpa_result.get('error', 'Unknown error')}")
                
            except Exception as e:
                update_stats['lpas_failed'] += 1
                error_msg = f"Failed to process LPA {lpa_code}: {e}"
                update_stats['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Final statistics
        self.update_state(state='PROGRESS', meta={'step': 'finalizing', 'progress': 95})
        
        update_stats['completed_at'] = datetime.utcnow().isoformat()
        update_stats['duration_seconds'] = (
            datetime.fromisoformat(update_stats['completed_at']) -
            datetime.fromisoformat(update_stats['started_at'])
        ).total_seconds()
        
        # Update global freshness tracking
        _update_lpa_global_freshness()
        
        # Send notification
        if update_stats['lpas_failed'] > 0:
            alert_level = AlertLevel.WARNING
            title = "⚠️ LPA Data Update Completed with Issues"
            message = f"Updated {update_stats['lpas_updated']}/{total_lpas} LPAs successfully, {update_stats['lpas_failed']} failed"
        else:
            alert_level = AlertLevel.INFO
            title = "✅ LPA Data Update Completed"
            message = f"Successfully updated all {update_stats['lpas_updated']} LPAs"
        
        alert_system.send_alert(
            title=title,
            message=message,
            level=alert_level,
            channels=[AlertChannel.SLACK],
            metadata=update_stats,
            throttle_key="lpa_update_complete"
        )
        
        logger.info(f"LPA data update completed: {update_stats}")
        
        return update_stats
        
    except Exception as e:
        error_msg = f"LPA data update failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title="❌ LPA Data Update Failed",
            message=error_msg,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id, 'error': str(e)}
        )
        
        raise

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.lpa_update_jobs.ingest_appeals_objections')
def ingest_appeals_objections(self, days_back: int = 7):
    """
    Ingest appeals and objections data from Planning Inspectorate
    
    Args:
        days_back: Number of days back to fetch data for
    """
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting appeals and objections ingestion (task_id: {task_id})")
        
        ingestion_stats = {
            'started_at': datetime.utcnow().isoformat(),
            'appeals_processed': 0,
            'appeals_new': 0,
            'appeals_updated': 0,
            'objections_processed': 0,
            'objections_new': 0,
            'objections_updated': 0,
            'errors': []
        }
        
        # Step 1: Fetch appeals data
        self.update_state(state='PROGRESS', meta={'step': 'fetching_appeals', 'progress': 20})
        
        appeals_data = _fetch_appeals_data(days_back)
        logger.info(f"Fetched {len(appeals_data)} appeals records")
        
        # Step 2: Process appeals
        self.update_state(state='PROGRESS', meta={'step': 'processing_appeals', 'progress': 40})
        
        for i, appeal in enumerate(appeals_data):
            try:
                result = appeals_processor.process_appeal(appeal)
                
                ingestion_stats['appeals_processed'] += 1
                if result['action'] == 'created':
                    ingestion_stats['appeals_new'] += 1
                elif result['action'] == 'updated':
                    ingestion_stats['appeals_updated'] += 1
                
                # Update progress
                if i % 10 == 0:  # Update every 10 appeals
                    progress = 40 + (i / len(appeals_data)) * 20
                    self.update_state(
                        state='PROGRESS',
                        meta={'step': 'processing_appeals', 'progress': progress}
                    )
                
            except Exception as e:
                error_msg = f"Failed to process appeal {appeal.get('case_reference', 'unknown')}: {e}"
                ingestion_stats['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Step 3: Fetch objections data
        self.update_state(state='PROGRESS', meta={'step': 'fetching_objections', 'progress': 60})
        
        objections_data = _fetch_objections_data(days_back)
        logger.info(f"Fetched {len(objections_data)} objections records")
        
        # Step 4: Process objections
        self.update_state(state='PROGRESS', meta={'step': 'processing_objections', 'progress': 80})
        
        for i, objection in enumerate(objections_data):
            try:
                result = appeals_processor.process_objection(objection)
                
                ingestion_stats['objections_processed'] += 1
                if result['action'] == 'created':
                    ingestion_stats['objections_new'] += 1
                elif result['action'] == 'updated':
                    ingestion_stats['objections_updated'] += 1
                
            except Exception as e:
                error_msg = f"Failed to process objection {objection.get('reference', 'unknown')}: {e}"
                ingestion_stats['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Finalize
        self.update_state(state='PROGRESS', meta={'step': 'finalizing', 'progress': 95})
        
        ingestion_stats['completed_at'] = datetime.utcnow().isoformat()
        
        # Update appeals freshness tracking
        _update_appeals_freshness()
        
        # Send notification
        alert_system.send_alert(
            title="📋 Appeals & Objections Ingestion Complete",
            message=f"Processed {ingestion_stats['appeals_processed']} appeals and {ingestion_stats['objections_processed']} objections",
            level=AlertLevel.INFO,
            channels=[AlertChannel.SLACK],
            metadata=ingestion_stats,
            throttle_key="appeals_ingestion_complete"
        )
        
        logger.info(f"Appeals and objections ingestion completed: {ingestion_stats}")
        
        return ingestion_stats
        
    except Exception as e:
        error_msg = f"Appeals and objections ingestion failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title="❌ Appeals & Objections Ingestion Failed",
            message=error_msg,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id}
        )
        
        raise

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.lpa_update_jobs.update_planning_constraints')
def update_planning_constraints(self, constraint_types: List[str] = None):
    """
    Update planning constraints data
    
    Args:
        constraint_types: List of constraint types to update, if None updates all
    """
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting planning constraints update (task_id: {task_id})")
        
        # Default constraint types
        if constraint_types is None:
            constraint_types = [
                'conservation_areas',
                'listed_buildings',
                'tree_preservation_orders',
                'flood_zones',
                'green_belt',
                'archaeological_sites',
                'sssi',  # Sites of Special Scientific Interest
                'national_parks',
                'aonb'   # Areas of Outstanding Natural Beauty
            ]
        
        constraints_stats = {
            'started_at': datetime.utcnow().isoformat(),
            'constraint_types_processed': 0,
            'total_records_updated': 0,
            'records_by_type': {},
            'errors': []
        }
        
        total_types = len(constraint_types)
        
        # Process each constraint type
        for i, constraint_type in enumerate(constraint_types):
            try:
                # Update progress
                progress = (i / total_types) * 90
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'step': f'updating_{constraint_type}',
                        'progress': progress,
                        'current_type': constraint_type,
                        'processed': i,
                        'total': total_types
                    }
                )
                
                logger.info(f"Updating constraint type: {constraint_type}")
                
                # Update specific constraint type
                result = constraints_updater.update_constraint_type(constraint_type)
                
                constraints_stats['constraint_types_processed'] += 1
                constraints_stats['total_records_updated'] += result.get('records_updated', 0)
                constraints_stats['records_by_type'][constraint_type] = result.get('records_updated', 0)
                
                if result.get('errors'):
                    constraints_stats['errors'].extend(result['errors'])
                
            except Exception as e:
                error_msg = f"Failed to update constraint type {constraint_type}: {e}"
                constraints_stats['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Finalize
        self.update_state(state='PROGRESS', meta={'step': 'finalizing', 'progress': 95})
        
        constraints_stats['completed_at'] = datetime.utcnow().isoformat()
        
        # Update constraints freshness tracking
        _update_constraints_freshness()
        
        # Send notification
        alert_level = AlertLevel.WARNING if constraints_stats['errors'] else AlertLevel.INFO
        title = "🗺️ Planning Constraints Update Complete"
        message = f"Updated {constraints_stats['total_records_updated']} constraint records across {constraints_stats['constraint_types_processed']} types"
        
        alert_system.send_alert(
            title=title,
            message=message,
            level=alert_level,
            channels=[AlertChannel.SLACK],
            metadata=constraints_stats,
            throttle_key="constraints_update_complete"
        )
        
        logger.info(f"Planning constraints update completed: {constraints_stats}")
        
        return constraints_stats
        
    except Exception as e:
        error_msg = f"Planning constraints update failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title="❌ Planning Constraints Update Failed",
            message=error_msg,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id}
        )
        
        raise

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.lpa_update_jobs.sync_hdt_5yhls_data')
def sync_hdt_5yhls_data(self):
    """
    Sync Housing Delivery Test (HDT) and 5-Year Housing Land Supply (5YHLS) data
    """
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting HDT and 5YHLS data sync (task_id: {task_id})")
        
        sync_stats = {
            'started_at': datetime.utcnow().isoformat(),
            'hdt_records_updated': 0,
            'yhls_records_updated': 0,
            'lpas_updated': 0,
            'errors': []
        }
        
        # Step 1: Fetch HDT data
        self.update_state(state='PROGRESS', meta={'step': 'fetching_hdt_data', 'progress': 20})
        
        hdt_data = _fetch_hdt_data()
        logger.info(f"Fetched HDT data for {len(hdt_data)} LPAs")
        
        # Step 2: Fetch 5YHLS data
        self.update_state(state='PROGRESS', meta={'step': 'fetching_5yhls_data', 'progress': 40})
        
        yhls_data = _fetch_5yhls_data()
        logger.info(f"Fetched 5YHLS data for {len(yhls_data)} LPAs")
        
        # Step 3: Process and update data
        self.update_state(state='PROGRESS', meta={'step': 'updating_records', 'progress': 60})
        
        # Get all unique LPAs from both datasets
        all_lpas = set(hdt_data.keys()) | set(yhls_data.keys())
        
        for i, lpa_code in enumerate(all_lpas):
            try:
                # Update HDT data if available
                if lpa_code in hdt_data:
                    _update_lpa_hdt_data(lpa_code, hdt_data[lpa_code])
                    sync_stats['hdt_records_updated'] += 1
                
                # Update 5YHLS data if available
                if lpa_code in yhls_data:
                    _update_lpa_5yhls_data(lpa_code, yhls_data[lpa_code])
                    sync_stats['yhls_records_updated'] += 1
                
                sync_stats['lpas_updated'] += 1
                
                # Update progress
                if i % 10 == 0:
                    progress = 60 + (i / len(all_lpas)) * 30
                    self.update_state(
                        state='PROGRESS',
                        meta={'step': 'updating_records', 'progress': progress}
                    )
                
            except Exception as e:
                error_msg = f"Failed to update HDT/5YHLS data for LPA {lpa_code}: {e}"
                sync_stats['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Finalize
        sync_stats['completed_at'] = datetime.utcnow().isoformat()
        
        # Update HDT/5YHLS freshness tracking
        _update_hdt_5yhls_freshness()
        
        # Send notification
        alert_system.send_alert(
            title="🏠 HDT & 5YHLS Data Sync Complete",
            message=f"Updated HDT data for {sync_stats['hdt_records_updated']} LPAs and 5YHLS data for {sync_stats['yhls_records_updated']} LPAs",
            level=AlertLevel.INFO,
            channels=[AlertChannel.SLACK],
            metadata=sync_stats,
            throttle_key="hdt_5yhls_sync_complete"
        )
        
        logger.info(f"HDT and 5YHLS data sync completed: {sync_stats}")
        
        return sync_stats
        
    except Exception as e:
        error_msg = f"HDT and 5YHLS data sync failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title="❌ HDT & 5YHLS Data Sync Failed",
            message=error_msg,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id}
        )
        
        raise

# Helper functions

def _get_all_lpa_codes() -> List[str]:
    """Get list of all LPA codes from database"""
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT DISTINCT lpa_code FROM lpas WHERE active = 1")
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logging.error(f"Error getting LPA codes: {e}")
        return []

def _update_single_lpa(lpa_code: str) -> Dict[str, Any]:
    """Update data for a single LPA"""
    try:
        result = {
            'success': False,
            'applications_updated': 0,
            'constraints_updated': 0,
            'policies_updated': 0,
            'error': None
        }
        
        # Update planning applications
        apps_result = lpa_data_updater.update_planning_applications(lpa_code)
        result['applications_updated'] = apps_result.get('updated_count', 0)
        
        # Update local policies
        policies_result = lpa_data_updater.update_local_policies(lpa_code)
        result['policies_updated'] = policies_result.get('updated_count', 0)
        
        # Update LPA information
        info_result = lpa_data_updater.update_lpa_information(lpa_code)
        
        # Mark as successful if no major errors
        result['success'] = True
        
        # Update LPA freshness tracking
        _update_individual_lpa_freshness(lpa_code)
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'applications_updated': 0,
            'constraints_updated': 0,
            'policies_updated': 0,
            'error': str(e)
        }

def _fetch_appeals_data(days_back: int) -> List[Dict[str, Any]]:
    """Fetch appeals data from Planning Inspectorate"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        # API endpoint for appeals data
        api_url = "https://acp.planninginspectorate.gov.uk/api/appeals"
        
        params = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'format': 'json',
            'limit': 1000
        }
        
        response = requests.get(api_url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        return data.get('appeals', [])
        
    except Exception as e:
        logging.error(f"Error fetching appeals data: {e}")
        return []

def _fetch_objections_data(days_back: int) -> List[Dict[str, Any]]:
    """Fetch objections data from various sources"""
    try:
        # This would fetch objections from multiple sources
        # For now, return empty list
        return []
        
    except Exception as e:
        logging.error(f"Error fetching objections data: {e}")
        return []

def _fetch_hdt_data() -> Dict[str, Dict[str, Any]]:
    """Fetch Housing Delivery Test data"""
    try:
        # Government HDT data endpoint
        api_url = "https://www.gov.uk/api/housing-delivery-test"
        
        response = requests.get(api_url, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        # Convert to LPA-keyed dictionary
        hdt_data = {}
        for record in data.get('authorities', []):
            lpa_code = record.get('lpa_code')
            if lpa_code:
                hdt_data[lpa_code] = {
                    'measurement_year': record.get('measurement_year'),
                    'delivery_percentage': record.get('delivery_percentage'),
                    'homes_required': record.get('homes_required'),
                    'homes_delivered': record.get('homes_delivered'),
                    'action_plan_required': record.get('action_plan_required', False),
                    'presumption_applies': record.get('presumption_applies', False)
                }
        
        return hdt_data
        
    except Exception as e:
        logging.error(f"Error fetching HDT data: {e}")
        return {}

def _fetch_5yhls_data() -> Dict[str, Dict[str, Any]]:
    """Fetch 5-Year Housing Land Supply data"""
    try:
        # This would fetch from multiple LPA sources
        # For now, return empty dict
        return {}
        
    except Exception as e:
        logging.error(f"Error fetching 5YHLS data: {e}")
        return {}

def _update_lpa_hdt_data(lpa_code: str, hdt_data: Dict[str, Any]):
    """Update HDT data for specific LPA"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO lpa_hdt_data 
                (lpa_code, measurement_year, delivery_percentage, homes_required, 
                 homes_delivered, action_plan_required, presumption_applies, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lpa_code,
                hdt_data.get('measurement_year'),
                hdt_data.get('delivery_percentage'),
                hdt_data.get('homes_required'),
                hdt_data.get('homes_delivered'),
                hdt_data.get('action_plan_required', False),
                hdt_data.get('presumption_applies', False),
                datetime.utcnow()
            ))
            conn.commit()
    except Exception as e:
        logging.error(f"Error updating HDT data for {lpa_code}: {e}")

def _update_lpa_5yhls_data(lpa_code: str, yhls_data: Dict[str, Any]):
    """Update 5YHLS data for specific LPA"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO lpa_5yhls_data 
                (lpa_code, assessment_date, supply_years, deliverable_homes, 
                 annual_requirement, supply_buffer, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                lpa_code,
                yhls_data.get('assessment_date'),
                yhls_data.get('supply_years'),
                yhls_data.get('deliverable_homes'),
                yhls_data.get('annual_requirement'),
                yhls_data.get('supply_buffer'),
                datetime.utcnow()
            ))
            conn.commit()
    except Exception as e:
        logging.error(f"Error updating 5YHLS data for {lpa_code}: {e}")

# Freshness tracking functions

def _update_lpa_global_freshness():
    """Update global LPA data freshness"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO knowledge_freshness 
                (type, last_updated, status)
                VALUES ('lpa_data', ?, 'fresh')
            """, (datetime.utcnow(),))
            conn.commit()
    except Exception as e:
        logging.error(f"Error updating LPA global freshness: {e}")

def _update_individual_lpa_freshness(lpa_code: str):
    """Update freshness tracking for individual LPA"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO lpa_freshness 
                (lpa_code, last_updated, status)
                VALUES (?, ?, 'fresh')
            """, (lpa_code, datetime.utcnow()))
            conn.commit()
    except Exception as e:
        logging.error(f"Error updating freshness for LPA {lpa_code}: {e}")

def _update_appeals_freshness():
    """Update appeals data freshness"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO knowledge_freshness 
                (type, last_updated, status)
                VALUES ('appeals_data', ?, 'fresh')
            """, (datetime.utcnow(),))
            conn.commit()
    except Exception as e:
        logging.error(f"Error updating appeals freshness: {e}")

def _update_constraints_freshness():
    """Update constraints data freshness"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO knowledge_freshness 
                (type, last_updated, status)
                VALUES ('constraints_data', ?, 'fresh')
            """, (datetime.utcnow(),))
            conn.commit()
    except Exception as e:
        logging.error(f"Error updating constraints freshness: {e}")

def _update_hdt_5yhls_freshness():
    """Update HDT and 5YHLS data freshness"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO knowledge_freshness 
                (type, last_updated, status)
                VALUES ('hdt_5yhls_data', ?, 'fresh')
            """, (datetime.utcnow(),))
            conn.commit()
    except Exception as e:
        logging.error(f"Error updating HDT/5YHLS freshness: {e}")
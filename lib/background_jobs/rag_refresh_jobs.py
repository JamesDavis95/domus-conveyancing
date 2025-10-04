"""
Background Jobs for RAG Knowledge Base Refresh
Handles periodic updates to the RAG knowledge base with latest planning data
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os
import json
import requests
from pathlib import Path

from celery import current_task
from ..background_jobs.job_scheduler import celery_app, DomusTask
from ..background_jobs.alert_system import AlertSystem, AlertLevel, AlertChannel
from ..rag.knowledge_refresh import KnowledgeRefreshService
from ..rag.document_processor import DocumentProcessor
from ..rag.embeddings_manager import EmbeddingsManager
from ..database import get_db_connection

# Initialize services
knowledge_refresh_service = KnowledgeRefreshService()
document_processor = DocumentProcessor()
embeddings_manager = EmbeddingsManager()
alert_system = AlertSystem()

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.rag_refresh_jobs.refresh_knowledge_base')
def refresh_knowledge_base(self, incremental: bool = True, force_full: bool = False):
    """
    Main task to refresh the RAG knowledge base
    
    Args:
        incremental: If True, only update changed documents
        force_full: If True, force a complete rebuild
    """
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting knowledge base refresh (task_id: {task_id})")
        
        # Set task progress
        self.update_state(state='PROGRESS', meta={'step': 'initializing', 'progress': 0})
        
        # Check if force full refresh is needed
        if force_full or _should_do_full_refresh():
            incremental = False
            logger.info("Performing full knowledge base refresh")
        
        # Initialize refresh service
        refresh_stats = {
            'started_at': datetime.utcnow().isoformat(),
            'incremental': incremental,
            'documents_processed': 0,
            'documents_updated': 0,
            'documents_added': 0,
            'documents_removed': 0,
            'embeddings_updated': 0,
            'errors': []
        }
        
        # Step 1: Fetch latest planning data
        self.update_state(state='PROGRESS', meta={'step': 'fetching_data', 'progress': 10})
        
        planning_data = _fetch_latest_planning_data()
        refresh_stats['planning_data_fetched'] = len(planning_data)
        
        # Step 2: Process documents
        self.update_state(state='PROGRESS', meta={'step': 'processing_documents', 'progress': 30})
        
        processed_docs = []
        for i, data_source in enumerate(planning_data):
            try:
                docs = document_processor.process_planning_data(data_source)
                processed_docs.extend(docs)
                refresh_stats['documents_processed'] += len(docs)
                
                # Update progress
                progress = 30 + (i / len(planning_data)) * 40
                self.update_state(
                    state='PROGRESS',
                    meta={'step': 'processing_documents', 'progress': progress}
                )
                
            except Exception as e:
                error_msg = f"Failed to process data source {data_source.get('name', 'unknown')}: {e}"
                refresh_stats['errors'].append(error_msg)
                logger.error(error_msg)
        
        # Step 3: Update knowledge base
        self.update_state(state='PROGRESS', meta={'step': 'updating_knowledge_base', 'progress': 70})
        
        if incremental:
            update_stats = knowledge_refresh_service.incremental_update(processed_docs)
        else:
            update_stats = knowledge_refresh_service.full_refresh(processed_docs)
        
        refresh_stats.update(update_stats)
        
        # Step 4: Update embeddings
        self.update_state(state='PROGRESS', meta={'step': 'updating_embeddings', 'progress': 85})
        
        embeddings_stats = _update_embeddings(processed_docs, incremental)
        refresh_stats.update(embeddings_stats)
        
        # Step 5: Cleanup and finalization
        self.update_state(state='PROGRESS', meta={'step': 'finalizing', 'progress': 95})
        
        # Clean up old embeddings if full refresh
        if not incremental:
            embeddings_manager.cleanup_orphaned_embeddings()
        
        # Update freshness tracking
        _update_knowledge_freshness()
        
        # Final statistics
        refresh_stats['completed_at'] = datetime.utcnow().isoformat()
        refresh_stats['duration_seconds'] = (
            datetime.fromisoformat(refresh_stats['completed_at']) -
            datetime.fromisoformat(refresh_stats['started_at'])
        ).total_seconds()
        
        # Send success notification
        alert_system.send_alert(
            title="✅ Knowledge Base Refresh Completed",
            message=f"Successfully updated {refresh_stats['documents_updated']} documents with {refresh_stats['embeddings_updated']} embedding updates",
            level=AlertLevel.INFO,
            channels=[AlertChannel.SLACK],
            metadata=refresh_stats,
            throttle_key="rag_refresh_success"
        )
        
        logger.info(f"Knowledge base refresh completed successfully: {refresh_stats}")
        
        return refresh_stats
        
    except Exception as e:
        error_msg = f"Knowledge base refresh failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        # Send failure alert
        alert_system.send_alert(
            title="❌ Knowledge Base Refresh Failed",
            message=error_msg,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id, 'error': str(e)}
        )
        
        raise

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.rag_refresh_jobs.update_specific_lpa')
def update_specific_lpa(self, lpa_code: str, force_refresh: bool = False):
    """
    Update knowledge base for a specific LPA
    
    Args:
        lpa_code: LPA code to update
        force_refresh: Force refresh even if data is recent
    """
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting LPA-specific refresh for {lpa_code} (task_id: {task_id})")
        
        # Fetch LPA-specific data
        self.update_state(state='PROGRESS', meta={'step': 'fetching_lpa_data', 'progress': 20})
        
        lpa_data = _fetch_lpa_specific_data(lpa_code, force_refresh)
        
        if not lpa_data:
            logger.info(f"No new data for LPA {lpa_code}")
            return {'lpa_code': lpa_code, 'status': 'no_update_needed'}
        
        # Process documents
        self.update_state(state='PROGRESS', meta={'step': 'processing_documents', 'progress': 50})
        
        processed_docs = document_processor.process_lpa_data(lpa_data)
        
        # Update knowledge base
        self.update_state(state='PROGRESS', meta={'step': 'updating_knowledge_base', 'progress': 80})
        
        update_stats = knowledge_refresh_service.update_lpa_knowledge(lpa_code, processed_docs)
        
        # Update embeddings
        embeddings_stats = _update_embeddings(processed_docs, incremental=True)
        update_stats.update(embeddings_stats)
        
        # Update LPA freshness tracking
        _update_lpa_freshness(lpa_code)
        
        logger.info(f"LPA {lpa_code} refresh completed: {update_stats}")
        
        return {
            'lpa_code': lpa_code,
            'status': 'success',
            **update_stats
        }
        
    except Exception as e:
        error_msg = f"LPA {lpa_code} refresh failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title=f"❌ LPA Refresh Failed: {lpa_code}",
            message=error_msg,
            level=AlertLevel.WARNING,
            channels=[AlertChannel.SLACK],
            metadata={'lpa_code': lpa_code, 'task_id': task_id}
        )
        
        raise

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.rag_refresh_jobs.rebuild_embeddings')
def rebuild_embeddings(self, batch_size: int = 100):
    """
    Rebuild all embeddings from scratch
    
    Args:
        batch_size: Number of documents to process in each batch
    """
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting embeddings rebuild (task_id: {task_id})")
        
        # Get all documents from knowledge base
        self.update_state(state='PROGRESS', meta={'step': 'fetching_documents', 'progress': 10})
        
        all_documents = knowledge_refresh_service.get_all_documents()
        total_docs = len(all_documents)
        
        if total_docs == 0:
            logger.warning("No documents found for embeddings rebuild")
            return {'status': 'no_documents', 'total_documents': 0}
        
        # Clear existing embeddings
        self.update_state(state='PROGRESS', meta={'step': 'clearing_embeddings', 'progress': 20})
        embeddings_manager.clear_all_embeddings()
        
        # Process documents in batches
        processed_count = 0
        
        for i in range(0, total_docs, batch_size):
            batch = all_documents[i:i + batch_size]
            
            # Update progress
            progress = 20 + (processed_count / total_docs) * 70
            self.update_state(
                state='PROGRESS',
                meta={
                    'step': 'rebuilding_embeddings',
                    'progress': progress,
                    'processed': processed_count,
                    'total': total_docs
                }
            )
            
            # Generate embeddings for batch
            embeddings_manager.generate_embeddings_batch(batch)
            processed_count += len(batch)
            
            logger.info(f"Processed {processed_count}/{total_docs} documents")
        
        # Finalize
        self.update_state(state='PROGRESS', meta={'step': 'finalizing', 'progress': 95})
        
        # Update tracking
        _update_embeddings_freshness()
        
        stats = {
            'status': 'success',
            'total_documents': total_docs,
            'embeddings_generated': processed_count,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        alert_system.send_alert(
            title="✅ Embeddings Rebuild Completed",
            message=f"Successfully rebuilt embeddings for {processed_count} documents",
            level=AlertLevel.INFO,
            channels=[AlertChannel.SLACK],
            metadata=stats
        )
        
        logger.info(f"Embeddings rebuild completed: {stats}")
        
        return stats
        
    except Exception as e:
        error_msg = f"Embeddings rebuild failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title="❌ Embeddings Rebuild Failed",
            message=error_msg,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id}
        )
        
        raise

@celery_app.task(bind=True, base=DomusTask, name='lib.background_jobs.rag_refresh_jobs.validate_knowledge_integrity')
def validate_knowledge_integrity(self):
    """Validate knowledge base integrity and consistency"""
    task_id = self.request.id
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting knowledge base integrity validation (task_id: {task_id})")
        
        validation_results = {
            'started_at': datetime.utcnow().isoformat(),
            'documents_checked': 0,
            'embeddings_checked': 0,
            'orphaned_embeddings': 0,
            'missing_embeddings': 0,
            'corrupted_documents': 0,
            'issues_found': []
        }
        
        # Step 1: Check document integrity
        self.update_state(state='PROGRESS', meta={'step': 'checking_documents', 'progress': 25})
        
        documents = knowledge_refresh_service.get_all_documents()
        validation_results['documents_checked'] = len(documents)
        
        for doc in documents:
            if not knowledge_refresh_service.validate_document(doc):
                validation_results['corrupted_documents'] += 1
                validation_results['issues_found'].append(f"Corrupted document: {doc.get('id', 'unknown')}")
        
        # Step 2: Check embeddings integrity
        self.update_state(state='PROGRESS', meta={'step': 'checking_embeddings', 'progress': 50})
        
        embeddings_stats = embeddings_manager.validate_embeddings()
        validation_results.update(embeddings_stats)
        
        # Step 3: Check cross-references
        self.update_state(state='PROGRESS', meta={'step': 'checking_references', 'progress': 75})
        
        ref_issues = knowledge_refresh_service.validate_cross_references()
        validation_results['reference_issues'] = len(ref_issues)
        validation_results['issues_found'].extend(ref_issues)
        
        # Step 4: Summary
        validation_results['completed_at'] = datetime.utcnow().isoformat()
        validation_results['status'] = 'healthy' if len(validation_results['issues_found']) == 0 else 'issues_found'
        
        # Send alert if issues found
        if validation_results['issues_found']:
            alert_system.send_alert(
                title="⚠️ Knowledge Base Integrity Issues",
                message=f"Found {len(validation_results['issues_found'])} integrity issues",
                level=AlertLevel.WARNING,
                channels=[AlertChannel.SLACK],
                metadata=validation_results
            )
        
        logger.info(f"Knowledge base validation completed: {validation_results}")
        
        return validation_results
        
    except Exception as e:
        error_msg = f"Knowledge base validation failed: {e}"
        logger.error(error_msg, exc_info=True)
        
        alert_system.send_alert(
            title="❌ Knowledge Base Validation Failed",
            message=error_msg,
            level=AlertLevel.ERROR,
            channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            metadata={'task_id': task_id}
        )
        
        raise

# Helper functions

def _should_do_full_refresh() -> bool:
    """Check if a full refresh is needed based on various criteria"""
    try:
        # Check last full refresh time
        last_full_refresh = knowledge_refresh_service.get_last_full_refresh()
        
        if not last_full_refresh:
            return True
        
        # Force full refresh if it's been more than 7 days
        if datetime.utcnow() - last_full_refresh > timedelta(days=7):
            return True
        
        # Check for schema changes
        if knowledge_refresh_service.has_schema_changes():
            return True
        
        # Check error rate from recent incremental updates
        error_rate = knowledge_refresh_service.get_recent_error_rate()
        if error_rate > 0.1:  # More than 10% error rate
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"Error checking full refresh criteria: {e}")
        return False

def _fetch_latest_planning_data() -> List[Dict[str, Any]]:
    """Fetch latest planning data from all configured sources"""
    try:
        data_sources = [
            {
                'name': 'gov_uk_planning',
                'url': 'https://www.gov.uk/api/planning-data',
                'type': 'api'
            },
            {
                'name': 'planning_inspectorate',
                'url': 'https://acp.planninginspectorate.gov.uk/api/appeals',
                'type': 'api'
            },
            {
                'name': 'local_authorities',
                'type': 'bulk',
                'sources': _get_lpa_data_sources()
            }
        ]
        
        planning_data = []
        
        for source in data_sources:
            try:
                if source['type'] == 'api':
                    data = _fetch_api_data(source)
                elif source['type'] == 'bulk':
                    data = _fetch_bulk_data(source)
                else:
                    continue
                
                if data:
                    planning_data.append({
                        'source': source['name'],
                        'data': data,
                        'fetched_at': datetime.utcnow().isoformat()
                    })
                
            except Exception as e:
                logging.error(f"Failed to fetch data from {source['name']}: {e}")
        
        return planning_data
        
    except Exception as e:
        logging.error(f"Error fetching latest planning data: {e}")
        return []

def _fetch_lpa_specific_data(lpa_code: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    """Fetch data for a specific LPA"""
    try:
        # Check if LPA data is recent enough
        if not force_refresh:
            last_update = knowledge_refresh_service.get_lpa_last_update(lpa_code)
            if last_update and datetime.utcnow() - last_update < timedelta(hours=6):
                return None
        
        # Fetch LPA-specific data from various sources
        lpa_data = {
            'lpa_code': lpa_code,
            'planning_applications': _fetch_lpa_planning_applications(lpa_code),
            'local_plan': _fetch_lpa_local_plan(lpa_code),
            'constraints': _fetch_lpa_constraints(lpa_code),
            'policies': _fetch_lpa_policies(lpa_code)
        }
        
        return lpa_data
        
    except Exception as e:
        logging.error(f"Error fetching LPA data for {lpa_code}: {e}")
        return None

def _update_embeddings(documents: List[Dict[str, Any]], incremental: bool = True) -> Dict[str, Any]:
    """Update embeddings for processed documents"""
    try:
        if incremental:
            stats = embeddings_manager.update_embeddings_incremental(documents)
        else:
            stats = embeddings_manager.regenerate_embeddings(documents)
        
        return {
            'embeddings_updated': stats.get('updated', 0),
            'embeddings_added': stats.get('added', 0),
            'embeddings_removed': stats.get('removed', 0),
            'embedding_errors': stats.get('errors', 0)
        }
        
    except Exception as e:
        logging.error(f"Error updating embeddings: {e}")
        return {'embedding_errors': 1}

def _update_knowledge_freshness():
    """Update knowledge base freshness tracking"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO knowledge_freshness 
                (type, last_updated, status)
                VALUES ('knowledge_base', ?, 'fresh')
            """, (datetime.utcnow(),))
            conn.commit()
    except Exception as e:
        logging.error(f"Error updating knowledge freshness: {e}")

def _update_lpa_freshness(lpa_code: str):
    """Update LPA-specific freshness tracking"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO lpa_freshness 
                (lpa_code, last_updated, status)
                VALUES (?, ?, 'fresh')
            """, (lpa_code, datetime.utcnow()))
            conn.commit()
    except Exception as e:
        logging.error(f"Error updating LPA freshness for {lpa_code}: {e}")

def _update_embeddings_freshness():
    """Update embeddings freshness tracking"""
    try:
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO knowledge_freshness 
                (type, last_updated, status)
                VALUES ('embeddings', ?, 'fresh')
            """, (datetime.utcnow(),))
            conn.commit()
    except Exception as e:
        logging.error(f"Error updating embeddings freshness: {e}")

def _get_lpa_data_sources() -> List[Dict[str, str]]:
    """Get list of LPA data sources"""
    # This would return actual LPA data sources
    return [
        {'name': 'Camden', 'code': 'CAM', 'api_url': 'https://camden.gov.uk/api/planning'},
        {'name': 'Westminster', 'code': 'WES', 'api_url': 'https://westminster.gov.uk/api/planning'},
        # ... more LPAs
    ]

def _fetch_api_data(source: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Fetch data from API source"""
    try:
        response = requests.get(source['url'], timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"Error fetching API data from {source['url']}: {e}")
        return None

def _fetch_bulk_data(source: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Fetch bulk data from multiple sources"""
    try:
        bulk_data = {}
        for sub_source in source.get('sources', []):
            data = _fetch_api_data(sub_source)
            if data:
                bulk_data[sub_source['name']] = data
        return bulk_data
    except Exception as e:
        logging.error(f"Error fetching bulk data: {e}")
        return None

def _fetch_lpa_planning_applications(lpa_code: str) -> List[Dict[str, Any]]:
    """Fetch planning applications for specific LPA"""
    # Implementation would fetch actual planning applications
    return []

def _fetch_lpa_local_plan(lpa_code: str) -> Dict[str, Any]:
    """Fetch local plan for specific LPA"""
    # Implementation would fetch actual local plan
    return {}

def _fetch_lpa_constraints(lpa_code: str) -> List[Dict[str, Any]]:
    """Fetch planning constraints for specific LPA"""
    # Implementation would fetch actual constraints
    return []

def _fetch_lpa_policies(lpa_code: str) -> List[Dict[str, Any]]:
    """Fetch planning policies for specific LPA"""
    # Implementation would fetch actual policies
    return []
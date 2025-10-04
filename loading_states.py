"""
Backend Loading State Management
Utilities and decorators for managing loading states in FastAPI endpoints
"""

from functools import wraps
from typing import Dict, Any, Optional, Callable
import asyncio
import time
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Global loading state tracker
_loading_states: Dict[str, Dict[str, Any]] = {}

class LoadingStateManager:
    """Manages loading states for API endpoints and operations"""
    
    def __init__(self):
        self.states = {}
        
    def start_operation(self, operation_id: str, operation_type: str = "general", metadata: Optional[Dict] = None):
        """Start tracking a loading operation"""
        self.states[operation_id] = {
            "status": "loading",
            "type": operation_type,
            "start_time": time.time(),
            "metadata": metadata or {},
            "progress": 0
        }
        logger.info(f"Started loading operation: {operation_id}")
        
    def update_progress(self, operation_id: str, progress: int, message: Optional[str] = None):
        """Update progress for an operation"""
        if operation_id in self.states:
            self.states[operation_id]["progress"] = progress
            if message:
                self.states[operation_id]["message"] = message
            logger.info(f"Updated progress for {operation_id}: {progress}%")
            
    def complete_operation(self, operation_id: str, result: Optional[Dict] = None):
        """Mark operation as completed"""
        if operation_id in self.states:
            self.states[operation_id].update({
                "status": "completed",
                "end_time": time.time(),
                "result": result
            })
            logger.info(f"Completed loading operation: {operation_id}")
            
    def fail_operation(self, operation_id: str, error: str):
        """Mark operation as failed"""
        if operation_id in self.states:
            self.states[operation_id].update({
                "status": "failed",
                "end_time": time.time(),
                "error": error
            })
            logger.error(f"Failed loading operation {operation_id}: {error}")
            
    def get_operation_status(self, operation_id: str) -> Optional[Dict]:
        """Get current status of an operation"""
        return self.states.get(operation_id)
        
    def cleanup_completed(self, max_age_seconds: int = 300):
        """Clean up completed operations older than max_age_seconds"""
        current_time = time.time()
        to_remove = []
        
        for op_id, state in self.states.items():
            if state.get("end_time") and (current_time - state["end_time"]) > max_age_seconds:
                to_remove.append(op_id)
                
        for op_id in to_remove:
            del self.states[op_id]
            
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} completed operations")

# Global loading state manager instance
loading_manager = LoadingStateManager()

def with_loading_state(operation_type: str = "general", auto_complete: bool = True):
    """
    Decorator to automatically manage loading states for API endpoints
    
    Args:
        operation_type: Type of operation for categorization
        auto_complete: Whether to automatically complete the operation on success
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import uuid
            operation_id = str(uuid.uuid4())
            
            # Extract metadata from request if available
            metadata = {}
            if args and hasattr(args[0], 'path_info'):
                metadata['endpoint'] = args[0].path_info
                
            loading_manager.start_operation(operation_id, operation_type, metadata)
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                    
                if auto_complete:
                    loading_manager.complete_operation(operation_id, {"success": True})
                    
                return result
                
            except Exception as e:
                loading_manager.fail_operation(operation_id, str(e))
                raise
                
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import uuid
            operation_id = str(uuid.uuid4())
            
            metadata = {}
            if args and hasattr(args[0], 'path_info'):
                metadata['endpoint'] = args[0].path_info
                
            loading_manager.start_operation(operation_id, operation_type, metadata)
            
            try:
                result = func(*args, **kwargs)
                if auto_complete:
                    loading_manager.complete_operation(operation_id, {"success": True})
                return result
                
            except Exception as e:
                loading_manager.fail_operation(operation_id, str(e))
                raise
                
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

@asynccontextmanager
async def loading_context(operation_id: str, operation_type: str = "general", metadata: Optional[Dict] = None):
    """
    Async context manager for managing loading states
    
    Usage:
        async with loading_context("document_upload", "upload") as ctx:
            # Perform long operation
            ctx.update_progress(50, "Processing document...")
            await process_document()
            ctx.update_progress(100, "Upload complete")
    """
    
    class LoadingContext:
        def __init__(self, op_id: str):
            self.operation_id = op_id
            
        def update_progress(self, progress: int, message: Optional[str] = None):
            loading_manager.update_progress(self.operation_id, progress, message)
            
    loading_manager.start_operation(operation_id, operation_type, metadata)
    context = LoadingContext(operation_id)
    
    try:
        yield context
        loading_manager.complete_operation(operation_id)
    except Exception as e:
        loading_manager.fail_operation(operation_id, str(e))
        raise

# Response models for loading states
from pydantic import BaseModel
from typing import List

class LoadingState(BaseModel):
    operation_id: str
    status: str  # loading, completed, failed
    type: str
    start_time: float
    end_time: Optional[float] = None
    progress: int = 0
    message: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}

class LoadingStatesResponse(BaseModel):
    states: List[LoadingState]
    active_count: int
    completed_count: int
    failed_count: int

# Database loading states for async operations
class DatabaseLoadingMixin:
    """Mixin for database operations with loading state tracking"""
    
    @staticmethod
    async def with_loading(operation_name: str, async_func: Callable, *args, **kwargs):
        """Execute database operation with loading state tracking"""
        import uuid
        operation_id = str(uuid.uuid4())
        
        async with loading_context(operation_id, "database", {"operation": operation_name}):
            return await async_func(*args, **kwargs)

# File upload loading states
class FileUploadProgress:
    """Track file upload progress with streaming updates"""
    
    def __init__(self, operation_id: str, total_size: int):
        self.operation_id = operation_id
        self.total_size = total_size
        self.uploaded_size = 0
        
    def update(self, chunk_size: int):
        """Update upload progress with new chunk"""
        self.uploaded_size += chunk_size
        progress = int((self.uploaded_size / self.total_size) * 100)
        
        loading_manager.update_progress(
            self.operation_id, 
            progress, 
            f"Uploaded {self.uploaded_size}/{self.total_size} bytes"
        )
        
    def complete(self):
        """Mark upload as complete"""
        loading_manager.complete_operation(self.operation_id, {
            "total_size": self.total_size,
            "uploaded_size": self.uploaded_size
        })

# Processing pipeline with stages
class PipelineProgress:
    """Track multi-stage processing with individual stage progress"""
    
    def __init__(self, operation_id: str, stages: List[str]):
        self.operation_id = operation_id
        self.stages = stages
        self.current_stage = 0
        self.stage_progress = 0
        
    def start_stage(self, stage_index: int):
        """Start a specific stage"""
        self.current_stage = stage_index
        self.stage_progress = 0
        stage_name = self.stages[stage_index] if stage_index < len(self.stages) else "Unknown"
        
        loading_manager.update_progress(
            self.operation_id,
            int((stage_index / len(self.stages)) * 100),
            f"Starting: {stage_name}"
        )
        
    def update_stage_progress(self, progress: int, message: Optional[str] = None):
        """Update progress within current stage"""
        self.stage_progress = progress
        
        # Calculate overall progress
        stage_weight = 100 / len(self.stages)
        stage_base = self.current_stage * stage_weight
        stage_offset = (progress / 100) * stage_weight
        overall_progress = int(stage_base + stage_offset)
        
        stage_name = self.stages[self.current_stage] if self.current_stage < len(self.stages) else "Unknown"
        full_message = f"{stage_name}: {message}" if message else stage_name
        
        loading_manager.update_progress(self.operation_id, overall_progress, full_message)
        
    def complete_stage(self):
        """Complete current stage and move to next"""
        self.current_stage += 1
        if self.current_stage >= len(self.stages):
            loading_manager.complete_operation(self.operation_id, {"stages_completed": len(self.stages)})
        else:
            self.start_stage(self.current_stage)

# Caching with loading states
class CacheLoadingWrapper:
    """Wrapper for caching operations with loading state feedback"""
    
    def __init__(self, cache_backend):
        self.cache = cache_backend
        
    async def get_or_compute(self, key: str, compute_func: Callable, ttl: int = 300):
        """Get from cache or compute with loading state"""
        # Try cache first
        cached_value = await self.cache.get(key)
        if cached_value is not None:
            return cached_value
            
        # Compute with loading state
        import uuid
        operation_id = str(uuid.uuid4())
        
        async with loading_context(operation_id, "cache_computation", {"cache_key": key}):
            result = await compute_func()
            await self.cache.set(key, result, ttl)
            return result

# Background task loading states
class BackgroundTaskManager:
    """Manage background tasks with loading state tracking"""
    
    def __init__(self):
        self.tasks = {}
        
    async def start_task(self, task_id: str, task_func: Callable, *args, **kwargs):
        """Start a background task with loading tracking"""
        loading_manager.start_operation(task_id, "background_task")
        
        async def task_wrapper():
            try:
                result = await task_func(*args, **kwargs)
                loading_manager.complete_operation(task_id, result)
                return result
            except Exception as e:
                loading_manager.fail_operation(task_id, str(e))
                raise
                
        task = asyncio.create_task(task_wrapper())
        self.tasks[task_id] = task
        return task
        
    def get_task_status(self, task_id: str):
        """Get status of background task"""
        return loading_manager.get_operation_status(task_id)

# Global background task manager
background_tasks = BackgroundTaskManager()

# Cleanup scheduler
async def cleanup_old_states():
    """Periodic cleanup of old loading states"""
    while True:
        await asyncio.sleep(300)  # Run every 5 minutes
        loading_manager.cleanup_completed(300)  # Clean up operations older than 5 minutes
"""
Loading State API Endpoints
FastAPI endpoints for managing and monitoring loading states
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional, Dict, Any
import asyncio
import uuid
from datetime import datetime, timedelta

from loading_states import (
    loading_manager, 
    LoadingState, 
    LoadingStatesResponse,
    background_tasks,
    with_loading_state,
    loading_context
)

router = APIRouter(prefix="/api/loading", tags=["loading"])

@router.get("/states", response_model=LoadingStatesResponse)
async def get_loading_states(
    status: Optional[str] = Query(None, description="Filter by status: loading, completed, failed"),
    operation_type: Optional[str] = Query(None, description="Filter by operation type")
):
    """Get current loading states with optional filtering"""
    
    states = []
    active_count = 0
    completed_count = 0
    failed_count = 0
    
    for op_id, state_data in loading_manager.states.items():
        # Apply filters
        if status and state_data.get("status") != status:
            continue
        if operation_type and state_data.get("type") != operation_type:
            continue
            
        loading_state = LoadingState(
            operation_id=op_id,
            status=state_data.get("status", "unknown"),
            type=state_data.get("type", "general"),
            start_time=state_data.get("start_time", 0),
            end_time=state_data.get("end_time"),
            progress=state_data.get("progress", 0),
            message=state_data.get("message"),
            error=state_data.get("error"),
            metadata=state_data.get("metadata", {})
        )
        states.append(loading_state)
        
        # Count by status
        if loading_state.status == "loading":
            active_count += 1
        elif loading_state.status == "completed":
            completed_count += 1
        elif loading_state.status == "failed":
            failed_count += 1
    
    return LoadingStatesResponse(
        states=states,
        active_count=active_count,
        completed_count=completed_count,
        failed_count=failed_count
    )

@router.get("/states/{operation_id}")
async def get_operation_state(operation_id: str):
    """Get specific operation loading state"""
    
    state = loading_manager.get_operation_status(operation_id)
    if not state:
        raise HTTPException(status_code=404, detail="Operation not found")
        
    return LoadingState(
        operation_id=operation_id,
        status=state.get("status", "unknown"),
        type=state.get("type", "general"),
        start_time=state.get("start_time", 0),
        end_time=state.get("end_time"),
        progress=state.get("progress", 0),
        message=state.get("message"),
        error=state.get("error"),
        metadata=state.get("metadata", {})
    )

@router.post("/cleanup")
async def cleanup_loading_states(max_age_seconds: int = Query(300, description="Max age in seconds for completed operations")):
    """Manually trigger cleanup of old loading states"""
    
    initial_count = len(loading_manager.states)
    loading_manager.cleanup_completed(max_age_seconds)
    final_count = len(loading_manager.states)
    cleaned_count = initial_count - final_count
    
    return {
        "message": f"Cleaned up {cleaned_count} operations",
        "initial_count": initial_count,
        "final_count": final_count,
        "cleaned_count": cleaned_count
    }

@router.post("/test/long-operation")
@with_loading_state(operation_type="test", auto_complete=False)
async def test_long_operation(duration: int = Query(10, description="Duration in seconds")):
    """Test endpoint for demonstrating loading states"""
    
    operation_id = str(uuid.uuid4())
    
    async with loading_context(operation_id, "test_operation", {"duration": duration}) as ctx:
        for i in range(duration):
            await asyncio.sleep(1)
            progress = int(((i + 1) / duration) * 100)
            ctx.update_progress(progress, f"Step {i + 1} of {duration}")
            
    return {"message": f"Completed test operation in {duration} seconds", "operation_id": operation_id}

@router.post("/test/multi-stage")
async def test_multi_stage_operation():
    """Test multi-stage operation with loading states"""
    
    from loading_states import PipelineProgress
    
    operation_id = str(uuid.uuid4())
    stages = ["Initialize", "Process Data", "Validate Results", "Save Output", "Cleanup"]
    
    loading_manager.start_operation(operation_id, "multi_stage_test", {"stages": stages})
    pipeline = PipelineProgress(operation_id, stages)
    
    try:
        for stage_idx in range(len(stages)):
            pipeline.start_stage(stage_idx)
            
            # Simulate work within each stage
            for progress in range(0, 101, 25):
                await asyncio.sleep(0.5)
                pipeline.update_stage_progress(progress, f"Processing... {progress}%")
                
            pipeline.complete_stage()
            
        return {"message": "Multi-stage operation completed", "operation_id": operation_id}
        
    except Exception as e:
        loading_manager.fail_operation(operation_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/file-upload-simulation")
async def test_file_upload_simulation(file_size_mb: int = Query(5, description="Simulated file size in MB")):
    """Simulate file upload with progress tracking"""
    
    from loading_states import FileUploadProgress
    
    operation_id = str(uuid.uuid4())
    total_size = file_size_mb * 1024 * 1024  # Convert to bytes
    chunk_size = 64 * 1024  # 64KB chunks
    
    loading_manager.start_operation(operation_id, "file_upload", {"file_size_mb": file_size_mb})
    upload_progress = FileUploadProgress(operation_id, total_size)
    
    try:
        uploaded = 0
        while uploaded < total_size:
            await asyncio.sleep(0.1)  # Simulate network delay
            current_chunk = min(chunk_size, total_size - uploaded)
            upload_progress.update(current_chunk)
            uploaded += current_chunk
            
        upload_progress.complete()
        return {"message": f"File upload simulation completed", "operation_id": operation_id, "size_mb": file_size_mb}
        
    except Exception as e:
        loading_manager.fail_operation(operation_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/background-task")
async def start_background_task(task_duration: int = Query(30, description="Task duration in seconds")):
    """Start a background task with loading state tracking"""
    
    task_id = str(uuid.uuid4())
    
    async def background_work():
        """Simulate background work"""
        for i in range(task_duration):
            await asyncio.sleep(1)
            progress = int(((i + 1) / task_duration) * 100)
            loading_manager.update_progress(task_id, progress, f"Background work: {i + 1}/{task_duration}")
        return {"completed_steps": task_duration}
    
    await background_tasks.start_task(task_id, background_work)
    
    return {
        "message": "Background task started",
        "task_id": task_id,
        "check_status_url": f"/api/loading/states/{task_id}"
    }

@router.get("/test/background-task/{task_id}")
async def get_background_task_status(task_id: str):
    """Get status of background task"""
    
    status = background_tasks.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return status

@router.websocket("/ws/states")
async def websocket_loading_states(websocket):
    """WebSocket endpoint for real-time loading state updates"""
    
    await websocket.accept()
    
    try:
        last_state_count = 0
        
        while True:
            # Check for state changes
            current_states = loading_manager.states
            current_count = len(current_states)
            
            # Send update if states changed
            if current_count != last_state_count:
                states_data = []
                for op_id, state_data in current_states.items():
                    states_data.append({
                        "operation_id": op_id,
                        "status": state_data.get("status"),
                        "type": state_data.get("type"),
                        "progress": state_data.get("progress", 0),
                        "message": state_data.get("message"),
                        "error": state_data.get("error")
                    })
                
                await websocket.send_json({
                    "type": "states_update",
                    "states": states_data,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                last_state_count = current_count
            
            await asyncio.sleep(1)  # Check every second
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@router.get("/health")
async def loading_health_check():
    """Health check for loading state system"""
    
    total_states = len(loading_manager.states)
    active_states = sum(1 for state in loading_manager.states.values() if state.get("status") == "loading")
    
    # Check for stale operations (running for more than 1 hour)
    import time
    current_time = time.time()
    stale_operations = []
    
    for op_id, state in loading_manager.states.items():
        if state.get("status") == "loading" and (current_time - state.get("start_time", 0)) > 3600:
            stale_operations.append(op_id)
    
    health_status = "healthy"
    issues = []
    
    if len(stale_operations) > 0:
        health_status = "warning"
        issues.append(f"{len(stale_operations)} stale operations detected")
    
    if active_states > 100:  # Too many concurrent operations
        health_status = "warning"
        issues.append(f"High number of active operations: {active_states}")
        
    return {
        "status": health_status,
        "total_states": total_states,
        "active_states": active_states,
        "stale_operations": stale_operations,
        "issues": issues,
        "timestamp": datetime.utcnow().isoformat()
    }
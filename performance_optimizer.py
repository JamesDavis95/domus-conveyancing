"""
Phase 2B: Performance & Scalability Enhancements
================================================

Upgrades for handling 10,000+ matters/month
"""
import redis
from typing import Dict, Any, List, Optional
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from celery import Celery
from contextlib import asynccontextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Redis caching layer
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Celery for background processing  
celery_app = Celery('la_processing', broker='redis://localhost:6379')

class PerformanceOptimizer:
    """Performance and caching layer for LA system"""
    
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=20)
        self.cache_ttl = 3600  # 1 hour
        
    async def get_cached_matter(self, matter_id: str) -> Optional[Dict[str, Any]]:
        """Get matter from cache"""
        cache_key = f"matter:{matter_id}"
        cached = redis_client.get(cache_key)
        if cached:
            import json
            return json.loads(cached)
        return None
    
    async def cache_matter(self, matter_id: str, matter_data: Dict[str, Any]):
        """Cache matter data"""
        cache_key = f"matter:{matter_id}"
        import json
        redis_client.setex(cache_key, self.cache_ttl, json.dumps(matter_data, default=str))
    
    async def batch_geocode_addresses(self, addresses: List[str]) -> Dict[str, Dict[str, float]]:
        """Batch geocode multiple addresses for performance"""
        # Use thread pool for I/O intensive geocoding
        loop = asyncio.get_event_loop()
        
        async def geocode_single(address: str) -> tuple:
            from spatial_intelligence import SpatialIntelligence
            spatial = SpatialIntelligence()
            result = await loop.run_in_executor(
                self.thread_pool,
                spatial.geocode_address,
                address
            )
            return address, result
        
        # Process in batches of 10
        results = {}
        batch_size = 10
        
        for i in range(0, len(addresses), batch_size):
            batch = addresses[i:i + batch_size]
            tasks = [geocode_single(addr) for addr in batch]
            batch_results = await asyncio.gather(*tasks)
            
            for address, geocode_result in batch_results:
                results[address] = geocode_result
                
        return results
    
    async def precompute_sla_dashboard(self) -> Dict[str, Any]:
        """Pre-compute SLA dashboard data"""
        cache_key = "sla_dashboard"
        cached = redis_client.get(cache_key)
        
        if cached:
            import json
            return json.loads(cached)
            
        # Compute fresh data
        from sla import sla_manager
        dashboard_data = await sla_manager.get_dashboard_metrics()
        
        # Cache for 10 minutes
        redis_client.setex(cache_key, 600, json.dumps(dashboard_data, default=str))
        return dashboard_data

# Database connection pooling
class DatabasePool:
    """Optimized database connection management"""
    
    def __init__(self):
        from sqlalchemy import create_engine
        from sqlalchemy.pool import QueuePool
        
        self.engine = create_engine(
            "postgresql://user:pass@localhost/domus_la",  # Production DB
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )
    
    @asynccontextmanager
    async def get_db_session(self):
        """Get optimized database session"""
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

# Celery tasks for background processing
@celery_app.task
def process_document_async(matter_id: str, document_data: bytes, document_type: str):
    """Process documents in background"""
    from la.services import parse_and_store
    from la.models import LAMatter
    
    with DatabasePool().get_db_session() as db:
        matter = db.query(LAMatter).filter(LAMatter.id == matter_id).first()
        if matter:
            docs = [(document_type, document_data)]
            parse_and_store(db, matter, docs)
    
    return {"status": "processed", "matter_id": matter_id}

@celery_app.task 
def bulk_sla_check():
    """Check SLA status for all active matters"""
    from sla import sla_manager
    from la.models import LAMatter
    
    with DatabasePool().get_db_session() as db:
        active_matters = db.query(LAMatter).filter(
            LAMatter.status.in_(["created", "in_progress", "assigned"])
        ).all()
        
        updated_count = 0
        for matter in active_matters:
            old_status = matter.sla_status
            new_status = sla_manager.check_sla_status(matter.id, db)
            if old_status != new_status:
                updated_count += 1
                
        return {"matters_checked": len(active_matters), "updated": updated_count}

# API Rate limiting
class RateLimiter:
    """Rate limiting for API endpoints"""
    
    def __init__(self, max_requests: int = 1000, window_minutes: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        
    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client is within rate limits"""
        key = f"rate_limit:{client_id}"
        current = redis_client.get(key)
        
        if current is None:
            redis_client.setex(key, self.window_seconds, 1)
            return True
            
        if int(current) >= self.max_requests:
            return False
            
        redis_client.incr(key)
        return True

# Monitoring and metrics
class MetricsCollector:
    """Collect performance metrics"""
    
    def record_api_call(self, endpoint: str, duration_ms: float, status_code: int):
        """Record API call metrics"""
        metrics = {
            "endpoint": endpoint,
            "duration_ms": duration_ms,
            "status_code": status_code,
            "timestamp": time.time()
        }
        
        # Store in time-series format for monitoring
        redis_client.lpush("api_metrics", json.dumps(metrics))
        redis_client.ltrim("api_metrics", 0, 10000)  # Keep last 10k records
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        metrics_raw = redis_client.lrange("api_metrics", 0, -1)
        metrics = [json.loads(m) for m in metrics_raw]
        
        if not metrics:
            return {"message": "No metrics available"}
            
        # Calculate stats
        durations = [m["duration_ms"] for m in metrics]
        return {
            "total_requests": len(metrics),
            "avg_duration_ms": sum(durations) / len(durations),
            "max_duration_ms": max(durations),
            "min_duration_ms": min(durations),
            "error_rate": len([m for m in metrics if m["status_code"] >= 400]) / len(metrics)
        }

# Health checks
class HealthChecker:
    """System health monitoring"""
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        checks = {
            "database": await self._check_database(),
            "redis": await self._check_redis(), 
            "celery": await self._check_celery(),
            "disk_space": await self._check_disk_space(),
            "memory_usage": await self._check_memory()
        }
        
        all_healthy = all(check["healthy"] for check in checks.values())
        
        return {
            "healthy": all_healthy,
            "checks": checks,
            "timestamp": time.time()
        }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            with DatabasePool().get_db_session() as db:
                db.execute("SELECT 1")
                return {"healthy": True, "message": "Database responsive"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity"""
        try:
            redis_client.ping()
            return {"healthy": True, "message": "Redis responsive"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_celery(self) -> Dict[str, Any]:
        """Check Celery worker status"""
        try:
            inspect = celery_app.control.inspect()
            stats = inspect.stats()
            if stats:
                return {"healthy": True, "workers": len(stats), "message": "Celery workers active"}
            else:
                return {"healthy": False, "message": "No Celery workers found"}
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space"""
        import shutil
        try:
            total, used, free = shutil.disk_usage("/")
            free_percent = (free / total) * 100
            
            return {
                "healthy": free_percent > 10,  # Alert if less than 10% free
                "free_percent": free_percent,
                "message": f"{free_percent:.1f}% disk space available"
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
    
    async def _check_memory(self) -> Dict[str, Any]:
        """Check memory usage"""
        import psutil
        try:
            memory = psutil.virtual_memory()
            return {
                "healthy": memory.percent < 90,  # Alert if over 90% used
                "usage_percent": memory.percent,
                "message": f"{memory.percent:.1f}% memory used"
            }
        except Exception as e:
            return {"healthy": False, "error": str(e)}
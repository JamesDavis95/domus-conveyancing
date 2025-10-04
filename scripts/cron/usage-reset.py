#!/usr/bin/env python3
"""
Usage Reset Script - Reset monthly quotas for all organizations
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from datetime import datetime
from database_config import get_db
from health_monitoring import AlertService

class UsageResetService:
    @staticmethod
    async def reset_monthly_quotas():
        """Reset monthly usage counters for all organizations"""
        try:
            print(f"[{datetime.now()}] Starting monthly quota reset...")
            
            db = next(get_db())
            from models import UsageCounters
            
            current_month = datetime.now().strftime('%Y-%m')
            
            # Get all usage counters for current month
            usage_records = db.query(UsageCounters).filter(
                UsageCounters.month == current_month
            ).all()
            
            reset_count = 0
            for usage in usage_records:
                # Reset monthly counters
                usage.docs_used = 0
                usage.api_calls_used = 0
                reset_count += 1
            
            db.commit()
            
            print(f"[{datetime.now()}] Monthly quota reset completed - {reset_count} organizations reset")
            
            await AlertService.send_alert(
                title="Monthly Quota Reset Completed",
                message=f"Successfully reset monthly quotas for {reset_count} organizations",
                level="info"
            )
            
            return True
            
        except Exception as e:
            error_msg = f"Monthly quota reset failed: {str(e)}"
            print(f"[{datetime.now()}] ERROR: {error_msg}")
            await AlertService.send_alert(
                title="Monthly Quota Reset Failed",
                message=error_msg,
                level="error"
            )
            return False
    
    @staticmethod
    async def cleanup_old_usage_data():
        """Clean up usage data older than 12 months"""
        try:
            print(f"[{datetime.now()}] Starting usage data cleanup...")
            
            db = next(get_db())
            from models import UsageCounters
            from datetime import datetime, timedelta
            
            # Calculate cutoff date (12 months ago)
            cutoff_date = datetime.now() - timedelta(days=365)
            cutoff_month = cutoff_date.strftime('%Y-%m')
            
            # Delete old usage records
            deleted_count = db.query(UsageCounters).filter(
                UsageCounters.month < cutoff_month
            ).delete()
            
            db.commit()
            
            print(f"[{datetime.now()}] Usage data cleanup completed - {deleted_count} old records removed")
            return True
            
        except Exception as e:
            error_msg = f"Usage data cleanup failed: {str(e)}"
            print(f"[{datetime.now()}] ERROR: {error_msg}")
            await AlertService.send_alert(
                title="Usage Data Cleanup Failed",
                message=error_msg,
                level="warning"
            )
            return False

async def main():
    """Main usage reset function"""
    print(f"[{datetime.now()}] Starting usage management tasks...")
    
    try:
        # Reset monthly quotas
        reset_success = await UsageResetService.reset_monthly_quotas()
        
        # Cleanup old data
        cleanup_success = await UsageResetService.cleanup_old_usage_data()
        
        if reset_success and cleanup_success:
            print(f"[{datetime.now()}] Usage management completed successfully")
        else:
            print(f"[{datetime.now()}] Usage management completed with some errors")
            
    except Exception as e:
        error_msg = f"Usage management script failed: {str(e)}"
        print(f"[{datetime.now()}] CRITICAL ERROR: {error_msg}")
        await AlertService.send_alert(
            title="Usage Management Script Failed",
            message=error_msg,
            level="error"
        )

if __name__ == "__main__":
    asyncio.run(main())
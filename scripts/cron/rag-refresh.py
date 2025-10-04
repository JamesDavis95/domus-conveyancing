#!/usr/bin/env python3
"""
RAG Refresh Script - Update policy corpus and legal precedents
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from datetime import datetime
from database_config import get_db
from health_monitoring import FreshnessService, AlertService

class RAGRefreshService:
    @staticmethod
    async def refresh_policy_corpus():
        """Refresh planning policy documents and legal texts"""
        try:
            print(f"[{datetime.now()}] Starting policy corpus refresh...")
            
            # Mock implementation - replace with real policy ingestion
            sources = [
                "National Planning Policy Framework",
                "Planning Practice Guidance", 
                "Local Plan Policies",
                "Appeal Decisions",
                "Planning White Paper Updates"
            ]
            
            for source in sources:
                print(f"  Processing {source}...")
                # Simulate processing time
                await asyncio.sleep(2)
                
                # Update freshness
                db = next(get_db())
                await FreshnessService.update_source_freshness(
                    source=source.lower().replace(" ", "_"),
                    status="updated",
                    db=db
                )
            
            print(f"[{datetime.now()}] Policy corpus refresh completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Policy corpus refresh failed: {str(e)}"
            print(f"[{datetime.now()}] ERROR: {error_msg}")
            await AlertService.send_alert(
                title="RAG Refresh Failed",
                message=error_msg,
                level="error"
            )
            return False
    
    @staticmethod
    async def refresh_legal_precedents():
        """Refresh legal precedents and case law"""
        try:
            print(f"[{datetime.now()}] Starting legal precedents refresh...")
            
            # Mock implementation - replace with real case law ingestion
            precedent_sources = [
                "Recent Appeal Decisions",
                "High Court Planning Cases", 
                "Secretary of State Decisions",
                "Local Authority Determinations"
            ]
            
            for source in precedent_sources:
                print(f"  Processing {source}...")
                # Simulate processing time
                await asyncio.sleep(3)
            
            # Update freshness
            db = next(get_db())
            await FreshnessService.update_source_freshness(
                source="legal_precedents",
                status="updated", 
                db=db
            )
            
            print(f"[{datetime.now()}] Legal precedents refresh completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Legal precedents refresh failed: {str(e)}"
            print(f"[{datetime.now()}] ERROR: {error_msg}")
            await AlertService.send_alert(
                title="Precedents Refresh Failed", 
                message=error_msg,
                level="error"
            )
            return False

async def main():
    """Main refresh function"""
    print(f"[{datetime.now()}] Starting RAG data refresh...")
    
    try:
        # Run policy corpus refresh
        policy_success = await RAGRefreshService.refresh_policy_corpus()
        
        # Run legal precedents refresh
        precedents_success = await RAGRefreshService.refresh_legal_precedents()
        
        if policy_success and precedents_success:
            print(f"[{datetime.now()}] RAG refresh completed successfully")
            await AlertService.send_alert(
                title="RAG Refresh Completed",
                message="Policy corpus and legal precedents updated successfully",
                level="info"
            )
        else:
            print(f"[{datetime.now()}] RAG refresh completed with errors")
            
    except Exception as e:
        error_msg = f"RAG refresh script failed: {str(e)}"
        print(f"[{datetime.now()}] CRITICAL ERROR: {error_msg}")
        await AlertService.send_alert(
            title="RAG Refresh Script Failed",
            message=error_msg,
            level="error"
        )

if __name__ == "__main__":
    asyncio.run(main())
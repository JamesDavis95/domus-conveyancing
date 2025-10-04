"""
Database Migration: AI Explainability and Citation Tracking
Creates tables for storing AI responses, citations, and explainability data
"""

import sqlite3
from datetime import datetime
import os

def migrate_explainability_tables(db_path="dev.db"):
    """Create tables for AI explainability and citation tracking"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # AI Responses table - stores all AI responses with explainability data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT UNIQUE NOT NULL,
                query TEXT NOT NULL,
                response_text TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                model_provider TEXT,
                confidence_score REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                lpa_code TEXT,
                is_valid BOOLEAN NOT NULL DEFAULT 0,
                is_blocked BOOLEAN NOT NULL DEFAULT 0,
                processing_time_ms INTEGER,
                
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create indexes for ai_responses
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_responses_response_id ON ai_responses (response_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_responses_created_at ON ai_responses (created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_responses_lpa_code ON ai_responses (lpa_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_responses_user_id ON ai_responses (user_id)")
        
        # Citations table - stores citation information
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                citation_id TEXT UNIQUE NOT NULL,
                response_id TEXT NOT NULL,
                citation_type TEXT NOT NULL,
                citation_quality TEXT NOT NULL,
                title TEXT NOT NULL,
                authority TEXT NOT NULL,
                citation_date DATE NOT NULL,
                url TEXT,
                section_reference TEXT,
                page_numbers TEXT,
                paragraph_reference TEXT,
                relevance_score REAL NOT NULL,
                content_excerpt TEXT NOT NULL,
                context_explanation TEXT NOT NULL,
                lpa_code TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (response_id) REFERENCES ai_responses (response_id)
            )
        """)
        
        # Create indexes for citations
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_citations_response_id ON citations (response_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_citations_type ON citations (citation_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_citations_quality ON citations (citation_quality)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_citations_lpa_code ON citations (lpa_code)")
        
        # Reasoning Chain table - stores step-by-step reasoning
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reasoning_chains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT NOT NULL,
                step_number INTEGER NOT NULL,
                reasoning_step TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (response_id) REFERENCES ai_responses (response_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reasoning_chains_response_id ON reasoning_chains (response_id)")
        
        # Assumptions table - stores AI response assumptions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_assumptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT NOT NULL,
                assumption_text TEXT NOT NULL,
                assumption_type TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (response_id) REFERENCES ai_responses (response_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_assumptions_response_id ON ai_assumptions (response_id)")
        
        # Limitations table - stores AI response limitations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_limitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT NOT NULL,
                limitation_text TEXT NOT NULL,
                limitation_type TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (response_id) REFERENCES ai_responses (response_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_limitations_response_id ON ai_limitations (response_id)")
        
        # Alternative Interpretations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alternative_interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT NOT NULL,
                interpretation_text TEXT NOT NULL,
                confidence_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (response_id) REFERENCES ai_responses (response_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_alternative_interpretations_response_id ON alternative_interpretations (response_id)")
        
        # LPA Context table - stores LPA-specific context data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lpa_context_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT NOT NULL,
                lpa_code TEXT NOT NULL,
                lpa_name TEXT,
                hdt_score INTEGER,
                hdt_status TEXT,
                hdt_year TEXT,
                five_yhls_years REAL,
                five_yhls_assessment_date DATE,
                five_yhls_buffer TEXT,
                local_plan_adoption_date DATE,
                recent_appeals_total INTEGER,
                appeals_allowed_rate REAL,
                snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (response_id) REFERENCES ai_responses (response_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lpa_context_response_id ON lpa_context_snapshots (response_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lpa_context_lpa_code ON lpa_context_snapshots (lpa_code)")
        
        # Analysis Snapshots table - stores full analysis snapshots for audit
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT UNIQUE NOT NULL,
                response_id TEXT NOT NULL,
                snapshot_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (response_id) REFERENCES ai_responses (response_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_snapshots_response_id ON analysis_snapshots (response_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_snapshots_snapshot_id ON analysis_snapshots (snapshot_id)")
        
        # Citation Quality Metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citation_quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT NOT NULL,
                total_citations INTEGER NOT NULL,
                primary_citations INTEGER NOT NULL DEFAULT 0,
                secondary_citations INTEGER NOT NULL DEFAULT 0,
                tertiary_citations INTEGER NOT NULL DEFAULT 0,
                average_relevance_score REAL NOT NULL,
                citation_score REAL NOT NULL,
                explainability_score REAL NOT NULL,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (response_id) REFERENCES ai_responses (response_id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_citation_quality_response_id ON citation_quality_metrics (response_id)")
        
        # Blocked Responses table - stores responses blocked for insufficient citations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blocked_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT NOT NULL,
                query TEXT NOT NULL,
                block_reason TEXT NOT NULL,
                attempted_response TEXT,
                user_id INTEGER,
                lpa_code TEXT,
                blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blocked_responses_user_id ON blocked_responses (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_blocked_responses_blocked_at ON blocked_responses (blocked_at)")
        
        # Model Performance Tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                date DATE NOT NULL,
                total_responses INTEGER NOT NULL DEFAULT 0,
                valid_responses INTEGER NOT NULL DEFAULT 0,
                blocked_responses INTEGER NOT NULL DEFAULT 0,
                average_confidence REAL,
                average_citation_score REAL,
                average_explainability_score REAL
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_performance_date ON model_performance (date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_performance_model ON model_performance (model_name, model_version)")
        
        # Insert default configuration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS explainability_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default config values
        default_configs = [
            ('min_citations_required', '2'),
            ('min_confidence_threshold', '0.7'),
            ('require_primary_citations', 'false'),
            ('block_uncited_suggestions', 'true'),
            ('enable_lpa_context', 'true'),
            ('citation_relevance_threshold', '0.5')
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO explainability_config (config_key, config_value)
            VALUES (?, ?)
        """, default_configs)
        
        conn.commit()
        
        print("✅ AI Explainability database tables created successfully")
        print(f"   - ai_responses: Main AI response tracking")
        print(f"   - citations: Citation provenance and metadata") 
        print(f"   - reasoning_chains: Step-by-step reasoning tracking")
        print(f"   - ai_assumptions: AI response assumptions")
        print(f"   - ai_limitations: AI response limitations")
        print(f"   - alternative_interpretations: Alternative interpretations")
        print(f"   - lpa_context_snapshots: LPA-specific context data")
        print(f"   - analysis_snapshots: Full analysis audit trail")
        print(f"   - citation_quality_metrics: Citation quality tracking")
        print(f"   - blocked_responses: Blocked response tracking")
        print(f"   - model_performance: Model performance metrics")
        print(f"   - explainability_config: Configuration management")
        
        # Add sample data for testing
        sample_response_id = "test_response_001"
        cursor.execute("""
            INSERT OR IGNORE INTO ai_responses 
            (response_id, query, response_text, model_name, model_version, model_provider, 
             confidence_score, lpa_code, is_valid, is_blocked)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            sample_response_id,
            "What are the planning considerations for a residential development?",
            "Planning considerations include design, transport, environment, and heritage factors...",
            "gpt-4",
            "2024-03",
            "openai",
            0.85,
            "E06000001",
            True,
            False
        ))
        
        # Sample citation
        cursor.execute("""
            INSERT OR IGNORE INTO citations
            (citation_id, response_id, citation_type, citation_quality, title, authority,
             citation_date, relevance_score, content_excerpt, context_explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "cite_001",
            sample_response_id,
            "planning_guidance",
            "secondary", 
            "National Planning Policy Framework",
            "Department for Levelling Up, Housing and Communities",
            "2023-12-19",
            0.90,
            "Planning policies should support development that makes efficient use of land",
            "Provides national policy context for residential development"
        ))
        
        conn.commit()
        print("✅ Sample explainability data inserted")
        
    except Exception as e:
        print(f"❌ Error creating explainability tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_explainability_tables()
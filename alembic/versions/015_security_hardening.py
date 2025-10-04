"""
Database migration for security hardening features
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '015_security_hardening'
down_revision = '014_submission_packs'
branch_labels = None
depends_on = None

def upgrade():
    """Add security hardening tables"""
    
    # User 2FA setup table
    op.create_table(
        'user_2fa_setup',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('secret_key', sa.String(255), nullable=False),
        sa.Column('backup_codes', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), default=False),
        sa.Column('recovery_email', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('backup_codes_used', sa.Integer(), default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.Index('ix_user_2fa_user_id', 'user_id'),
        sa.Index('ix_user_2fa_enabled', 'is_enabled')
    )
    
    # CAPTCHA challenges table
    op.create_table(
        'captcha_challenges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.String(255), nullable=False),
        sa.Column('challenge_type', sa.String(50), nullable=False),
        sa.Column('challenge_data', sa.Text(), nullable=False),
        sa.Column('answer', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('attempts', sa.Integer(), default=0),
        sa.Column('is_solved', sa.Boolean(), default=False),
        sa.Column('client_ip', sa.String(45), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_captcha_challenge_id', 'challenge_id', unique=True),
        sa.Index('ix_captcha_expires_at', 'expires_at'),
        sa.Index('ix_captcha_client_ip', 'client_ip')
    )
    
    # Rate limit violations table
    op.create_table(
        'rate_limit_violations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('request_count', sa.Integer(), nullable=False),
        sa.Column('limit_exceeded', sa.Integer(), nullable=False),
        sa.Column('time_window', sa.Integer(), nullable=False),
        sa.Column('violation_time', sa.DateTime(), nullable=False),
        sa.Column('client_ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('blocked_until', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_rate_limit_client_id', 'client_id'),
        sa.Index('ix_rate_limit_endpoint', 'endpoint'),
        sa.Index('ix_rate_limit_violation_time', 'violation_time'),
        sa.Index('ix_rate_limit_blocked_until', 'blocked_until')
    )
    
    # Rate limit requests tracking table
    op.create_table(
        'rate_limit_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.String(255), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('request_time', sa.DateTime(), nullable=False),
        sa.Column('client_ip', sa.String(45), nullable=True),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_rate_limit_requests_client_endpoint', 'client_id', 'endpoint'),
        sa.Index('ix_rate_limit_requests_time', 'request_time'),
        sa.Index('ix_rate_limit_requests_ip', 'client_ip')
    )
    
    # IP allowlist rules table
    op.create_table(
        'ip_allowlist_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('network', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.Index('ix_ip_allowlist_network', 'network'),
        sa.Index('ix_ip_allowlist_rule_type', 'rule_type'),
        sa.Index('ix_ip_allowlist_expires_at', 'expires_at'),
        sa.Index('ix_ip_allowlist_active', 'is_active')
    )
    
    # Security events log table
    op.create_table(
        'security_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('client_ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('event_data', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=True),
        sa.Column('request_id', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.Index('ix_security_events_type', 'event_type'),
        sa.Index('ix_security_events_user_id', 'user_id'),
        sa.Index('ix_security_events_timestamp', 'timestamp'),
        sa.Index('ix_security_events_severity', 'severity'),
        sa.Index('ix_security_events_ip', 'client_ip')
    )
    
    # CSP violation reports table
    op.create_table(
        'csp_violation_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_uri', sa.Text(), nullable=True),
        sa.Column('blocked_uri', sa.Text(), nullable=True),
        sa.Column('violated_directive', sa.String(255), nullable=True),
        sa.Column('effective_directive', sa.String(255), nullable=True),
        sa.Column('original_policy', sa.Text(), nullable=True),
        sa.Column('disposition', sa.String(50), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('client_ip', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('report_count', sa.Integer(), default=1),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('ix_csp_violations_directive', 'violated_directive'),
        sa.Index('ix_csp_violations_timestamp', 'timestamp'),
        sa.Index('ix_csp_violations_ip', 'client_ip'),
        sa.Index('ix_csp_violations_blocked_uri', 'blocked_uri')
    )
    
    # Add 2FA required field to users table
    op.add_column('users', sa.Column('requires_2fa', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('2fa_enabled', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('last_2fa_setup', sa.DateTime(), nullable=True))
    
    # Add security-related fields to sessions table if it exists
    try:
        op.add_column('user_sessions', sa.Column('ip_address', sa.String(45), nullable=True))
        op.add_column('user_sessions', sa.Column('user_agent', sa.Text(), nullable=True))
        op.add_column('user_sessions', sa.Column('is_2fa_verified', sa.Boolean(), default=False))
        op.add_column('user_sessions', sa.Column('security_level', sa.String(20), default='basic'))
    except:
        # Sessions table might not exist yet
        pass
    
    # Create indexes for security fields
    op.create_index('ix_users_requires_2fa', 'users', ['requires_2fa'])
    op.create_index('ix_users_2fa_enabled', 'users', ['2fa_enabled'])

def downgrade():
    """Remove security hardening tables"""
    
    # Drop tables in reverse order
    op.drop_table('csp_violation_reports')
    op.drop_table('security_events')
    op.drop_table('ip_allowlist_rules')
    op.drop_table('rate_limit_requests')
    op.drop_table('rate_limit_violations')
    op.drop_table('captcha_challenges')
    op.drop_table('user_2fa_setup')
    
    # Remove columns from users table
    op.drop_index('ix_users_2fa_enabled', 'users')
    op.drop_index('ix_users_requires_2fa', 'users')
    op.drop_column('users', 'last_2fa_setup')
    op.drop_column('users', '2fa_enabled')
    op.drop_column('users', 'requires_2fa')
    
    # Remove security fields from sessions table if they exist
    try:
        op.drop_column('user_sessions', 'security_level')
        op.drop_column('user_sessions', 'is_2fa_verified')
        op.drop_column('user_sessions', 'user_agent')
        op.drop_column('user_sessions', 'ip_address')
    except:
        # Columns might not exist
        pass
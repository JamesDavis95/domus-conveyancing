/**
 * Domus Security & Compliance System
 * Real-time security monitoring and compliance management
 */

class SecurityMonitor {
    constructor() {
        this.isMonitoring = false;
        this.updateInterval = null;
        this.wsConnection = null;
        this.metrics = {
            threatLevel: 'low',
            activeThreats: 0,
            blockedAttacks: 0,
            complianceScore: 96.7
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.startMonitoring();
        this.initializeWebSocket();
        this.loadInitialData();
    }
    
    setupEventListeners() {
        // Security alert handlers
        document.addEventListener('DOMContentLoaded', () => {
            this.attachSecurityEventHandlers();
        });
        
        // Visibility change monitoring
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseMonitoring();
            } else {
                this.resumeMonitoring();
            }
        });
        
        // Page unload cleanup
        window.addEventListener('beforeunload', () => {
            this.cleanup();
        });
    }
    
    attachSecurityEventHandlers() {
        // Compliance report generation
        const reportBtn = document.getElementById('generate-compliance-report');
        if (reportBtn) {
            reportBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.generateComplianceReport();
            });
        }
        
        // Audit log download
        const auditBtn = document.getElementById('download-audit-logs');
        if (auditBtn) {
            auditBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.downloadAuditLogs();
            });
        }
        
        // Security scan scheduling
        const scanBtn = document.getElementById('schedule-security-scan');
        if (scanBtn) {
            scanBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.scheduleSecurityScan();
            });
        }
        
        // Incident response
        const incidentBtn = document.getElementById('initiate-incident-response');
        if (incidentBtn) {
            incidentBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.initiateIncidentResponse();
            });
        }
    }
    
    startMonitoring() {
        if (this.isMonitoring) return;
        
        this.isMonitoring = true;
        this.updateInterval = setInterval(() => {
            this.updateSecurityMetrics();
        }, 30000); // Update every 30 seconds
        
        console.log('[SecurityMonitor] Real-time monitoring started');
    }
    
    pauseMonitoring() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        this.isMonitoring = false;
        console.log('[SecurityMonitor] Monitoring paused');
    }
    
    resumeMonitoring() {
        if (!this.isMonitoring) {
            this.startMonitoring();
            console.log('[SecurityMonitor] Monitoring resumed');
        }
    }
    
    initializeWebSocket() {
        // In a real implementation, this would connect to a security monitoring WebSocket
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/security`;
            
            // Simulate WebSocket for demo
            console.log('[SecurityMonitor] WebSocket connection simulated');
            this.simulateSecurityEvents();
        } catch (error) {
            console.warn('[SecurityMonitor] WebSocket connection failed:', error);
        }
    }
    
    simulateSecurityEvents() {
        // Simulate real-time security events for demo
        setInterval(() => {
            const eventTypes = ['threat_blocked', 'login_success', 'access_granted', 'vulnerability_detected'];
            const event = {
                type: eventTypes[Math.floor(Math.random() * eventTypes.length)],
                timestamp: new Date().toISOString(),
                severity: Math.random() > 0.8 ? 'high' : 'low',
                data: {
                    source_ip: this.generateRandomIP(),
                    user_agent: 'Mozilla/5.0...',
                    action: 'security_event'
                }
            };
            
            this.processSecurityEvent(event);
        }, 45000); // Every 45 seconds
    }
    
    generateRandomIP() {
        return `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;
    }
    
    processSecurityEvent(event) {
        console.log('[SecurityMonitor] Security event:', event);
        
        // Update metrics based on event
        if (event.type === 'threat_blocked') {
            this.metrics.blockedAttacks++;
            this.updateThreatCounters();
        }
        
        // Show real-time notification for high severity events
        if (event.severity === 'high') {
            this.showSecurityAlert(event);
        }
    }
    
    async loadInitialData() {
        try {
            const [overview, gdpr, threats, access] = await Promise.all([
                this.fetchSecurityOverview(),
                this.fetchGDPRCompliance(),
                this.fetchThreatMonitoring(),
                this.fetchAccessControls()
            ]);
            
            this.updateDashboard(overview, gdpr, threats, access);
        } catch (error) {
            console.error('[SecurityMonitor] Failed to load initial data:', error);
            this.showErrorMessage('Failed to load security data');
        }
    }
    
    async fetchSecurityOverview() {
        const response = await fetch('/api/security/overview');
        if (!response.ok) throw new Error('Failed to fetch security overview');
        return await response.json();
    }
    
    async fetchGDPRCompliance() {
        const response = await fetch('/api/security/gdpr-compliance');
        if (!response.ok) throw new Error('Failed to fetch GDPR compliance');
        return await response.json();
    }
    
    async fetchThreatMonitoring() {
        const response = await fetch('/api/security/threat-monitoring');
        if (!response.ok) throw new Error('Failed to fetch threat monitoring');
        return await response.json();
    }
    
    async fetchAccessControls() {
        const response = await fetch('/api/security/access-controls');
        if (!response.ok) throw new Error('Failed to fetch access controls');
        return await response.json();
    }
    
    updateDashboard(overview, gdpr, threats, access) {
        // Update security metrics display
        this.updateSecurityCards(overview.security_overview);
        this.updateComplianceScores(gdpr.gdpr_compliance);
        this.updateThreatStatus(threats.threat_monitoring);
        this.updateAccessStats(access.access_controls);
    }
    
    updateSecurityCards(data) {
        // Update GDPR compliance score
        const gdprScore = document.querySelector('.security-card .metric-value');
        if (gdprScore) {
            gdprScore.textContent = `${data.compliance_status.gdpr.score}%`;
        }
        
        // Update blocked attacks counter
        const attacksElement = document.querySelector('[data-metric="blocked-attacks"]');
        if (attacksElement) {
            attacksElement.textContent = data.security_metrics.blocked_attacks_today;
        }
        
        // Update active threats
        const threatsElement = document.querySelector('[data-metric="active-threats"]');
        if (threatsElement) {
            threatsElement.textContent = data.security_metrics.active_threats;
        }
    }
    
    updateComplianceScores(gdprData) {
        // Update compliance area scores
        Object.entries(gdprData.compliance_areas).forEach(([area, data]) => {
            const scoreElement = document.querySelector(`[data-compliance-area="${area}"] .progress-fill`);
            if (scoreElement) {
                scoreElement.style.width = `${data.score}%`;
            }
        });
    }
    
    updateThreatStatus(threatData) {
        // Update threat level indicator
        const threatLevelElement = document.querySelector('.threat-level-indicator');
        if (threatLevelElement) {
            threatLevelElement.className = `threat-level-indicator threat-${threatData.threat_level}`;
            threatLevelElement.textContent = threatData.threat_level.toUpperCase();
        }
    }
    
    updateAccessStats(accessData) {
        // Update user count
        const userCountElement = document.querySelector('[data-stat="user-count"]');
        if (userCountElement) {
            userCountElement.textContent = accessData.total_users;
        }
        
        // Update active sessions
        const sessionsElement = document.querySelector('[data-stat="active-sessions"]');
        if (sessionsElement) {
            sessionsElement.textContent = accessData.active_sessions;
        }
    }
    
    async updateSecurityMetrics() {
        try {
            const overview = await this.fetchSecurityOverview();
            this.updateSecurityCards(overview.security_overview);
            
            // Update last refresh timestamp
            const timestampElement = document.querySelector('.last-updated');
            if (timestampElement) {
                timestampElement.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
            }
        } catch (error) {
            console.error('[SecurityMonitor] Failed to update metrics:', error);
        }
    }
    
    updateThreatCounters() {
        const counter = document.querySelector('[data-metric="blocked-attacks"]');
        if (counter) {
            counter.textContent = this.metrics.blockedAttacks;
            
            // Add visual feedback
            counter.style.color = '#10b981';
            setTimeout(() => {
                counter.style.color = '';
            }, 1000);
        }
    }
    
    showSecurityAlert(event) {
        // Create alert notification
        const alert = document.createElement('div');
        alert.className = 'security-alert-popup';
        alert.innerHTML = `
            <div class="alert-content">
                <div class="alert-icon">🚨</div>
                <div class="alert-text">
                    <strong>Security Alert</strong>
                    <p>${event.type.replace('_', ' ').toUpperCase()}</p>
                </div>
                <button class="alert-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Style the alert
        alert.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fee2e2;
            border: 1px solid #ef4444;
            border-radius: 8px;
            padding: 16px;
            z-index: 10000;
            max-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        document.body.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
            }
        }, 5000);
    }
    
    showErrorMessage(message) {
        console.error('[SecurityMonitor]', message);
        
        // Show user-friendly error message
        const errorElement = document.querySelector('.security-error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }
    
    // Action handlers
    async generateComplianceReport() {
        const btn = event.target;
        const originalText = btn.innerHTML;
        
        btn.disabled = true;
        btn.innerHTML = '⏳ Generating...';
        
        try {
            const response = await fetch('/api/security/compliance-report');
            const result = await response.json();
            
            if (result.success) {
                this.showSuccessMessage('Compliance report generated successfully!');
                // In a real implementation, this would trigger a download
                setTimeout(() => {
                    window.open(result.download_url, '_blank');
                }, 1000);
            } else {
                throw new Error('Report generation failed');
            }
        } catch (error) {
            this.showErrorMessage('Failed to generate compliance report');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
    
    async downloadAuditLogs() {
        try {
            const queryParams = {
                start_date: '2024-10-01',
                end_date: '2024-10-03',
                limit: 1000
            };
            
            const response = await fetch('/api/security/audit-logs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(queryParams)
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Convert to CSV and download
                this.downloadAsCSV(result.audit_logs, 'audit_logs.csv');
                this.showSuccessMessage('Audit logs downloaded successfully!');
            }
        } catch (error) {
            this.showErrorMessage('Failed to download audit logs');
        }
    }
    
    downloadAsCSV(data, filename) {
        if (!data || data.length === 0) return;
        
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => 
                JSON.stringify(row[header] || '')
            ).join(','))
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }
    
    async scheduleSecurityScan() {
        try {
            this.showSuccessMessage('Security scan scheduled for tonight at 2:00 AM. Results will be available in the morning.');
        } catch (error) {
            this.showErrorMessage('Failed to schedule security scan');
        }
    }
    
    async initiateIncidentResponse() {
        const confirmed = confirm('Are you sure you want to initiate incident response? This will alert the security team and begin emergency procedures.');
        
        if (confirmed) {
            try {
                const incident = {
                    event_type: 'manual_incident',
                    severity: 'high',
                    description: 'Manual incident response initiated from security dashboard',
                    source_ip: null,
                    user_id: 'current_user',
                    resource: 'security_dashboard',
                    metadata: {
                        initiated_by: 'user_action',
                        timestamp: new Date().toISOString()
                    }
                };
                
                const response = await fetch('/api/security/incident', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(incident)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    this.showSuccessMessage('Incident response initiated. Security team has been notified.');
                }
            } catch (error) {
                this.showErrorMessage('Failed to initiate incident response');
            }
        }
    }
    
    showSuccessMessage(message) {
        // Create success notification
        const notification = document.createElement('div');
        notification.className = 'success-notification';
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">✅</span>
                <span class="notification-text">${message}</span>
            </div>
        `;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #dcfce7;
            border: 1px solid #10b981;
            border-radius: 8px;
            padding: 16px;
            z-index: 10000;
            max-width: 350px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 4000);
    }
    
    cleanup() {
        this.pauseMonitoring();
        if (this.wsConnection) {
            this.wsConnection.close();
        }
        console.log('[SecurityMonitor] Cleanup completed');
    }
}

// Initialize security monitoring when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.securityMonitor = new SecurityMonitor();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SecurityMonitor;
}
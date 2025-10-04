/**
 * Global Error Handler & User Experience Manager
 * Handles errors gracefully and provides consistent UX patterns
 */

class ErrorHandler {
    constructor() {
        this.errors = [];
        this.maxErrors = 50;
        this.notificationQueue = [];
        this.isNotificationShowing = false;
        this.retryAttempts = new Map();
        this.initializeGlobalHandlers();
    }

    initializeGlobalHandlers() {
        // Global error handler
        window.addEventListener('error', (event) => {
            this.handleJavaScriptError(event.error, event.filename, event.lineno);
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            this.handlePromiseRejection(event.reason);
            event.preventDefault(); // Prevent console error
        });

        // Network error detection
        window.addEventListener('online', () => {
            this.handleNetworkRestore();
        });

        window.addEventListener('offline', () => {
            this.handleNetworkLoss();
        });
    }

    // Error categorization
    categorizeError(error) {
        const errorStr = error.toString().toLowerCase();
        
        if (errorStr.includes('network') || errorStr.includes('fetch')) {
            return 'network';
        } else if (errorStr.includes('permission') || errorStr.includes('unauthorized')) {
            return 'permission';
        } else if (errorStr.includes('validation') || errorStr.includes('invalid')) {
            return 'validation';
        } else if (errorStr.includes('quota') || errorStr.includes('limit')) {
            return 'quota';
        } else if (errorStr.includes('timeout')) {
            return 'timeout';
        } else {
            return 'general';
        }
    }

    // Handle different error types
    handleJavaScriptError(error, filename, line) {
        const errorInfo = {
            type: 'javascript',
            error: error,
            filename: filename,
            line: line,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };

        this.logError(errorInfo);
        this.showUserFriendlyError('javascript', error);
    }

    handlePromiseRejection(reason) {
        const errorInfo = {
            type: 'promise',
            reason: reason,
            timestamp: new Date().toISOString(),
            url: window.location.href
        };

        this.logError(errorInfo);
        this.showUserFriendlyError('promise', reason);
    }

    handleAPIError(response, context = '') {
        const category = this.categorizeError(response.statusText || 'API Error');
        
        const errorInfo = {
            type: 'api',
            status: response.status,
            statusText: response.statusText,
            url: response.url,
            context: context,
            category: category,
            timestamp: new Date().toISOString()
        };

        this.logError(errorInfo);
        this.showUserFriendlyError(category, errorInfo);
        
        return this.createErrorResponse(errorInfo);
    }

    handleNetworkLoss() {
        this.showNotification({
            type: 'warning',
            title: 'Connection Lost',
            message: 'You appear to be offline. Some features may not work correctly.',
            icon: 'fas fa-wifi',
            persistent: true,
            id: 'network-offline'
        });
    }

    handleNetworkRestore() {
        this.hideNotification('network-offline');
        this.showNotification({
            type: 'success',
            title: 'Connection Restored',
            message: 'You are back online.',
            icon: 'fas fa-wifi',
            autoHide: 3000
        });
    }

    // User-friendly error messages
    getUserFriendlyMessage(category, error) {
        const messages = {
            network: {
                title: 'Connection Problem',
                message: 'Please check your internet connection and try again.',
                icon: 'fas fa-wifi',
                action: 'Retry'
            },
            permission: {
                title: 'Access Denied',
                message: 'You don\'t have permission to perform this action. Please sign in or contact support.',
                icon: 'fas fa-lock',
                action: 'Sign In'
            },
            validation: {
                title: 'Invalid Input',
                message: 'Please check your input and try again.',
                icon: 'fas fa-exclamation-triangle',
                action: 'Review'
            },
            quota: {
                title: 'Limit Exceeded',
                message: 'You\'ve reached your usage limit. Please upgrade your plan or try again later.',
                icon: 'fas fa-chart-line',
                action: 'Upgrade'
            },
            timeout: {
                title: 'Request Timeout',
                message: 'The request took too long to complete. Please try again.',
                icon: 'fas fa-clock',
                action: 'Retry'
            },
            javascript: {
                title: 'Unexpected Error',
                message: 'Something went wrong. Please refresh the page and try again.',
                icon: 'fas fa-bug',
                action: 'Refresh'
            },
            promise: {
                title: 'Processing Error',
                message: 'An error occurred while processing your request.',
                icon: 'fas fa-exclamation-circle',
                action: 'Retry'
            },
            general: {
                title: 'Error',
                message: 'An unexpected error occurred. Please try again or contact support.',
                icon: 'fas fa-exclamation-triangle',
                action: 'Retry'
            }
        };

        return messages[category] || messages.general;
    }

    showUserFriendlyError(category, error) {
        const friendlyError = this.getUserFriendlyMessage(category, error);
        
        this.showNotification({
            type: 'error',
            title: friendlyError.title,
            message: friendlyError.message,
            icon: friendlyError.icon,
            action: {
                text: friendlyError.action,
                callback: () => this.handleErrorAction(category, error)
            },
            autoHide: 8000
        });
    }

    handleErrorAction(category, error) {
        switch (category) {
            case 'network':
            case 'timeout':
                this.retryLastAction();
                break;
            case 'permission':
                window.location.href = '/login';
                break;
            case 'quota':
                window.location.href = '/settings/billing';
                break;
            case 'javascript':
                window.location.reload();
                break;
            default:
                this.retryLastAction();
        }
    }

    // Retry mechanism
    retryLastAction() {
        const lastAction = this.getLastAction();
        if (lastAction) {
            const retryKey = `${lastAction.url}_${lastAction.method}`;
            const attempts = this.retryAttempts.get(retryKey) || 0;
            
            if (attempts < 3) {
                this.retryAttempts.set(retryKey, attempts + 1);
                this.executeRetry(lastAction);
            } else {
                this.showNotification({
                    type: 'error',
                    title: 'Maximum Retries Reached',
                    message: 'Please refresh the page or contact support.',
                    autoHide: 5000
                });
            }
        }
    }

    // Notification system
    showNotification(config) {
        const {
            type = 'info',
            title,
            message,
            icon = 'fas fa-info-circle',
            action = null,
            autoHide = null,
            persistent = false,
            id = null
        } = config;

        const notification = {
            id: id || `notification-${Date.now()}`,
            type,
            title,
            message,
            icon,
            action,
            autoHide,
            persistent,
            timestamp: Date.now()
        };

        this.notificationQueue.push(notification);
        this.processNotificationQueue();
    }

    processNotificationQueue() {
        if (this.isNotificationShowing || this.notificationQueue.length === 0) {
            return;
        }

        const notification = this.notificationQueue.shift();
        this.displayNotification(notification);
    }

    displayNotification(notification) {
        this.isNotificationShowing = true;

        // Create notification element
        const notificationEl = document.createElement('div');
        notificationEl.id = notification.id;
        notificationEl.className = `alert alert-${this.getBootstrapType(notification.type)} alert-dismissible fade show position-fixed`;
        notificationEl.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px; max-width: 500px;';

        notificationEl.innerHTML = `
            <div class="d-flex align-items-start">
                <i class="${notification.icon} me-2 mt-1"></i>
                <div class="flex-grow-1">
                    ${notification.title ? `<h6 class="alert-heading mb-1">${notification.title}</h6>` : ''}
                    <div>${notification.message}</div>
                    ${notification.action ? `
                        <button class="btn btn-sm btn-outline-${this.getBootstrapType(notification.type)} mt-2 notification-action">
                            ${notification.action.text}
                        </button>
                    ` : ''}
                </div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        // Add to DOM
        document.body.appendChild(notificationEl);

        // Add action handler
        if (notification.action) {
            const actionBtn = notificationEl.querySelector('.notification-action');
            actionBtn.addEventListener('click', () => {
                notification.action.callback();
                this.hideNotification(notification.id);
            });
        }

        // Auto-hide
        if (notification.autoHide) {
            setTimeout(() => {
                this.hideNotification(notification.id);
            }, notification.autoHide);
        }

        // Handle dismiss
        notificationEl.addEventListener('closed.bs.alert', () => {
            this.onNotificationClosed();
        });
    }

    hideNotification(id) {
        const notification = document.getElementById(id);
        if (notification) {
            notification.remove();
            this.onNotificationClosed();
        }
    }

    onNotificationClosed() {
        this.isNotificationShowing = false;
        setTimeout(() => {
            this.processNotificationQueue();
        }, 100);
    }

    getBootstrapType(type) {
        const typeMap = {
            error: 'danger',
            warning: 'warning',
            success: 'success',
            info: 'info'
        };
        return typeMap[type] || 'info';
    }

    // Error logging
    logError(errorInfo) {
        this.errors.unshift(errorInfo);
        if (this.errors.length > this.maxErrors) {
            this.errors = this.errors.slice(0, this.maxErrors);
        }

        // Console logging for development
        console.error('Error logged:', errorInfo);

        // Send to analytics/monitoring service in production
        this.sendToMonitoring(errorInfo);
    }

    sendToMonitoring(errorInfo) {
        // In production, send to monitoring service
        if (window.gtag) {
            window.gtag('event', 'exception', {
                description: errorInfo.error?.message || errorInfo.reason,
                fatal: false
            });
        }
    }

    // Fetch wrapper with error handling
    async safeFetch(url, options = {}) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                return this.handleAPIError(response, `${options.method || 'GET'} ${url}`);
            }

            return response;
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
        }
    }

    // Form validation error display
    showFieldError(fieldId, message) {
        const field = document.getElementById(fieldId);
        if (!field) return;

        // Remove existing error
        this.clearFieldError(fieldId);

        // Add error class
        field.classList.add('is-invalid');

        // Create error element
        const errorEl = document.createElement('div');
        errorEl.className = 'invalid-feedback';
        errorEl.textContent = message;
        errorEl.id = `${fieldId}-error`;

        // Insert after field
        field.parentNode.insertBefore(errorEl, field.nextSibling);
    }

    clearFieldError(fieldId) {
        const field = document.getElementById(fieldId);
        if (field) {
            field.classList.remove('is-invalid');
            const errorEl = document.getElementById(`${fieldId}-error`);
            if (errorEl) {
                errorEl.remove();
            }
        }
    }

    clearAllFieldErrors() {
        document.querySelectorAll('.is-invalid').forEach(field => {
            field.classList.remove('is-invalid');
        });
        document.querySelectorAll('.invalid-feedback').forEach(error => {
            error.remove();
        });
    }

    // Utility methods
    getLastAction() {
        // In a real implementation, this would track the last user action
        return null;
    }

    executeRetry(action) {
        // In a real implementation, this would re-execute the last action
        console.log('Retrying action:', action);
    }

    createErrorResponse(errorInfo) {
        return {
            ok: false,
            status: errorInfo.status,
            statusText: errorInfo.statusText,
            error: errorInfo
        };
    }

    // Debug methods
    getErrorHistory() {
        return this.errors;
    }

    clearErrorHistory() {
        this.errors = [];
    }
}

// Global instance
window.ErrorHandler = new ErrorHandler();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ErrorHandler;
}
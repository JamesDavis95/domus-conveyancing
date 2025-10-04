/**
 * Cookie Consent Management System
 * Provides GDPR-compliant cookie consent with granular controls
 */

class CookieConsentManager {
    constructor() {
        this.consentKey = 'domus_cookie_consent';
        this.consentData = this.loadConsent();
        this.categories = {
            necessary: {
                name: 'Necessary',
                description: 'Essential cookies for website functionality',
                required: true,
                cookies: ['session_id', 'csrf_token', 'auth_token']
            },
            analytics: {
                name: 'Analytics',
                description: 'Help us understand how visitors use our website',
                required: false,
                cookies: ['_ga', '_ga_*', '_gid', '_gat']
            },
            marketing: {
                name: 'Marketing',
                description: 'Used to track visitors across websites for advertising',
                required: false,
                cookies: ['_fbp', '_fbc', 'fr']
            },
            preferences: {
                name: 'Preferences',
                description: 'Remember your choices and personalize your experience',
                required: false,
                cookies: ['theme', 'language', 'dashboard_layout']
            }
        };

        this.init();
    }

    init() {
        this.createBannerHTML();
        this.bindEvents();
        
        // Show banner if consent not given
        if (!this.consentData.hasConsented) {
            this.showBanner();
        }

        // Apply current consent settings
        this.applyConsent();
    }

    loadConsent() {
        try {
            const stored = localStorage.getItem(this.consentKey);
            if (stored) {
                return JSON.parse(stored);
            }
        } catch (error) {
            console.warn('Failed to load cookie consent data:', error);
        }

        return {
            hasConsented: false,
            timestamp: null,
            version: '1.0',
            categories: {
                necessary: true,
                analytics: false,
                marketing: false,
                preferences: false
            }
        };
    }

    saveConsent() {
        try {
            this.consentData.timestamp = new Date().toISOString();
            localStorage.setItem(this.consentKey, JSON.stringify(this.consentData));
            
            // Also send to server for compliance records
            fetch('/api/consent/record', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(this.consentData)
            }).catch(console.warn);
        } catch (error) {
            console.warn('Failed to save cookie consent:', error);
        }
    }

    createBannerHTML() {
        const bannerHTML = `
            <div id="cookie-banner" class="cookie-banner" style="display: none;">
                <div class="cookie-banner-content">
                    <div class="cookie-banner-text">
                        <h3>
                            <i class="fas fa-cookie-bite me-2"></i>
                            Cookie Preferences
                        </h3>
                        <p>We use cookies to enhance your experience, analyze site usage, and personalize content. You can manage your preferences below.</p>
                    </div>
                    
                    <div class="cookie-banner-actions">
                        <button type="button" class="btn btn-outline-light btn-sm me-2" data-action="manage">
                            <i class="fas fa-cog me-1"></i>Manage Preferences
                        </button>
                        <button type="button" class="btn btn-secondary btn-sm me-2" data-action="reject">
                            Reject All
                        </button>
                        <button type="button" class="btn btn-success btn-sm" data-action="accept">
                            Accept All
                        </button>
                    </div>
                </div>
            </div>

            <div id="cookie-preferences-modal" class="modal fade" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                <i class="fas fa-cookie-bite me-2"></i>
                                Cookie Preferences
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        
                        <div class="modal-body">
                            <div class="mb-4">
                                <p>We use different types of cookies to enhance your experience. You can choose which categories to allow:</p>
                            </div>

                            <div class="cookie-categories">
                                ${this.renderCategorySettings()}
                            </div>

                            <div class="mt-4 p-3 bg-light rounded">
                                <h6>More Information</h6>
                                <p class="mb-2">For detailed information about our cookie usage, please see our:</p>
                                <ul class="list-unstyled">
                                    <li><a href="/privacy-policy" target="_blank">Privacy Policy</a></li>
                                    <li><a href="/cookie-policy" target="_blank">Cookie Policy</a></li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-outline-danger me-2" data-action="reject-modal">
                                Reject All
                            </button>
                            <button type="button" class="btn btn-success" data-action="save-preferences">
                                Save Preferences
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Add styles
        const styleHTML = `
            <style>
                .cookie-banner {
                    position: fixed;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%);
                    color: white;
                    padding: 1rem;
                    box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
                    z-index: 9999;
                    border-top: 3px solid rgba(255,255,255,0.2);
                }

                .cookie-banner-content {
                    max-width: 1200px;
                    margin: 0 auto;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 2rem;
                }

                .cookie-banner-text h3 {
                    margin: 0 0 0.5rem 0;
                    font-size: 1.25rem;
                    font-weight: 600;
                }

                .cookie-banner-text p {
                    margin: 0;
                    opacity: 0.9;
                    line-height: 1.4;
                }

                .cookie-banner-actions {
                    display: flex;
                    flex-wrap: nowrap;
                    gap: 0.5rem;
                }

                .cookie-category {
                    border: 1px solid #dee2e6;
                    border-radius: 0.375rem;
                    margin-bottom: 1rem;
                    overflow: hidden;
                }

                .cookie-category-header {
                    background: #f8f9fa;
                    padding: 1rem;
                    border-bottom: 1px solid #dee2e6;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }

                .cookie-category-body {
                    padding: 1rem;
                }

                .cookie-category-required {
                    background: #e3f2fd;
                    border-color: #2196f3;
                }

                .cookie-list {
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                    font-size: 0.875rem;
                    background: #f8f9fa;
                    padding: 0.5rem;
                    border-radius: 0.25rem;
                    margin-top: 0.5rem;
                }

                @media (max-width: 768px) {
                    .cookie-banner-content {
                        flex-direction: column;
                        text-align: center;
                        gap: 1rem;
                    }
                    
                    .cookie-banner-actions {
                        justify-content: center;
                        flex-wrap: wrap;
                    }
                }

                /* Animation for banner appearance */
                .cookie-banner {
                    animation: slideUp 0.3s ease-out;
                }

                @keyframes slideUp {
                    from {
                        transform: translateY(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
            </style>
        `;

        // Inject into page
        document.head.insertAdjacentHTML('beforeend', styleHTML);
        document.body.insertAdjacentHTML('beforeend', bannerHTML);
    }

    renderCategorySettings() {
        return Object.entries(this.categories).map(([key, category]) => {
            const isRequired = category.required;
            const isEnabled = this.consentData.categories[key];
            
            return `
                <div class="cookie-category ${isRequired ? 'cookie-category-required' : ''}">
                    <div class="cookie-category-header">
                        <div>
                            <h6 class="mb-1">
                                ${category.name}
                                ${isRequired ? '<span class="badge bg-primary ms-2">Required</span>' : ''}
                            </h6>
                            <small class="text-muted">${category.description}</small>
                        </div>
                        <div class="form-check form-switch">
                            <input 
                                class="form-check-input" 
                                type="checkbox" 
                                id="cookie-${key}"
                                data-category="${key}"
                                ${isEnabled ? 'checked' : ''}
                                ${isRequired ? 'disabled' : ''}
                            >
                            <label class="form-check-label" for="cookie-${key}">
                                ${isEnabled || isRequired ? 'Enabled' : 'Disabled'}
                            </label>
                        </div>
                    </div>
                    <div class="cookie-category-body">
                        <p><strong>Cookies used:</strong></p>
                        <div class="cookie-list">
                            ${category.cookies.join(', ')}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    bindEvents() {
        // Banner action buttons
        document.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            
            switch (action) {
                case 'accept':
                    this.acceptAll();
                    break;
                case 'reject':
                    this.rejectAll();
                    break;
                case 'manage':
                    this.showPreferences();
                    break;
                case 'save-preferences':
                    this.savePreferences();
                    break;
                case 'reject-modal':
                    this.rejectAll();
                    break;
            }
        });

        // Category toggle switches
        document.addEventListener('change', (e) => {
            if (e.target.dataset.category) {
                const category = e.target.dataset.category;
                const label = e.target.nextElementSibling;
                label.textContent = e.target.checked ? 'Enabled' : 'Disabled';
            }
        });
    }

    showBanner() {
        const banner = document.getElementById('cookie-banner');
        if (banner) {
            banner.style.display = 'block';
        }
    }

    hideBanner() {
        const banner = document.getElementById('cookie-banner');
        if (banner) {
            banner.style.display = 'none';
        }
    }

    showPreferences() {
        // Update modal content with current settings
        const modalBody = document.querySelector('#cookie-preferences-modal .modal-body');
        const categoriesContainer = modalBody.querySelector('.cookie-categories');
        categoriesContainer.innerHTML = this.renderCategorySettings();

        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('cookie-preferences-modal'));
        modal.show();
    }

    acceptAll() {
        // Enable all categories
        Object.keys(this.categories).forEach(category => {
            this.consentData.categories[category] = true;
        });

        this.consentData.hasConsented = true;
        this.saveConsent();
        this.applyConsent();
        this.hideBanner();

        this.showToast('All cookies accepted', 'success');
    }

    rejectAll() {
        // Only keep necessary cookies
        Object.keys(this.categories).forEach(category => {
            this.consentData.categories[category] = this.categories[category].required;
        });

        this.consentData.hasConsented = true;
        this.saveConsent();
        this.applyConsent();
        this.hideBanner();

        // Close modal if open
        const modal = bootstrap.Modal.getInstance(document.getElementById('cookie-preferences-modal'));
        if (modal) {
            modal.hide();
        }

        this.showToast('Only necessary cookies accepted', 'info');
    }

    savePreferences() {
        // Get checkbox states
        Object.keys(this.categories).forEach(category => {
            const checkbox = document.getElementById(`cookie-${category}`);
            if (checkbox && !checkbox.disabled) {
                this.consentData.categories[category] = checkbox.checked;
            }
        });

        this.consentData.hasConsented = true;
        this.saveConsent();
        this.applyConsent();
        this.hideBanner();

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('cookie-preferences-modal'));
        if (modal) {
            modal.hide();
        }

        this.showToast('Cookie preferences saved', 'success');
    }

    applyConsent() {
        // Analytics cookies
        if (this.consentData.categories.analytics) {
            this.enableGoogleAnalytics();
        } else {
            this.disableGoogleAnalytics();
        }

        // Marketing cookies
        if (this.consentData.categories.marketing) {
            this.enableMarketingPixels();
        } else {
            this.disableMarketingPixels();
        }

        // Preferences cookies
        if (!this.consentData.categories.preferences) {
            this.clearPreferenceCookies();
        }

        // Send consent data to server
        this.updateServerConsent();
    }

    enableGoogleAnalytics() {
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'analytics_storage': 'granted'
            });
        }
    }

    disableGoogleAnalytics() {
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'analytics_storage': 'denied'
            });
        }
        
        // Clear existing GA cookies
        this.clearCookiesByPattern(/^_ga/);
    }

    enableMarketingPixels() {
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'ad_storage': 'granted'
            });
        }
    }

    disableMarketingPixels() {
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'ad_storage': 'denied'
            });
        }
        
        // Clear marketing cookies
        this.clearCookiesByPattern(/^_fbp|^_fbc|^fr$/);
    }

    clearPreferenceCookies() {
        const preferenceCookies = this.categories.preferences.cookies;
        preferenceCookies.forEach(cookie => {
            this.deleteCookie(cookie);
        });
    }

    clearCookiesByPattern(pattern) {
        document.cookie.split(';').forEach(cookie => {
            const name = cookie.split('=')[0].trim();
            if (pattern.test(name)) {
                this.deleteCookie(name);
            }
        });
    }

    deleteCookie(name, domain = null, path = '/') {
        let cookieString = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=${path};`;
        if (domain) {
            cookieString += ` domain=${domain};`;
        }
        document.cookie = cookieString;
    }

    updateServerConsent() {
        fetch('/api/consent/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                consent: this.consentData,
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString()
            })
        }).catch(console.warn);
    }

    getCSRFToken() {
        return document.querySelector('meta[name=csrf-token]')?.getAttribute('content') || '';
    }

    showToast(message, type = 'info') {
        // Create toast if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            toastContainer.style.zIndex = '10000';
            document.body.appendChild(toastContainer);
        }

        const toastHTML = `
            <div class="toast" role="alert">
                <div class="toast-header">
                    <i class="fas fa-cookie-bite text-${type} me-2"></i>
                    <strong class="me-auto">Cookie Preferences</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        const toastElement = toastContainer.lastElementChild;
        const toast = new bootstrap.Toast(toastElement);
        toast.show();

        // Remove after hiding
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }

    // Public methods for manual consent management
    hasConsentFor(category) {
        return this.consentData.categories[category] === true;
    }

    getConsentData() {
        return { ...this.consentData };
    }

    resetConsent() {
        localStorage.removeItem(this.consentKey);
        location.reload();
    }

    showConsentManager() {
        this.showPreferences();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.cookieConsent = new CookieConsentManager();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CookieConsentManager;
}
/**
 * Empty States & Error UX Components
 * Uniform components for consistent user experience
 */

class EmptyStatesManager {
    constructor() {
        this.loadingStates = new Map();
        this.errorBoundaries = new Map();
        this.initializeStyles();
    }

    initializeStyles() {
        // Inject empty states CSS if not already present
        if (!document.getElementById('empty-states-styles')) {
            const styles = document.createElement('style');
            styles.id = 'empty-states-styles';
            styles.textContent = `
                .empty-state {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    padding: 3rem 2rem;
                    text-align: center;
                    min-height: 200px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border: 2px dashed #dee2e6;
                }

                .empty-state-icon {
                    font-size: 3rem;
                    color: #6c757d;
                    margin-bottom: 1rem;
                }

                .empty-state-title {
                    font-size: 1.25rem;
                    font-weight: 600;
                    color: #495057;
                    margin-bottom: 0.5rem;
                }

                .empty-state-description {
                    color: #6c757d;
                    margin-bottom: 1.5rem;
                    max-width: 400px;
                }

                .empty-state-action {
                    margin-top: 0.5rem;
                }

                .skeleton-loader {
                    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                    background-size: 200% 100%;
                    animation: loading 1.5s infinite;
                    border-radius: 4px;
                }

                @keyframes loading {
                    0% { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                }

                .skeleton-text {
                    height: 1rem;
                    margin-bottom: 0.5rem;
                }

                .skeleton-text:last-child {
                    margin-bottom: 0;
                }

                .skeleton-title {
                    height: 1.5rem;
                    width: 60%;
                    margin-bottom: 1rem;
                }

                .skeleton-card {
                    padding: 1rem;
                    border: 1px solid #dee2e6;
                    border-radius: 0.375rem;
                    margin-bottom: 1rem;
                }

                .error-boundary {
                    padding: 2rem;
                    text-align: center;
                    border: 2px solid #f8d7da;
                    border-radius: 8px;
                    background: #f8d7da;
                    color: #721c24;
                }

                .error-boundary-icon {
                    font-size: 2.5rem;
                    margin-bottom: 1rem;
                }

                .retry-button {
                    margin-top: 1rem;
                }

                .empty-state.compact {
                    min-height: 120px;
                    padding: 2rem 1rem;
                }

                .empty-state.compact .empty-state-icon {
                    font-size: 2rem;
                    margin-bottom: 0.5rem;
                }

                .empty-state.compact .empty-state-title {
                    font-size: 1rem;
                    margin-bottom: 0.25rem;
                }

                .empty-state.compact .empty-state-description {
                    font-size: 0.875rem;
                    margin-bottom: 1rem;
                }
            `;
            document.head.appendChild(styles);
        }
    }

    // Empty state templates
    createEmptyState(config) {
        const {
            icon = 'fas fa-inbox',
            title = 'No items found',
            description = 'Get started by adding your first item.',
            actionText = null,
            actionCallback = null,
            compact = false
        } = config;

        const container = document.createElement('div');
        container.className = `empty-state ${compact ? 'compact' : ''}`;

        container.innerHTML = `
            <div class="empty-state-icon">
                <i class="${icon}"></i>
            </div>
            <h4 class="empty-state-title">${title}</h4>
            <p class="empty-state-description">${description}</p>
            ${actionText ? `
                <div class="empty-state-action">
                    <button class="btn btn-primary empty-state-btn">${actionText}</button>
                </div>
            ` : ''}
        `;

        if (actionText && actionCallback) {
            const button = container.querySelector('.empty-state-btn');
            button.addEventListener('click', actionCallback);
        }

        return container;
    }

    // Project-specific empty states
    createProjectsEmptyState() {
        return this.createEmptyState({
            icon: 'fas fa-building',
            title: 'No projects yet',
            description: 'Start your first planning project and unlock powerful AI-driven insights.',
            actionText: 'Create Project',
            actionCallback: () => window.location.href = '/projects/new'
        });
    }

    createDocumentsEmptyState() {
        return this.createEmptyState({
            icon: 'fas fa-file-pdf',
            title: 'No documents uploaded',
            description: 'Upload your planning documents to get started with AI analysis.',
            actionText: 'Upload Documents',
            actionCallback: () => document.getElementById('file-upload')?.click()
        });
    }

    createAnalysisEmptyState() {
        return this.createEmptyState({
            icon: 'fas fa-chart-line',
            title: 'No analysis available',
            description: 'Upload documents and generate your first AI-powered planning analysis.',
            actionText: 'Start Analysis',
            actionCallback: () => this.triggerAnalysis?.()
        });
    }

    createSubmissionsEmptyState() {
        return this.createEmptyState({
            icon: 'fas fa-paper-plane',
            title: 'No submissions created',
            description: 'Create your first submission package when your analysis is complete.',
            compact: true
        });
    }

    createSearchEmptyState(query) {
        return this.createEmptyState({
            icon: 'fas fa-search',
            title: 'No results found',
            description: `We couldn't find any results for "${query}". Try adjusting your search terms.`,
            compact: true
        });
    }

    createNetworkErrorState() {
        return this.createEmptyState({
            icon: 'fas fa-wifi',
            title: 'Connection problem',
            description: 'Check your internet connection and try again.',
            actionText: 'Retry',
            actionCallback: () => window.location.reload()
        });
    }

    // Skeleton loaders
    createSkeletonLoader(config) {
        const {
            type = 'card',
            count = 3,
            height = null
        } = config;

        const container = document.createElement('div');

        switch (type) {
            case 'card':
                for (let i = 0; i < count; i++) {
                    const card = document.createElement('div');
                    card.className = 'skeleton-card';
                    card.innerHTML = `
                        <div class="skeleton-loader skeleton-title"></div>
                        <div class="skeleton-loader skeleton-text"></div>
                        <div class="skeleton-loader skeleton-text" style="width: 80%;"></div>
                        <div class="skeleton-loader skeleton-text" style="width: 60%;"></div>
                    `;
                    container.appendChild(card);
                }
                break;

            case 'list':
                for (let i = 0; i < count; i++) {
                    const item = document.createElement('div');
                    item.className = 'd-flex align-items-center mb-3';
                    item.innerHTML = `
                        <div class="skeleton-loader rounded-circle me-3" style="width: 40px; height: 40px;"></div>
                        <div class="flex-grow-1">
                            <div class="skeleton-loader skeleton-text" style="width: 40%;"></div>
                            <div class="skeleton-loader skeleton-text" style="width: 60%;"></div>
                        </div>
                    `;
                    container.appendChild(item);
                }
                break;

            case 'table':
                const table = document.createElement('table');
                table.className = 'table';
                for (let i = 0; i < count; i++) {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><div class="skeleton-loader skeleton-text"></div></td>
                        <td><div class="skeleton-loader skeleton-text" style="width: 70%;"></div></td>
                        <td><div class="skeleton-loader skeleton-text" style="width: 50%;"></div></td>
                        <td><div class="skeleton-loader skeleton-text" style="width: 30%;"></div></td>
                    `;
                    table.appendChild(row);
                }
                container.appendChild(table);
                break;

            case 'text':
                for (let i = 0; i < count; i++) {
                    const text = document.createElement('div');
                    text.className = 'skeleton-loader skeleton-text mb-2';
                    if (height) text.style.height = height;
                    container.appendChild(text);
                }
                break;
        }

        return container;
    }

    // Error boundaries
    createErrorBoundary(error, componentName = 'Component') {
        const container = document.createElement('div');
        container.className = 'error-boundary';

        container.innerHTML = `
            <div class="error-boundary-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h5>Something went wrong</h5>
            <p>We encountered an error in the ${componentName} component.</p>
            <details style="text-align: left; margin-top: 1rem;">
                <summary>Error details</summary>
                <pre style="font-size: 0.8rem; margin-top: 0.5rem;">${error.message || error}</pre>
            </details>
            <button class="btn btn-outline-danger retry-button" onclick="window.location.reload()">
                <i class="fas fa-redo me-1"></i> Reload Page
            </button>
        `;

        return container;
    }

    // Loading state management
    showLoading(containerId, config = {}) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const {
            type = 'card',
            count = 3,
            message = 'Loading...'
        } = config;

        this.loadingStates.set(containerId, container.innerHTML);

        if (config.showMessage) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary mb-3"></div>
                    <p class="text-muted">${message}</p>
                </div>
            `;
        } else {
            const skeleton = this.createSkeletonLoader({ type, count });
            container.innerHTML = '';
            container.appendChild(skeleton);
        }
    }

    hideLoading(containerId, content = null) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (content) {
            container.innerHTML = content;
        } else {
            const originalContent = this.loadingStates.get(containerId);
            if (originalContent) {
                container.innerHTML = originalContent;
                this.loadingStates.delete(containerId);
            }
        }
    }

    // Show empty state in container
    showEmptyState(containerId, config) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const emptyState = this.createEmptyState(config);
        container.innerHTML = '';
        container.appendChild(emptyState);
    }

    // Show error boundary in container
    showError(containerId, error, componentName) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const errorBoundary = this.createErrorBoundary(error, componentName);
        container.innerHTML = '';
        container.appendChild(errorBoundary);
    }

    // Utility methods
    wrapWithErrorBoundary(element, componentName) {
        try {
            return element;
        } catch (error) {
            console.error(`Error in ${componentName}:`, error);
            return this.createErrorBoundary(error, componentName);
        }
    }

    // Auto-retry functionality
    createAutoRetry(callback, maxRetries = 3, delay = 1000) {
        let retries = 0;
        
        const attempt = async () => {
            try {
                return await callback();
            } catch (error) {
                retries++;
                if (retries < maxRetries) {
                    console.log(`Attempt ${retries} failed, retrying in ${delay}ms...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                    return attempt();
                } else {
                    throw error;
                }
            }
        };

        return attempt();
    }
}

// Global instance
window.EmptyStates = new EmptyStatesManager();

// jQuery integration (if available)
if (typeof $ !== 'undefined') {
    $.fn.showEmptyState = function(config) {
        return this.each(function() {
            const emptyState = window.EmptyStates.createEmptyState(config);
            $(this).html('').append(emptyState);
        });
    };

    $.fn.showLoading = function(config = {}) {
        return this.each(function() {
            const id = this.id || 'temp-' + Math.random().toString(36).substr(2, 9);
            this.id = id;
            window.EmptyStates.showLoading(id, config);
        });
    };

    $.fn.hideLoading = function(content = null) {
        return this.each(function() {
            if (this.id) {
                window.EmptyStates.hideLoading(this.id, content);
            }
        });
    };
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EmptyStatesManager;
}
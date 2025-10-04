/**
 * Error Boundary Components
 * React error boundaries for graceful error handling and recovery
 */

import React from 'react';

// Main Error Boundary Class Component
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      errorId: Math.random().toString(36).substr(2, 9)
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('Error Boundary caught an error:', error, errorInfo);
    
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Report error to monitoring service (if available)
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Send to error reporting service
    this.reportError(error, errorInfo);
  }

  reportError = (error, errorInfo) => {
    try {
      // Send error to backend logging endpoint
      fetch('/api/errors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error: {
            message: error.message,
            stack: error.stack,
            name: error.name
          },
          errorInfo: errorInfo,
          errorId: this.state.errorId,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href
        })
      }).catch(reportingError => {
        console.error('Failed to report error:', reportingError);
      });
    } catch (reportingError) {
      console.error('Error reporting failed:', reportingError);
    }
  };

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      errorId: null
    });
  };

  handleReportIssue = () => {
    const errorDetails = {
      message: this.state.error?.message || 'Unknown error',
      errorId: this.state.errorId,
      timestamp: new Date().toISOString()
    };

    // Open support ticket or email
    const subject = encodeURIComponent(`Error Report - ID: ${errorDetails.errorId}`);
    const body = encodeURIComponent(`
Error Details:
- Error ID: ${errorDetails.errorId}
- Message: ${errorDetails.message}
- Time: ${errorDetails.timestamp}
- Page: ${window.location.href}

Please describe what you were doing when this error occurred:

    `.trim());

    window.open(`mailto:support@domusconveyancing.com?subject=${subject}&body=${body}`);
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback(
          this.state.error,
          this.state.errorInfo,
          this.handleRetry,
          this.handleReportIssue
        );
      }

      // Default error UI
      return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
          <div className="sm:mx-auto sm:w-full sm:max-w-md">
            <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
              <div className="text-center">
                <div className="mx-auto w-16 h-16 text-red-500 mb-4">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.664-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
                  </svg>
                </div>
                
                <h2 className="text-lg font-medium text-gray-900 mb-2">
                  Something went wrong
                </h2>
                
                <p className="text-sm text-gray-500 mb-6">
                  We encountered an unexpected error. Our team has been notified and we're working to fix it.
                </p>

                {this.state.errorId && (
                  <p className="text-xs text-gray-400 mb-6 font-mono">
                    Error ID: {this.state.errorId}
                  </p>
                )}

                <div className="flex flex-col space-y-3">
                  <button
                    onClick={this.handleRetry}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Try Again
                  </button>
                  
                  <button
                    onClick={this.handleReportIssue}
                    className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Report Issue
                  </button>
                  
                  <button
                    onClick={() => window.location.href = '/'}
                    className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Go Home
                  </button>
                </div>

                {process.env.NODE_ENV === 'development' && this.state.error && (
                  <details className="mt-6 text-left">
                    <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                      Error Details (Development)
                    </summary>
                    <div className="mt-2 p-3 bg-gray-100 rounded text-xs font-mono text-gray-800 overflow-auto max-h-48">
                      <p className="font-bold mb-2">Error:</p>
                      <p className="mb-2">{this.state.error.toString()}</p>
                      <p className="font-bold mb-2">Stack Trace:</p>
                      <pre className="whitespace-pre-wrap">{this.state.error.stack}</pre>
                      {this.state.errorInfo && (
                        <>
                          <p className="font-bold mb-2 mt-4">Component Stack:</p>
                          <pre className="whitespace-pre-wrap">{this.state.errorInfo.componentStack}</pre>
                        </>
                      )}
                    </div>
                  </details>
                )}
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Functional component wrapper for easier usage
export const withErrorBoundary = (Component, errorBoundaryProps = {}) => {
  const WrappedComponent = (props) => (
    <ErrorBoundary {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundary>
  );
  
  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
  return WrappedComponent;
};

// Async Error Boundary for handling async operations
export class AsyncErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      isRetrying: false
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Async Error Boundary caught an error:', error, errorInfo);
    this.setState({ error });
    
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = async () => {
    this.setState({ isRetrying: true });
    
    try {
      if (this.props.onRetry) {
        await this.props.onRetry();
      }
      
      this.setState({
        hasError: false,
        error: null,
        isRetrying: false
      });
    } catch (retryError) {
      console.error('Retry failed:', retryError);
      this.setState({
        error: retryError,
        isRetrying: false
      });
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback(
          this.state.error,
          this.handleRetry,
          this.state.isRetrying
        );
      }

      return (
        <div className="text-center py-8">
          <div className="mx-auto w-16 h-16 text-red-500 mb-4">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.664-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Operation Failed
          </h3>
          
          <p className="text-sm text-gray-500 mb-6">
            {this.state.error?.message || 'An unexpected error occurred during this operation.'}
          </p>
          
          <button
            onClick={this.handleRetry}
            disabled={this.state.isRetrying}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {this.state.isRetrying ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Retrying...
              </>
            ) : (
              'Try Again'
            )}
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Route Error Boundary for handling route-level errors
export const RouteErrorBoundary = ({ children }) => {
  return (
    <ErrorBoundary
      fallback={(error, errorInfo, retry, reportIssue) => (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
          <div className="sm:mx-auto sm:w-full sm:max-w-lg">
            <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
              <div className="text-center">
                <div className="mx-auto w-20 h-20 text-red-500 mb-6">
                  <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                
                <h1 className="text-2xl font-bold text-gray-900 mb-4">
                  Page Error
                </h1>
                
                <p className="text-gray-600 mb-8">
                  This page encountered an error and couldn't be loaded properly.
                </p>

                <div className="space-y-4">
                  <button
                    onClick={retry}
                    className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Reload Page
                  </button>
                  
                  <div className="flex space-x-4">
                    <button
                      onClick={() => window.history.back()}
                      className="flex-1 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Go Back
                    </button>
                    
                    <button
                      onClick={() => window.location.href = '/'}
                      className="flex-1 py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Home
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    >
      {children}
    </ErrorBoundary>
  );
};

// Component Error Boundary for wrapping individual components
export const ComponentErrorBoundary = ({ children, componentName = 'Component' }) => {
  return (
    <ErrorBoundary
      fallback={(error, errorInfo, retry) => (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.664-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-red-800">
                {componentName} Error
              </h3>
              <p className="mt-1 text-sm text-red-700">
                This component failed to load. 
              </p>
              <div className="mt-3">
                <button
                  onClick={retry}
                  className="text-sm font-medium text-red-800 hover:text-red-600 underline"
                >
                  Try again
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    >
      {children}
    </ErrorBoundary>
  );
};
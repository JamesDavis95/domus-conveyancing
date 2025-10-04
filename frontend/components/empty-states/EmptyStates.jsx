/**
 * Empty States Components
 * React components for displaying empty states with proper messaging and actions
 */

import React from 'react';

// Generic Empty State Component
export const EmptyState = ({ 
  icon,
  title, 
  description, 
  action = null,
  className = ''
}) => {
  return (
    <div className={`text-center py-12 px-4 ${className}`}>
      {icon && (
        <div className="mx-auto w-24 h-24 text-gray-300 mb-6">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-medium text-gray-900 mb-2">
        {title}
      </h3>
      <p className="text-gray-500 mb-6 max-w-md mx-auto">
        {description}
      </p>
      {action && (
        <div className="flex justify-center">
          {action}
        </div>
      )}
    </div>
  );
};

// No Transactions Empty State
export const NoTransactionsEmpty = ({ onStartTransaction }) => {
  const icon = (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  );

  return (
    <EmptyState
      icon={icon}
      title="No Active Transactions"
      description="You don't have any property transactions in progress. Start a new conveyancing matter to get started."
      action={
        <button
          onClick={onStartTransaction}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Start New Transaction
        </button>
      }
    />
  );
};

// No Documents Empty State
export const NoDocumentsEmpty = ({ onUploadDocument, transactionType = 'transaction' }) => {
  const icon = (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );

  return (
    <EmptyState
      icon={icon}
      title="No Documents"
      description={`No documents have been uploaded for this ${transactionType} yet. Upload your first document to get started.`}
      action={
        <button
          onClick={onUploadDocument}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          Upload Document
        </button>
      }
    />
  );
};

// No Messages Empty State
export const NoMessagesEmpty = ({ onSendMessage }) => {
  const icon = (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  );

  return (
    <EmptyState
      icon={icon}
      title="No Messages"
      description="Start a conversation with your solicitor or other parties involved in your transaction."
      action={
        <button
          onClick={onSendMessage}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Send Message
        </button>
      }
    />
  );
};

// No Search Results Empty State
export const NoSearchResultsEmpty = ({ searchTerm, onClearSearch }) => {
  const icon = (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  );

  return (
    <EmptyState
      icon={icon}
      title="No Results Found"
      description={`We couldn't find any results for "${searchTerm}". Try adjusting your search terms or filters.`}
      action={
        <button
          onClick={onClearSearch}
          className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Clear Search
        </button>
      }
    />
  );
};

// Error State (Empty state for errors)
export const ErrorState = ({ 
  title = "Something went wrong", 
  description = "We encountered an error while loading this content.",
  onRetry = null,
  onReportIssue = null
}) => {
  const icon = (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full text-red-300">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.664-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z" />
    </svg>
  );

  return (
    <EmptyState
      icon={icon}
      title={title}
      description={description}
      action={
        <div className="flex flex-col sm:flex-row gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Try Again
            </button>
          )}
          {onReportIssue && (
            <button
              onClick={onReportIssue}
              className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Report Issue
            </button>
          )}
        </div>
      }
    />
  );
};

// Network Error State
export const NetworkErrorState = ({ onRetry }) => {
  const icon = (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full text-red-300">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 2.25A9.75 9.75 0 102.25 12 9.75 9.75 0 0012 2.25z" />
    </svg>
  );

  return (
    <EmptyState
      icon={icon}
      title="Connection Problem"
      description="We're having trouble connecting to our servers. Please check your internet connection and try again."
      action={
        <button
          onClick={onRetry}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg className="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Retry Connection
        </button>
      }
    />
  );
};

// Permission Denied Empty State
export const PermissionDeniedState = ({ onContactSupport }) => {
  const icon = (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full text-yellow-300">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
    </svg>
  );

  return (
    <EmptyState
      icon={icon}
      title="Access Denied"
      description="You don't have permission to view this content. Contact your administrator if you believe this is an error."
      action={
        onContactSupport && (
          <button
            onClick={onContactSupport}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Contact Support
          </button>
        )
      }
    />
  );
};

// No Notifications Empty State
export const NoNotificationsEmpty = () => {
  const icon = (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 17h5l-5 5v-5zM11 19H6.828a2 2 0 01-1.414-.586l-4.828-4.828A2 2 0 010 12.172V6a2 2 0 012-2h4.828a2 2 0 011.414.586L13.657 10H20a2 2 0 012 2v6a2 2 0 01-2 2h-9z" />
    </svg>
  );

  return (
    <EmptyState
      icon={icon}
      title="No Notifications"
      description="You're all caught up! We'll notify you when there are updates on your transactions."
      className="py-8"
    />
  );
};

// Coming Soon Empty State
export const ComingSoonState = ({ featureName, description }) => {
  const icon = (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full text-blue-300">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );

  return (
    <EmptyState
      icon={icon}
      title={`${featureName} Coming Soon`}
      description={description || `We're working hard to bring you ${featureName}. Stay tuned for updates!`}
      className="py-8"
    />
  );
};

// Maintenance Mode Empty State
export const MaintenanceState = ({ estimatedTime }) => {
  const icon = (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full text-orange-300">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );

  return (
    <EmptyState
      icon={icon}
      title="System Maintenance"
      description={`We're performing scheduled maintenance to improve your experience. ${estimatedTime ? `Estimated completion: ${estimatedTime}` : 'We\'ll be back shortly.'}`}
      className="py-8"
    />
  );
};

// Filter Results Empty State
export const NoFilterResultsEmpty = ({ onClearFilters, filterCount = 0 }) => {
  const icon = (
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" className="w-full h-full">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
    </svg>
  );

  return (
    <EmptyState
      icon={icon}
      title="No Matches Found"
      description={`No items match your current filters${filterCount > 0 ? ` (${filterCount} active)` : ''}. Try adjusting or clearing your filters to see more results.`}
      action={
        <button
          onClick={onClearFilters}
          className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Clear All Filters
        </button>
      }
    />
  );
};
/**
 * Loading States and Skeletons
 * React components for loading states and skeleton screens
 */

import React from 'react';

// Loading Spinner Component
export const LoadingSpinner = ({ size = 'medium', color = 'primary' }) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8', 
    large: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  const colorClasses = {
    primary: 'text-blue-600',
    secondary: 'text-gray-600',
    white: 'text-white',
    success: 'text-green-600',
    danger: 'text-red-600'
  };

  return (
    <div className={`inline-block animate-spin rounded-full border-2 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite] ${sizeClasses[size]} ${colorClasses[color]}`}>
      <span className="!absolute !-m-px !h-px !w-px !overflow-hidden !whitespace-nowrap !border-0 !p-0 ![clip:rect(0,0,0,0)]">
        Loading...
      </span>
    </div>
  );
};

// Loading Overlay Component
export const LoadingOverlay = ({ isLoading, children, message = 'Loading...' }) => {
  if (!isLoading) {
    return children;
  }

  return (
    <div className="relative">
      {children}
      <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        <div className="text-center">
          <LoadingSpinner size="large" />
          <p className="mt-4 text-gray-600 font-medium">{message}</p>
        </div>
      </div>
    </div>
  );
};

// Skeleton Components for different content types
export const SkeletonText = ({ lines = 1, className = '' }) => {
  return (
    <div className={`animate-pulse ${className}`}>
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className={`bg-gray-200 rounded h-4 mb-2 ${
            index === lines - 1 && lines > 1 ? 'w-3/4' : 'w-full'
          }`}
        />
      ))}
    </div>
  );
};

export const SkeletonCard = ({ className = '' }) => {
  return (
    <div className={`animate-pulse ${className}`}>
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center space-x-4 mb-4">
          <div className="bg-gray-200 rounded-full w-12 h-12"></div>
          <div className="flex-1">
            <div className="bg-gray-200 rounded h-4 w-3/4 mb-2"></div>
            <div className="bg-gray-200 rounded h-3 w-1/2"></div>
          </div>
        </div>
        <div className="space-y-2">
          <div className="bg-gray-200 rounded h-3 w-full"></div>
          <div className="bg-gray-200 rounded h-3 w-full"></div>
          <div className="bg-gray-200 rounded h-3 w-2/3"></div>
        </div>
      </div>
    </div>
  );
};

export const SkeletonTable = ({ rows = 5, columns = 4 }) => {
  return (
    <div className="animate-pulse">
      <div className="bg-white shadow rounded-lg overflow-hidden">
        {/* Table Header */}
        <div className="bg-gray-50 px-6 py-4 border-b">
          <div className="flex space-x-4">
            {Array.from({ length: columns }).map((_, index) => (
              <div key={index} className="flex-1">
                <div className="bg-gray-200 rounded h-4 w-3/4"></div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Table Rows */}
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="px-6 py-4 border-b border-gray-200">
            <div className="flex space-x-4">
              {Array.from({ length: columns }).map((_, colIndex) => (
                <div key={colIndex} className="flex-1">
                  <div className="bg-gray-200 rounded h-4 w-full"></div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Property Transaction Skeleton
export const PropertyTransactionSkeleton = () => {
  return (
    <div className="animate-pulse">
      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* Property Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="bg-gray-200 rounded-lg w-16 h-16"></div>
            <div>
              <div className="bg-gray-200 rounded h-6 w-48 mb-2"></div>
              <div className="bg-gray-200 rounded h-4 w-32"></div>
            </div>
          </div>
          <div className="bg-gray-200 rounded-full h-8 w-24"></div>
        </div>

        {/* Progress Bar */}
        <div className="mb-6">
          <div className="bg-gray-200 rounded h-2 w-full"></div>
        </div>

        {/* Transaction Details */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="bg-gray-200 rounded h-4 w-20 mb-2"></div>
            <div className="bg-gray-200 rounded h-6 w-32"></div>
          </div>
          <div>
            <div className="bg-gray-200 rounded h-4 w-24 mb-2"></div>
            <div className="bg-gray-200 rounded h-6 w-28"></div>
          </div>
          <div>
            <div className="bg-gray-200 rounded h-4 w-16 mb-2"></div>
            <div className="bg-gray-200 rounded h-6 w-36"></div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="mt-6">
          <div className="bg-gray-200 rounded h-5 w-32 mb-4"></div>
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="flex items-center space-x-3">
                <div className="bg-gray-200 rounded-full w-8 h-8"></div>
                <div className="flex-1">
                  <div className="bg-gray-200 rounded h-4 w-full mb-1"></div>
                  <div className="bg-gray-200 rounded h-3 w-2/3"></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Document List Skeleton
export const DocumentListSkeleton = ({ count = 5 }) => {
  return (
    <div className="animate-pulse space-y-4">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center space-x-4">
            <div className="bg-gray-200 rounded w-10 h-10"></div>
            <div className="flex-1">
              <div className="bg-gray-200 rounded h-4 w-3/4 mb-2"></div>
              <div className="flex items-center space-x-4">
                <div className="bg-gray-200 rounded h-3 w-20"></div>
                <div className="bg-gray-200 rounded h-3 w-16"></div>
                <div className="bg-gray-200 rounded h-3 w-24"></div>
              </div>
            </div>
            <div className="bg-gray-200 rounded-full h-8 w-20"></div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Chat/Messages Skeleton
export const ChatSkeleton = () => {
  return (
    <div className="animate-pulse space-y-4">
      {Array.from({ length: 6 }).map((_, index) => (
        <div key={index} className={`flex ${index % 2 === 0 ? 'justify-start' : 'justify-end'}`}>
          <div className={`max-w-xs lg:max-w-md ${index % 2 === 0 ? 'bg-gray-200' : 'bg-blue-200'} rounded-lg p-3`}>
            <div className="bg-gray-300 rounded h-3 w-full mb-1"></div>
            <div className="bg-gray-300 rounded h-3 w-2/3"></div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Form Skeleton
export const FormSkeleton = ({ fields = 5 }) => {
  return (
    <div className="animate-pulse space-y-6">
      {Array.from({ length: fields }).map((_, index) => (
        <div key={index}>
          <div className="bg-gray-200 rounded h-4 w-24 mb-2"></div>
          <div className="bg-gray-200 rounded-md h-10 w-full"></div>
        </div>
      ))}
      <div className="flex justify-end space-x-4 pt-4">
        <div className="bg-gray-200 rounded h-10 w-20"></div>
        <div className="bg-gray-200 rounded h-10 w-24"></div>
      </div>
    </div>
  );
};

// Dashboard Skeleton
export const DashboardSkeleton = () => {
  return (
    <div className="animate-pulse">
      {/* Header */}
      <div className="mb-8">
        <div className="bg-gray-200 rounded h-8 w-64 mb-2"></div>
        <div className="bg-gray-200 rounded h-4 w-96"></div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="bg-gray-200 rounded-full w-12 h-12 mr-4"></div>
              <div>
                <div className="bg-gray-200 rounded h-4 w-16 mb-2"></div>
                <div className="bg-gray-200 rounded h-6 w-20"></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">
          <PropertyTransactionSkeleton />
          <SkeletonTable rows={3} columns={4} />
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="bg-gray-200 rounded h-5 w-32 mb-4"></div>
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className="bg-gray-200 rounded-full w-2 h-2"></div>
                  <div className="bg-gray-200 rounded h-4 flex-1"></div>
                </div>
              ))}
            </div>
          </div>
          
          <ChatSkeleton />
        </div>
      </div>
    </div>
  );
};

// Loading Button Component
export const LoadingButton = ({ 
  isLoading, 
  children, 
  className = '', 
  disabled = false,
  ...props 
}) => {
  return (
    <button
      className={`relative ${className} ${isLoading || disabled ? 'opacity-75 cursor-not-allowed' : ''}`}
      disabled={isLoading || disabled}
      {...props}
    >
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <LoadingSpinner size="small" color="white" />
        </div>
      )}
      <span className={isLoading ? 'invisible' : 'visible'}>
        {children}
      </span>
    </button>
  );
};

// Progressive Loading Component
export const ProgressiveLoader = ({ 
  steps, 
  currentStep, 
  isLoading = false,
  error = null 
}) => {
  return (
    <div className="max-w-md mx-auto">
      <div className="space-y-4">
        {steps.map((step, index) => {
          const isComplete = index < currentStep;
          const isCurrent = index === currentStep;
          const isPending = index > currentStep;

          return (
            <div key={index} className="flex items-center space-x-3">
              {/* Step Indicator */}
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                isComplete 
                  ? 'bg-green-500 text-white' 
                  : isCurrent && isLoading
                  ? 'bg-blue-500 text-white'
                  : isCurrent && error
                  ? 'bg-red-500 text-white'
                  : isCurrent
                  ? 'bg-blue-100 text-blue-600'
                  : 'bg-gray-100 text-gray-400'
              }`}>
                {isComplete ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : isCurrent && isLoading ? (
                  <LoadingSpinner size="small" color="white" />
                ) : isCurrent && error ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <span className="text-sm font-medium">{index + 1}</span>
                )}
              </div>

              {/* Step Content */}
              <div className="flex-1">
                <p className={`text-sm font-medium ${
                  isComplete 
                    ? 'text-green-600'
                    : isCurrent
                    ? error ? 'text-red-600' : 'text-blue-600'
                    : 'text-gray-400'
                }`}>
                  {step.title}
                </p>
                {step.description && (
                  <p className="text-xs text-gray-500 mt-1">
                    {step.description}
                  </p>
                )}
                {isCurrent && error && (
                  <p className="text-xs text-red-500 mt-1">
                    {error}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
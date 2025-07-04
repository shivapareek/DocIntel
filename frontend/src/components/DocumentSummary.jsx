import React, { useState } from 'react';
import { useDocument } from '../context/DocContext';

const DocumentSummary = () => {
  const { isUploaded, summary, fileName, isLoading } = useDocument();
  const [isExpanded, setIsExpanded] = useState(true);

  if (!isUploaded && !isLoading) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Document Summary</h2>
          <div className="animate-pulse">
            <div className="h-4 bg-gray-300 rounded w-20"></div>
          </div>
        </div>
        
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-300 rounded w-full"></div>
          <div className="h-4 bg-gray-300 rounded w-5/6"></div>
          <div className="h-4 bg-gray-300 rounded w-4/6"></div>
          <div className="h-4 bg-gray-300 rounded w-3/6"></div>
        </div>
      </div>
    );
  }

  if (!isUploaded || !summary) {
    return null;
  }

  const wordCount = summary.split(/\s+/).length;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <h2 className="text-xl font-semibold text-gray-900">Document Summary</h2>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            {wordCount} words
          </span>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-sm text-gray-600 hover:text-gray-800 font-medium flex items-center space-x-1"
        >
          <span>{isExpanded ? 'Collapse' : 'Expand'}</span>
          <span className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </button>
      </div>

      {isExpanded && (
        <div className="space-y-4">
          <div className="bg-gray-50 rounded-md p-4">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-sm font-medium text-gray-700">Source:</span>
              <span className="text-sm text-gray-600">{fileName}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">Generated:</span>
              <span className="text-sm text-gray-600">{new Date().toLocaleString()}</span>
            </div>
          </div>

          <div className="prose max-w-none">
            <div className="text-gray-800 leading-relaxed">
              {summary.split('\n').map((paragraph, index) => (
                <p key={index} className="mb-3 last:mb-0">
                  {paragraph}
                </p>
              ))}
            </div>
          </div>

          <div className="border-t pt-4">
            <div className="flex items-center justify-between text-sm text-gray-600">
              <div className="flex items-center space-x-4">
                <span className="flex items-center space-x-1">
                  <span>📊</span>
                  <span>Auto-generated summary</span>
                </span>
                <span className="flex items-center space-x-1">
                  <span>🎯</span>
                  <span>Key insights extracted</span>
                </span>
              </div>
              <div className="flex items-center space-x-1">
                <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                <span>Ready for questions</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {!isExpanded && (
        <div className="text-gray-600 text-sm">
          <p className="line-clamp-2">
            {summary.substring(0, 150)}...
          </p>
          <p className="mt-2 text-xs text-gray-500">
            Click expand to view full summary
          </p>
        </div>
      )}
    </div>
  );
};

export default DocumentSummary;
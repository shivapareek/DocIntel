import React, { useState, useRef } from 'react';
import { useDocument } from '../context/DocContext';

const DocumentUpload = () => {
  const { uploadDocument, isUploaded, fileName, fileSize, isLoading, error, resetDocument } = useDocument();
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = async (file) => {
    if (!file) return;

    // Validate file type
    const allowedTypes = ['application/pdf', 'text/plain'];
    if (!allowedTypes.includes(file.type)) {
      alert('Please upload only PDF or TXT files');
      return;
    }

    // Validate file size (10MB max)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      alert('File size should be less than 10MB');
      return;
    }

    try {
      await uploadDocument(file);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleFileSelect(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files[0];
    handleFileSelect(file);
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isUploaded) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Document Uploaded</h2>
          <button
            onClick={resetDocument}
            className="text-sm text-red-600 hover:text-red-800 font-medium"
          >
            Upload New Document
          </button>
        </div>
        
        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <span className="text-2xl">📄</span>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">{fileName}</h3>
              <p className="text-sm text-green-600">{formatFileSize(fileSize)}</p>
            </div>
            <div className="ml-auto">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                ✓ Ready
              </span>
            </div>
          </div>
        </div>

        <div className="mt-4 text-sm text-gray-600">
          <p>Your document has been successfully uploaded and processed. You can now:</p>
          <ul className="mt-2 space-y-1 ml-4">
            <li>• Ask questions about the document content</li>
            <li>• Take the challenge mode to test your understanding</li>
            <li>• View the auto-generated summary below</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Upload Document</h2>
        <p className="text-sm text-gray-600">
          Upload a PDF or TXT file to start analyzing your document with AI assistance.
        </p>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-red-400">⚠️</span>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragOver
            ? 'border-blue-400 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt"
          onChange={handleFileInputChange}
          className="hidden"
        />

        <div className="space-y-4">
          <div className="text-6xl">📄</div>
          
          <div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {dragOver ? 'Drop your file here' : 'Drag and drop your document'}
            </h3>
            <p className="text-sm text-gray-600">
              or{' '}
              <button
                onClick={handleBrowseClick}
                className="text-blue-600 hover:text-blue-800 font-medium"
                disabled={isLoading}
              >
                browse to choose a file
              </button>
            </p>
          </div>

          <div className="text-xs text-gray-500">
            <p>Supported formats: PDF, TXT</p>
            <p>Maximum file size: 10MB</p>
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-md p-3">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-800">Processing your document...</p>
            </div>
          </div>
        </div>
      )}

      <div className="mt-6 bg-gray-50 rounded-md p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">What happens next?</h4>
        <div className="text-sm text-gray-600 space-y-1">
          <p>1. Your document will be analyzed and summarized</p>
          <p>2. You can ask questions about any part of the content</p>
          <p>3. Take challenges to test your understanding</p>
          <p>4. All answers are backed by specific document references</p>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;
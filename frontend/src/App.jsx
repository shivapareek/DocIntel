import React, { useState } from 'react';
import DocumentUpload from './components/DocumentUpload';
import DocumentSummary from './components/DocumentSummary';
import ChatInterface from './components/ChatInterface';
import ChallengeMode from './components/ChallengeMode';
import { DocumentProvider } from './context/DocContext.jsx';
import {  useEffect } from 'react'; // 👈 Add useEffect here


import './App.css';

function App() {
  
  const [activeTab, setActiveTab] = useState('upload');
    useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => console.log("✅ /api/health success:", data))
      .catch(err => console.error("❌ /api/health failed:", err));
  }, []);

  return (
    <DocumentProvider>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <h1 className="text-xl font-bold text-gray-900">
                  🤖 Smart Document Assistant
                </h1>
              </div>
              <div className="text-sm text-gray-500">
                AI-Powered Research Summarization
              </div>
            </div>
          </div>
        </header>

        {/* Navigation Tabs */}
        <nav className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex space-x-8">
              <button
                onClick={() => setActiveTab('upload')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'upload'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                📄 Upload Document
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'chat'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                💬 Ask Anything
              </button>
              <button
                onClick={() => setActiveTab('challenge')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'challenge'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                🧠 Challenge Me
              </button>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {activeTab === 'upload' && (
            <div className="space-y-6">
              <DocumentUpload />
              <DocumentSummary />
            </div>
          )}
          
          {activeTab === 'chat' && <ChatInterface />}
          
          {activeTab === 'challenge' && <ChallengeMode />}
        </main>

        {/* Footer */}
        <footer className="bg-gray-800 text-white mt-12">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="text-center text-sm">
              Built with React + FastAPI • Smart Document Analysis
            </div>
          </div>
        </footer>
      </div>
    </DocumentProvider>
  );
}

export default App;
import React, { useState, useEffect } from 'react';
import DocumentUpload from './components/DocumentUpload';
import DocumentSummary from './components/DocumentSummary';
import ChatInterface from './components/ChatInterface';
import ChallengeMode from './components/ChallengeMode';
import { DocumentProvider } from './context/DocContext.jsx';
import { FileText, MessageSquare, Zap } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [summary, setSummary] = useState("");
  const [fileName, setFileName] = useState("");

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => console.log("✅ /api/health success:", data))
      .catch(err => console.error("❌ /api/health failed:", err));
  }, []);

  const tabs = [
    { id: 'upload', label: 'Upload Document', icon: FileText },
    { id: 'chat', label: 'Ask Anything', icon: MessageSquare },
    { id: 'challenge', label: 'Challenge Me', icon: Zap },
  ];

  return (
    <DocumentProvider>
      <div className="min-h-screen bg-gradient-to-b from-indigo-50 via-white to-indigo-100 font-inter">
        {/* Header */}
        <header className="bg-white shadow-md border-b border-indigo-200">
          <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10">
            <div className="flex justify-between items-center h-20">
              <h1 className="text-3xl font-extrabold text-indigo-700 select-none">
                Smart Document Assistant
              </h1>
              <p className="text-indigo-500 text-lg italic tracking-wide hidden sm:block">
                AI-Powered Research Summarization
              </p>
            </div>
          </div>
        </header>

        {/* Navigation Tabs */}
        <nav className="bg-white border-b border-indigo-200">
          <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10">
            <div className="flex space-x-12">
              {tabs.map(({ id, label, icon: Icon }) => {
                const isActive = activeTab === id;
                return (
                  <button
                    key={id}
                    onClick={() => setActiveTab(id)}
                    className={`relative flex items-center gap-2 text-sm font-semibold px-3 py-4 transition-all duration-300
                      ${isActive
                        ? 'text-indigo-700 after:absolute after:-bottom-1 after:left-0 after:right-0 after:h-1 after:rounded-full after:bg-indigo-600'
                        : 'text-indigo-400 hover:text-indigo-600 hover:after:absolute hover:after:-bottom-1 hover:after:left-0 hover:after:right-0 hover:after:h-1 hover:after:rounded-full hover:after:bg-indigo-300'
                      }
                      focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-offset-2
                    `}
                    aria-current={isActive ? "page" : undefined}
                  >
                    <Icon size={18} />
                    {label}
                  </button>
                );
              })}
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10 py-10 min-h-[60vh]">
          {activeTab === 'upload' && (
            <div className="space-y-10">
              <DocumentUpload setSummary={setSummary} setFileName={setFileName} /> {/* ✅ */}
              <DocumentSummary summary={summary} fileName={fileName} />             {/* ✅ */}
            </div>
          )}

          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'challenge' && <ChallengeMode />}
        </main>

        {/* Footer */}
        <footer className="bg-indigo-700 text-indigo-200 mt-20">
          <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10 py-6">
            <p className="text-center text-sm tracking-wide select-none">
              Built with <span className="font-semibold">React + FastAPI</span> • Smart Document Analysis
            </p>
          </div>
        </footer>
      </div>
    </DocumentProvider>
  );
}

export default App;

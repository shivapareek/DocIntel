import React, { useState, useEffect } from 'react';
import {
  FileText,
  MessageSquare,
  Zap,
  Moon,
  Sun,
  Sparkles,
  Bot,
} from 'lucide-react';
import { ToastProvider } from "./context/ToastContext";

import DocumentUpload from './components/DocumentUpload';
import DocumentSummary from './components/DocumentSummary';
import ChatInterface from './components/ChatInterface';
import ChallengeMode from './components/ChallengeMode';
import { DocumentProvider } from './context/DocContext.jsx';

function App() {
  const prefersDark =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-color-scheme: dark)').matches;

  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'dark' || saved === 'light') return saved === 'dark';
    return prefersDark;
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
    localStorage.setItem('theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  const [activeTab, setActiveTab] = useState('upload');
  const [summary, setSummary] = useState('');
  const [fileName, setFileName] = useState('');

  const tabs = [
    {
      id: 'upload',
      label: 'Upload',
      icon: FileText,
      gradient: 'from-sky-500 to-cyan-500',
    },
    {
      id: 'chat',
      label: 'Chat',
      icon: MessageSquare,
      gradient: 'from-blue-500 to-sky-500',
    },
    {
      id: 'challenge',
      label: 'Challenge',
      icon: Zap,
      gradient: 'from-indigo-500 to-blue-600',
    },
  ];

  return (
    <ToastProvider>
      <DocumentProvider>
        <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-sky-100 dark:from-[#0f172a] dark:via-[#1e293b] dark:to-[#0f172a] font-inter text-gray-800 dark:text-gray-100 transition-colors duration-500">
          <div className="fixed inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-sky-400/10 dark:bg-sky-300/20 rounded-full blur-3xl animate-pulse" />
            <div className="absolute top-3/4 right-1/4 w-96 h-96 bg-blue-500/10 dark:bg-blue-400/20 rounded-full blur-3xl animate-pulse delay-1000" />
            <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-cyan-400/10 dark:bg-cyan-300/20 rounded-full blur-3xl animate-pulse delay-500" />
          </div>

          <header className="relative bg-white/80 dark:bg-[#1e293b]/80 backdrop-blur-xl shadow-xl shadow-black/5 border-b border-white/20 dark:border-slate-700/50">
            <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10">
              <div className="flex justify-between items-center h-20">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-sky-500 to-cyan-500 rounded-2xl flex items-center justify-center shadow-lg shadow-sky-500/25">
                    <Bot className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-black bg-gradient-to-r from-sky-500 via-cyan-500 to-blue-500 bg-clip-text text-transparent select-none">
                      DocIntel
                    </h1>
                    <p className="text-sm text-gray-500 dark:text-gray-400 font-medium select-none">
                      Document + Intelligence
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-sky-100 to-cyan-100 dark:from-[#334155]/30 dark:to-[#1e293b]/30 rounded-xl select-none">
                    <Sparkles className="w-4 h-4 text-sky-600 dark:text-sky-400" />
                    <span className="text-sm font-semibold text-sky-700 dark:text-sky-300">
                      AI Enhanced
                    </span>
                  </div>
                  <button
                    onClick={() => setDarkMode((prev) => !prev)}
                    aria-label="Toggle theme"
                    className="p-3 rounded-2xl bg-white/50 dark:bg-[#334155]/50 hover:bg-white/80 dark:hover:bg-[#1e293b]/80 backdrop-blur-sm transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 shadow-lg shadow-black/5 hover:shadow-xl hover:shadow-black/10 transform hover:-translate-y-1"
                  >
                    {darkMode ? (
                      <Sun className="w-5 h-5 text-amber-500" />
                    ) : (
                      <Moon className="w-5 h-5 text-slate-700" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          </header>

          <nav className="relative bg-white/60 dark:bg-[#1e293b]/60 backdrop-blur-xl border-b border-white/20 dark:border-slate-700/50">
            <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-10">
              <div className="flex justify-center gap-2 py-4">
                {tabs.map(({ id, label, icon: Icon, gradient }) => {
                  const isActive = activeTab === id;
                  return (
                    <button
                      key={id}
                      onClick={() => setActiveTab(id)}
                      className={`relative flex items-center gap-3 px-6 py-3 rounded-2xl font-semibold transition-all duration-300 transform hover:-translate-y-1 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 ${
                        isActive
                          ? `bg-gradient-to-r ${gradient} text-white shadow-lg shadow-black/20`
                          : 'bg-white/50 dark:bg-[#334155]/50 hover:bg-white/80 dark:hover:bg-[#1e293b]/80 text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white backdrop-blur-sm'
                      }`}
                    >
                      <Icon size={20} />
                      {label}
                      {isActive && (
                        <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-white/20 to-transparent animate-pulse" />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          </nav>

          <main className="relative max-w-7xl mx-auto px-6 sm:px-8 lg:px-10 py-12">
            <div className="space-y-8">
              {activeTab === 'upload' && (
                <div className="space-y-10">
                  <DocumentUpload setSummary={setSummary} setFileName={setFileName} />
                  <DocumentSummary summary={summary} fileName={fileName} />
                </div>
              )}
              {activeTab === 'chat' && <ChatInterface />}
              {activeTab === 'challenge' && <ChallengeMode />}
            </div>
          </main>

          <footer className="border-t border-white/20 dark:border-slate-700/50 mt-20 py-4 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>
              © 2025 <span className="font-semibold text-sky-600 dark:text-sky-400">DocIntel</span> · Accelerating Document Intelligence
            </p>
          </footer>
        </div>
      </DocumentProvider>
    </ToastProvider>
  );
}

export default App;

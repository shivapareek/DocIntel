import React, { useState, useRef, useEffect } from 'react';
import {
  Bot,
  User,
  FileText,
  Loader2,
  Sparkles,
  ArrowUpFromLine,
  MessageSquare,
  Lightbulb,
  Trash2,
} from 'lucide-react';
import { useDocument } from '../context/DocContext';

const ChatInterface = () => {
  const {
    isUploaded,
    fileName,
    chatHistory,
    askQuestion,
    clearChatHistory,
    isLoading,
    error,
  } = useDocument();

  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () =>
    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const formatTime = (d) => new Date(d).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!currentQuestion.trim() || isLoading) return;
    const question = currentQuestion.trim();
    setCurrentQuestion('');
    setIsTyping(true);
    await askQuestion(question);
    setIsTyping(false);
  };
  const handleKeyPress = (e) => e.key === 'Enter' && !e.shiftKey && handleSubmit(e);

  const documentSuggestions = [
    'What are the main points?',
    'Explain key findings',
    'What methodology was used?',
    'List all conclusions',
    'Mention limitations',
    'Generate a concise summary',
  ];

  const sendSuggestion = (q) => !isLoading && (setCurrentQuestion(q), handleSubmit({ preventDefault: () => {} }), inputRef.current?.focus());

  if (!isUploaded) {
    return (
      <section className="flex-1 px-4 py-6 dark:bg-slate-800/60 flex flex-col justify-center items-center gap-6">
        <div className="max-w-lg w-full bg-white dark:bg-slate-900/80 backdrop-blur-xl border border-slate-100 dark:border-slate-700 rounded-3xl shadow-xl p-10 text-center animate-fade-in">
          <div className="mx-auto h-16 w-16 rounded-2xl bg-gradient-to-br from-sky-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-sky-500/30 mb-6">
            <ArrowUpFromLine className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-2">Upload a Document to Start</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
            Switch to the <span className="font-semibold text-sky-600">Upload</span> tab and drop your PDF, DOCX, or TXT file. Once processed, you can chat with our AI assistant for instant insights.
          </p>
          <div className="flex items-center justify-center gap-3 text-xs text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-1"><FileText className="h-4 w-4" /> PDF · DOCX · TXT</span>
            <span className="flex items-center gap-1"><Sparkles className="h-4 w-4" /> Hindi + English</span>
          </div>
        </div>
      </section>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto h-[600px] flex flex-col bg-gradient-to-br from-white to-sky-50 dark:from-slate-900 dark:to-slate-800 rounded-3xl shadow-2xl overflow-hidden animate-fade-in">
      <header className="bg-gradient-to-r from-sky-700 to-blue-700 text-white px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <MessageSquare className="h-6 w-6" />
          <div>
            <h3 className="font-semibold text-lg">AI Chat Assistant</h3>
            <p className="text-xs text-white/80 truncate max-w-[180px] md:max-w-xs">{fileName}</p>
          </div>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="bg-white/20 px-2 py-0.5 rounded-full">{chatHistory.length} msgs</span>
          {chatHistory.length > 0 && (
            <button onClick={clearChatHistory} className="flex items-center gap-1 bg-red-600/20 hover:bg-red-600/30 px-3 py-1 rounded-full">
              <Trash2 className="h-3 w-3" /> Clear
            </button>
          )}
        </div>
      </header>

      <section className="flex-1 px-6 py-4 overflow-y-auto scrollbar-thin scrollbar-thumb-sky-300 dark:scrollbar-thumb-sky-700">
        {chatHistory.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-6">
            <Bot className="h-12 w-12 text-sky-500" />
            <p className="text-center text-sm text-slate-600 dark:text-slate-400 max-w-sm">
              Ask anything about your document. Here are some ideas:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-md">
              {documentSuggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => sendSuggestion(s)}
                  className="flex items-center gap-2 bg-white dark:bg-slate-700/60 border border-slate-200 dark:border-slate-600 rounded-lg px-3 py-2 text-sm hover:border-sky-400 hover:bg-sky-50 dark:hover:bg-slate-600 transition"
                >
                  <Lightbulb className="h-4 w-4 text-sky-500" /> {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-5">
            {chatHistory.map((m, i) => (
              <div key={i} className={`flex ${m.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[90%] md:max-w-3xl rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-md transition-all duration-300 ${
                    m.type === 'user'
                      ? 'bg-gradient-to-br from-blue-600 to-sky-500 text-white rounded-br-sm'
                      : 'bg-white dark:bg-slate-700/70 text-slate-800 dark:text-slate-100 border dark:border-slate-600 rounded-bl-sm'
                  }`}
                >
                  {m.content}
                  {m.justification && <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">{m.justification}</p>}
                  <div className="text-xs mt-2 opacity-60 flex items-center gap-1">
                    {m.type === 'user' ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />} {formatTime(m.timestamp)}
                  </div>
                </div>
              </div>
            ))}
            {(isTyping || isLoading) && (
              <div className="flex justify-start">
                <div className="bg-white dark:bg-slate-700/70 border dark:border-slate-600 px-4 py-3 rounded-2xl text-sm flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-sky-500" /> Typing…
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </section>

      {error && (
        <div className="border-t bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-600 p-3 text-red-700 dark:text-red-300 text-sm text-center">
          {error}
        </div>
      )}

      <footer className="border-t bg-white dark:bg-slate-900/80 backdrop-blur-xl p-4">
        <form onSubmit={handleSubmit} className="flex gap-3">
          <textarea
            ref={inputRef}
            value={currentQuestion}
            onChange={(e) => {
              setCurrentQuestion(e.target.value);
              e.target.style.height = 'auto';
              e.target.style.height = `${e.target.scrollHeight}px`;
            }}
            onKeyDown={handleKeyPress}
            rows={1}
            placeholder="Ask a question…"
            className="flex-1 resize-none bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-sky-500 focus:border-transparent text-slate-800 dark:text-slate-100"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!currentQuestion.trim() || isLoading}
            className="shrink-0 h-12 px-6 bg-sky-600 hover:bg-sky-700 text-white rounded-xl flex items-center justify-center disabled:opacity-50"
          >
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : 'Send'}
          </button>
        </form>
      </footer>
    </div>
  );
};

export default ChatInterface;

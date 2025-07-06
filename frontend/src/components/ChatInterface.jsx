import React, { useState, useRef, useEffect } from 'react';
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

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 50);
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, isLoading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!currentQuestion.trim() || isLoading) return;

    const question = currentQuestion.trim();
    setCurrentQuestion('');
    setIsTyping(true);

    await askQuestion(question);

    setIsTyping(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatTime = (date) => {
    return new Date(date).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handleSuggestionClick = async (suggestion) => {
    if (isLoading) return;
    setCurrentQuestion(suggestion);
    await handleSubmit({ preventDefault: () => {} });
    inputRef.current?.focus();
  };

  const clearChat = () => clearChatHistory();

  const documentSuggestions = [
    "Document mein main points kya hain?",
    "Key findings explain karo",
    "What methodology was used?",
    "Conclusions kya hain?",
    "Are there any limitations?",
    "Summary de do is document ka",
  ];

  // ── 1. Upload Required View ──────────────────────────────────────────────
  if (!isUploaded) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="max-w-4xl w-full">
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="text-6xl mb-6">📄</div>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Document Upload Required</h1>
            <p className="text-lg text-gray-600 mb-6">
              Pehle document upload karo, phir main detailed analysis kar sakta hun!
            </p>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <div className="flex items-center justify-center space-x-2">
                <span className="text-yellow-600">⚠️</span>
                <p className="text-yellow-800 font-medium">
                  Document analysis ke liye "Upload Document" tab mein jao
                </p>
              </div>
            </div>

            <div className="flex items-center justify-center space-x-4 text-sm text-gray-500">
              <span>✅ PDF Support</span>
              <span>✅ Word Docs</span>
              <span>✅ Text Files</span>
              <span>✅ Hindi + English</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ── 2. Main Chat View ────────────────────────────────────────────────────
  return (
    <div className="bg-white rounded-2xl shadow-xl h-[700px] flex flex-col overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-blue-600 text-white p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
              <span className="text-xl">💬</span>
            </div>
            <div>
              <h2 className="text-lg font-semibold">Document Analysis Mode</h2>
              <p className="text-sm text-green-100">📄 {fileName} - Ready for analysis!</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <span className="text-xs bg-white bg-opacity-20 px-2 py-1 rounded-full">
              {chatHistory.length} messages
            </span>
            {chatHistory.length > 0 && (
              <button
                onClick={clearChat}
                className="text-xs bg-red-500 bg-opacity-20 hover:bg-opacity-30 px-3 py-1 rounded-full transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
        {chatHistory.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🎉</div>
            <h3 className="text-xl font-semibold text-gray-800 mb-3">Document uploaded successfully!</h3>
            <p className="text-gray-600 mb-6">
              Ab main aapke document ke bare mein detailed analysis kar sakta hun. Kya puchna chahoge?
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
              {documentSuggestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(question)}
                  className="text-left p-3 bg-white rounded-lg border border-gray-200 hover:border-blue-300 hover:bg-blue-50 transition-all duration-200 text-sm"
                >
                  <span className="text-blue-600">💡</span> {question}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {chatHistory.map((message, index) => (
              <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-xs md:max-w-md lg:max-w-lg xl:max-w-2xl px-4 py-3 rounded-2xl ${
                    message.type === 'user'
                      ? 'bg-blue-600 text-white rounded-br-sm'
                      : 'bg-white text-gray-800 shadow-md rounded-bl-sm border'
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    <span className="text-sm flex-shrink-0 mt-1">
                      {message.type === 'user' ? '👤' : '🤖'}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="whitespace-pre-wrap break-words">{message.content}</div>

                      {message.justification && (
                        <div className="mt-2 text-xs text-gray-500">📍 {message.justification}</div>
                      )}

                      {/* Source snippets & confidence removed for cleaner ChatGPT‑style output */}

                      <div className="text-xs opacity-60 mt-2">{formatTime(message.timestamp)}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {(isTyping || isLoading) && (
              <div className="flex justify-start">
                <div className="bg-white rounded-2xl rounded-bl-sm shadow-md border px-4 py-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm">🤖</span>
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
                      <div
                        className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                        style={{ animationDelay: '0.1s' }}
                      />
                      <div
                        className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                        style={{ animationDelay: '0.2s' }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Error Box */}
      {error && (
        <div className="border-t bg-red-50 border-red-200 p-4">
          <div className="flex items-center space-x-2">
            <span className="text-red-500 text-lg">⚠️</span>
            <p className="text-sm text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Input Box */}
      <div className="border-t bg-white p-4">
        <form onSubmit={handleSubmit} className="flex space-x-3">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={currentQuestion}
              onChange={(e) => {
                setCurrentQuestion(e.target.value);
                e.target.style.height = 'auto';
                e.target.style.height = `${e.target.scrollHeight}px`;
              }}
              onKeyDown={handleKeyPress}
              placeholder="Document ke bare mein kuch bhi pucho... (Hindi/English both work!)"
              className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm overflow-hidden"
              rows={1}
              disabled={isLoading}
              autoFocus
            />
          </div>
          <button
            type="submit"
            disabled={!currentQuestion.trim() || isLoading}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <span className="text-lg">📤</span>
            )}
          </button>
        </form>
        <div className="mt-2 text-xs text-gray-500 text-center">
          Enter to send • Shift+Enter for new line • Document analysis active! 🔥
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

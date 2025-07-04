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
    error 
  } = useDocument();
  
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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

    try {
      await askQuestion(question);
    } catch (error) {
      console.error('Failed to ask question:', error);
    } finally {
      setIsTyping(false);
    }
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
      minute: '2-digit' 
    });
  };

  const suggestedQuestions = [
    "What are the main points discussed in this document?",
    "Can you explain the key findings?",
    "What methodology was used?",
    "What are the conclusions?",
    "Are there any limitations mentioned?"
  ];

  if (!isUploaded) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="text-6xl mb-4">📄</div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No Document Uploaded</h2>
        <p className="text-gray-600 mb-6">
          Please upload a document first to start asking questions.
        </p>
        <div className="text-sm text-gray-500">
          Go to the "Upload Document" tab to get started.
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md h-[600px] flex flex-col">
      {/* Header */}
      <div className="border-b p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xl">💬</span>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Ask Anything</h2>
              <p className="text-sm text-gray-600">Chatting about: {fileName}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-500">
              {chatHistory.length / 2} questions asked
            </span>
            {chatHistory.length > 0 && (
              <button
                onClick={clearChatHistory}
                className="text-xs text-red-600 hover:text-red-800 font-medium"
              >
                Clear Chat
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatHistory.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🤖</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to help!</h3>
            <p className="text-gray-600 mb-6">
              Ask me anything about your document. I'll provide answers with specific references.
            </p>
            
            <div className="text-left max-w-md mx-auto">
              <p className="text-sm font-medium text-gray-700 mb-2">Try asking:</p>
              <div className="space-y-2">
                {suggestedQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentQuestion(question)}
                    className="block w-full text-left text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-3 py-2 rounded-md transition-colors"
                  >
                    "{question}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          chatHistory.map((message, index) => (
            <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3xl px-4 py-3 rounded-lg ${
                message.type === 'user' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                <div className="flex items-start space-x-2">
                  <span className="text-sm">
                    {message.type === 'user' ? '👤' : '🤖'}
                  </span>
                  <div className="flex-1">
                    <div className="whitespace-pre-wrap">{message.content}</div>

                    {message.type === 'assistant' && (
                      <div className="mt-3 pt-3 border-t border-gray-200 space-y-2">
                        {/* Justification */}
                        {message.justification && (
                          <div>
                            <span className="text-xs font-medium text-gray-600">📍 Justification:</span>
                            <p className="text-xs text-gray-700 mt-1">{message.justification}</p>
                          </div>
                        )}

                        {/* Source Snippets */}
                        {message.source_snippets && message.source_snippets.length > 0 && (
                          <div>
                            <span className="text-xs font-medium text-gray-600">📚 Source Snippets:</span>
                            <ul className="list-disc list-inside mt-1 space-y-1 text-xs text-gray-700">
                              {message.source_snippets.map((snippet, i) => (
                                <li key={i} className="italic">"{snippet}"</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Confidence */}
                        {typeof message.confidence === 'number' && (
                          <div>
                            <span className="text-xs font-medium text-gray-600">🔎 Confidence:</span>
                            <p className="text-xs text-gray-700 mt-1">{(message.confidence * 100).toFixed(1)}%</p>
                          </div>
                        )}
                      </div>
                    )}

                    <div className="text-xs opacity-75 mt-2">
                      {formatTime(message.timestamp)}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
        
        {(isLoading || isTyping) && (
          <div className="flex justify-start">
            <div className="max-w-3xl px-4 py-3 rounded-lg bg-gray-100 text-gray-800">
              <div className="flex items-center space-x-2">
                <span className="text-sm">🤖</span>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Error Display */}
      {error && (
        <div className="border-t bg-red-50 p-3">
          <div className="flex items-center space-x-2">
            <span className="text-red-400">⚠️</span>
            <p className="text-sm text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={currentQuestion}
              onChange={(e) => setCurrentQuestion(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask anything about your document..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows="1"
              disabled={isLoading}
            />
          </div>
          <button
            type="submit"
            disabled={!currentQuestion.trim() || isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            ) : (
              '📤'
            )}
          </button>
        </form>
        <div className="mt-2 text-xs text-gray-500">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;

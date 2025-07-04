import React, { useState, useEffect } from 'react';
import { useDocument } from '../context/DocContext';

const ChallengeMode = () => {
  const { 
    isUploaded, 
    fileName,
    challenges, 
    userAnswers,
    currentChallenge,
    generateChallenges,
    submitChallengeAnswer,
    setCurrentChallenge,
    isLoading,
    error 
  } = useDocument();

  const [currentAnswer, setCurrentAnswer] = useState('');
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    // Clear current answer when challenge changes
    setCurrentAnswer('');
  }, [currentChallenge]);

  const handleStartChallenge = async () => {
    try {
      await generateChallenges();
      setShowResults(false);
    } catch (error) {
      console.error('Failed to generate challenges:', error);
    }
  };

  const handleSubmitAnswer = async () => {
    if (!currentAnswer.trim() || currentChallenge === null) return;

    try {
      await submitChallengeAnswer(currentChallenge, currentAnswer.trim());
      setCurrentAnswer('');
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  const handleNextQuestion = () => {
    if (currentChallenge < challenges.length - 1) {
      setCurrentChallenge(currentChallenge + 1);
    }
  };

  const handlePrevQuestion = () => {
    if (currentChallenge > 0) {
      setCurrentChallenge(currentChallenge - 1);
    }
  };

  const handleShowResults = () => {
    setShowResults(true);
  };

  const getCurrentAnswer = () => {
    return userAnswers.find(answer => answer.questionIndex === currentChallenge);
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getOverallScore = () => {
    if (userAnswers.length === 0) return 0;
    const totalScore = userAnswers.reduce((sum, answer) => sum + (answer.evaluation?.score || 0), 0);
    return Math.round(totalScore / userAnswers.length);
  };

  if (!isUploaded) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="text-6xl mb-4">📄</div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">No Document Uploaded</h2>
        <p className="text-gray-600 mb-6">
          Please upload a document first to start the challenge mode.
        </p>
        <div className="text-sm text-gray-500">
          Go to the "Upload Document" tab to get started.
        </div>
      </div>
    );
  }

  // Results View
  if (showResults && userAnswers.length > 0) {
    const overallScore = getOverallScore();
    
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Challenge Results</h2>
          <button
            onClick={handleStartChallenge}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Take New Challenge
          </button>
        </div>

        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900">Overall Score</h3>
              <p className="text-sm text-gray-600">Based on {userAnswers.length} questions</p>
            </div>
            <div className={`text-3xl font-bold ${getScoreColor(overallScore)}`}>
              {overallScore}%
            </div>
          </div>
          
          <div className="mt-3">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full transition-all duration-500 ${
                  overallScore >= 80 ? 'bg-green-500' : 
                  overallScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${overallScore}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {userAnswers.map((answer, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between mb-3">
                <h4 className="text-sm font-medium text-gray-900">
                  Question {answer.questionIndex + 1}
                </h4>
                <span className={`text-sm font-semibold ${getScoreColor(answer.evaluation?.score || 0)}`}>
                  {answer.evaluation?.score || 0}%
                </span>
              </div>
              
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-700 mb-2">
                    {challenges[answer.questionIndex]?.question}
                  </p>
                </div>
                
                <div className="bg-blue-50 p-3 rounded">
                  <p className="text-xs font-medium text-blue-700 mb-1">Your Answer:</p>
                  <p className="text-sm text-blue-800">{answer.userAnswer}</p>
                </div>
                
                {answer.evaluation?.feedback && (
                  <div className="bg-gray-50 p-3 rounded">
                    <p className="text-xs font-medium text-gray-700 mb-1">Feedback:</p>
                    <p className="text-sm text-gray-600">{answer.evaluation.feedback}</p>
                  </div>
                )}
                
                {answer.evaluation?.reference && (
                  <div className="bg-green-50 p-3 rounded">
                    <p className="text-xs font-medium text-green-700 mb-1">Reference:</p>
                    <p className="text-sm text-green-600">{answer.evaluation.reference}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // No challenges generated yet
  if (challenges.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="text-6xl mb-4">🧠</div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Challenge Mode</h2>
        <p className="text-gray-600 mb-6">
          Test your understanding with AI-generated questions based on your document.
        </p>
        
        <div className="mb-6 text-sm text-gray-600 space-y-2">
          <p>📖 Source: {fileName}</p>
          <p>🎯 I'll generate 3 challenging questions</p>
          <p>💡 Each answer will be evaluated with feedback</p>
          <p>📊 You'll get a detailed score report</p>
        </div>

        <button
          onClick={handleStartChallenge}
          disabled={isLoading}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              <span>Generating Questions...</span>
            </div>
          ) : (
            'Start Challenge'
          )}
        </button>
      </div>
    );
  }

  // Challenge Questions View
  const currentQuestionData = challenges[currentChallenge];
  const currentUserAnswer = getCurrentAnswer();
  
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          <h2 className="text-xl font-semibold text-gray-900">Challenge Mode</h2>
          <span className="text-sm text-gray-600">
            Question {currentChallenge + 1} of {challenges.length}
          </span>
        </div>
        <button
          onClick={handleShowResults}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          disabled={userAnswers.length === 0}
        >
          View Results
        </button>
      </div>

      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3">
          <div className="flex">
            <span className="text-red-400 mr-2">⚠️</span>
            <p className="text-sm text-red-800">{error}</p>
          </div>
        </div>
      )}

      <div className="mb-6">
        <div className="flex items-center space-x-2 mb-3">
          <span className="text-2xl">❓</span>
          <h3 className="text-lg font-medium text-gray-900">
            Question {currentChallenge + 1}
          </h3>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg">
          <p className="text-gray-800 leading-relaxed">
            {currentQuestionData?.question}
          </p>
        </div>
      </div>

      {currentUserAnswer ? (
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="text-sm font-medium text-blue-700 mb-2">Your Answer:</h4>
            <p className="text-blue-800">{currentUserAnswer.userAnswer}</p>
          </div>
          
          {currentUserAnswer.evaluation && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium text-gray-900">Evaluation Results</h4>
                <span className={`text-lg font-semibold ${getScoreColor(currentUserAnswer.evaluation.score)}`}>
                  {currentUserAnswer.evaluation.score}%
                </span>
              </div>
              
              {currentUserAnswer.evaluation.feedback && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Feedback:</h5>
                  <p className="text-gray-600">{currentUserAnswer.evaluation.feedback}</p>
                </div>
              )}
              
              {currentUserAnswer.evaluation.reference && (
                <div className="bg-green-50 p-4 rounded-lg">
                  <h5 className="text-sm font-medium text-green-700 mb-2">Document Reference:</h5>
                  <p className="text-green-600">{currentUserAnswer.evaluation.reference}</p>
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Answer:
            </label>
            <textarea
              value={currentAnswer}
              onChange={(e) => setCurrentAnswer(e.target.value)}
              placeholder="Type your answer here..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows="4"
              disabled={isLoading}
            />
          </div>
          
          <button
            onClick={handleSubmitAnswer}
            disabled={!currentAnswer.trim() || isLoading}
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span>Evaluating...</span>
              </div>
            ) : (
              'Submit Answer'
            )}
          </button>
        </div>
      )}

      {/* Navigation */}
      <div className="flex items-center justify-between mt-6 pt-4 border-t">
        <button
          onClick={handlePrevQuestion}
          disabled={currentChallenge === 0}
          className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>←</span>
          <span>Previous</span>
        </button>
        
        <div className="flex space-x-2">
          {challenges.map((_, index) => (
            <button
              key={index}
              onClick={() => setCurrentChallenge(index)}
              className={`w-8 h-8 rounded-full text-sm font-medium transition-colors ${
                index === currentChallenge
                  ? 'bg-blue-600 text-white'
                  : userAnswers.find(a => a.questionIndex === index)
                  ? 'bg-green-100 text-green-600'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {index + 1}
            </button>
          ))}
        </div>
        
        <button
          onClick={handleNextQuestion}
          disabled={currentChallenge >= challenges.length - 1}
          className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>Next</span>
          <span>→</span>
        </button>
      </div>
    </div>
  );
};

export default ChallengeMode;
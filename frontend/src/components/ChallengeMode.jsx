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
      const q = challenges[currentChallenge]; // ✅ Use real question ID
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
  return userAnswers.find(a => a.questionIndex === currentChallenge);
};


  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getOverallScore = () => {
    if (userAnswers.length === 0) return 0;
    const total = userAnswers.reduce((sum, a) => sum + (a.evaluation?.score || 0), 0);
    return Math.round(total / userAnswers.length);
  };

  if (!isUploaded) {
    return (
      <div className="bg-white rounded-lg shadow-md p-8 text-center">
        <div className="text-6xl mb-4">📄</div>
        <h2 className="text-xl font-semibold">No Document Uploaded</h2>
        <p className="text-gray-600 mb-4">Please upload a document to begin.</p>
      </div>
    );
  }

  if (showResults && userAnswers.length > 0) {
    const overallScore = getOverallScore();

    return (
      <div className="bg-white p-6 rounded-lg shadow-md">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">Challenge Results</h2>
          <button
            onClick={handleStartChallenge}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Take New Challenge
          </button>
        </div>

        <div className="mb-6 p-4 bg-gray-100 rounded-lg">
          <h3 className="font-medium text-gray-800">Overall Score</h3>
          <div className="flex justify-between items-center mt-2">
            <span className="text-lg font-bold">Based on {userAnswers.length} questions</span>
            <span className={`text-2xl font-bold ${getScoreColor(overallScore)}`}>{overallScore}%</span>
          </div>
        </div>

        {userAnswers.map((ans, i) => {
          const q = challenges.find(c => c.id === ans.questionId);
          return (
            <div key={i} className="border p-4 rounded mb-4">
              <h4 className="font-semibold text-gray-900 mb-2">Q{i + 1}: {q?.question}</h4>
              <p className="text-blue-800 mb-2"><strong>Your Answer:</strong> {ans.userAnswer}</p>
              <p className={`mb-2 font-medium ${getScoreColor(ans.evaluation?.score || 0)}`}>
                ✅ Score: {ans.evaluation?.score || 0}% — {ans.evaluation?.correct ? 'Correct' : 'Incorrect'}
              </p>
              <p className="text-gray-700 mb-1"><strong>Feedback:</strong> {ans.evaluation?.feedback}</p>
              <p className="text-gray-700 mb-1"><strong>Justification:</strong> {ans.evaluation?.justification}</p>
              <p className="text-green-700"><strong>Reference:</strong> {ans.evaluation?.reference}</p>
            </div>
          );
        })}
      </div>
    );
  }

  if (challenges.length === 0) {
    return (
      <div className="bg-white p-8 rounded-lg shadow-md text-center">
        <div className="text-6xl mb-4">🧠</div>
        <h2 className="text-xl font-semibold">Challenge Mode</h2>
        <p className="text-gray-600 mb-4">Generate 3 AI-based questions and get feedback.</p>
        <button
          onClick={handleStartChallenge}
          disabled={isLoading}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? 'Generating...' : 'Start Challenge'}
        </button>
      </div>
    );
  }

  const currentQuestion = challenges[currentChallenge];
  const currentUserAnswer = getCurrentAnswer();

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Challenge Mode</h2>
        <button
          onClick={handleShowResults}
          disabled={userAnswers.length === 0}
          className="text-blue-600 hover:underline"
        >
          View Results
        </button>
      </div>

      <h3 className="text-lg font-medium mb-2">Question {currentChallenge + 1}:</h3>
      <div className="bg-gray-100 p-4 rounded mb-4">
        <p>{currentQuestion?.question}</p>
      </div>

      {currentUserAnswer ? (
        <div className="space-y-2">
          <p className="text-blue-800"><strong>Your Answer:</strong> {currentUserAnswer.userAnswer}</p>
          <p className={`font-medium ${getScoreColor(currentUserAnswer.evaluation?.score || 0)}`}>
            ✅ Score: {currentUserAnswer.evaluation?.score || 0}% — {currentUserAnswer.evaluation?.correct ? 'Correct' : 'Incorrect'}
          </p>
          <p><strong>Feedback:</strong> {currentUserAnswer.evaluation?.feedback}</p>
          <p><strong>Justification:</strong> {currentUserAnswer.evaluation?.justification}</p>
          <p className="text-green-700"><strong>Reference:</strong> {currentUserAnswer.evaluation?.reference}</p>
        </div>
      ) : (
        <div>
          <textarea
            value={currentAnswer}
            onChange={(e) => setCurrentAnswer(e.target.value)}
            placeholder="Type your answer..."
            rows={4}
            className="w-full border rounded p-3 mb-3"
          />
          <button
            onClick={handleSubmitAnswer}
            disabled={!currentAnswer.trim() || isLoading}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            Submit Answer
          </button>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between items-center mt-6 pt-4 border-t">
        <button onClick={handlePrevQuestion} disabled={currentChallenge === 0} className="text-gray-600 hover:underline">
          ← Previous
        </button>
        <div className="space-x-2">
          {challenges.map((q, idx) => {
            const ans = userAnswers.find(a => a.questionId === q.id);
            const color = !ans
              ? 'bg-gray-200 text-gray-600'
              : ans.evaluation.score >= 80
              ? 'bg-green-500 text-white'
              : ans.evaluation.score >= 60
              ? 'bg-yellow-400 text-white'
              : 'bg-red-500 text-white';
            return (
              <button
                key={q.id}
                onClick={() => setCurrentChallenge(idx)}
                className={`w-8 h-8 rounded-full ${color}`}
              >
                {idx + 1}
              </button>
            );
          })}
        </div>
        <button onClick={handleNextQuestion} disabled={currentChallenge === challenges.length - 1} className="text-gray-600 hover:underline">
          Next →
        </button>
      </div>
    </div>
  );
};

export default ChallengeMode;

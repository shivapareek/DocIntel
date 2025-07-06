import React, { useState, useEffect } from "react";
import { useDocument } from "../context/DocContext";

/**
 * ChallengeMode – MCQ practice component
 * -------------------------------------------------------------
 * • Generates 3 document‑aware questions via backend.
 * • Shows inline feedback & an optional detailed view.
 * • Persists results so user can review overall score.
 */
const ChallengeMode = () => {
  const {
    isUploaded,
    challenges,
    userAnswers,
    currentChallenge,
    generateChallenges,
    submitChallengeAnswer,
    setCurrentChallenge,
    isLoading,
  } = useDocument();

  // ────────────────────────────────────────────────────────────── state
  const [selectedOption, setSelectedOption] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [showDetailedFeedback, setShowDetailedFeedback] = useState(false);

  // Reset radio + close detailed panel whenever we change Q
  useEffect(() => {
    setSelectedOption("");
    setShowDetailedFeedback(false);
  }, [currentChallenge]);

  // ────────────────────────────────────────────────────────────── helpers
  const getCurrentAnswer = () =>
    userAnswers.find((a) => a.questionIndex === currentChallenge);

  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getOverallScore = () => {
    if (!userAnswers.length) return 0;
    const total = userAnswers.reduce(
      (sum, a) => sum + (a.evaluation?.score || 0),
      0
    );
    return Math.round(total / userAnswers.length);
  };

  // ────────────────────────────────────────────────────────────── actions
  const handleStartChallenge = async () => {
    await generateChallenges();
    setShowResults(false);
    setSelectedOption("");
    setShowDetailedFeedback(false);
  };

  const handleSubmitAnswer = async () => {
    if (!selectedOption || currentChallenge === null) return;
    await submitChallengeAnswer(currentChallenge, selectedOption);
    setSelectedOption("");
    setShowDetailedFeedback(true);
  };

  const handleNext = () => {
    if (currentChallenge < challenges.length - 1) {
      setCurrentChallenge(currentChallenge + 1);
    }
  };

  const handlePrev = () => {
    if (currentChallenge > 0) {
      setCurrentChallenge(currentChallenge - 1);
    }
  };

  // ────────────────────────────────────────────────────────────── render
  if (!isUploaded) {
    return (
      <div className="p-8 bg-white rounded shadow text-center">
        <p className="text-xl">📄 Upload a document to start</p>
      </div>
    );
  }

  // Finished state – show summary panel
  if (showResults && userAnswers.length) {
    const overall = getOverallScore();
    return (
      <div className="p-6 bg-white rounded shadow w-full max-w-2xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold">Challenge Results</h2>
          <button
            className="bg-blue-600 text-white px-4 py-2 rounded"
            onClick={handleStartChallenge}
          >
            Retry
          </button>
        </div>

        <div className="mb-4 text-lg font-semibold">
          Overall Score: <span className={getScoreColor(overall)}>{overall}%</span>
        </div>

        {userAnswers.map((ans, i) => {
          const q = challenges.find((c) => c.id === ans.questionId);
          return (
            <div key={i} className="border p-4 rounded mb-4">
              <p className="font-bold mb-1">
                Q{i + 1}: {q?.question}
              </p>
              <p>
                <strong>Your Answer:</strong> {ans.userAnswer}
              </p>
              <p className={getScoreColor(ans.evaluation.score)}>
                ✅ Score: {ans.evaluation.score}% — {ans.evaluation.correct ? "Correct" : "Incorrect"}
              </p>
              <p>
                <strong>Feedback:</strong> {ans.evaluation.feedback}
              </p>
              <p>
                <strong>Justification:</strong> {ans.evaluation.justification}
              </p>
            </div>
          );
        })}
      </div>
    );
  }

  // No questions yet – show start screen
  if (!challenges.length) {
    return (
      <div className="p-8 bg-white rounded shadow text-center">
        <p className="text-2xl mb-4">🧠 Challenge Mode</p>
        <button
          onClick={handleStartChallenge}
          className="bg-blue-600 text-white px-6 py-3 rounded"
        >
          {isLoading ? "Loading…" : "Start Challenge"}
        </button>
      </div>
    );
  }

  // Ongoing quiz view --------------------------------------------------
  const currentQuestion = challenges[currentChallenge];
  const currentUserAnswer = getCurrentAnswer();

  return (
    <div className="p-6 bg-white rounded shadow w-full max-w-2xl mx-auto">
      <div className="flex justify-between mb-4">
        <h2 className="text-2xl font-semibold">Challenge Mode</h2>
        <button onClick={() => setShowResults(true)} className="text-blue-600 underline">
          View Results
        </button>
      </div>

      <h3 className="mb-4 font-medium text-lg">
        Question {currentChallenge + 1}: {currentQuestion.question}
      </h3>

      <div className="space-y-3 mb-6">
        {Object.entries(currentQuestion.options).map(([letter, text]) => (
          <label
            key={letter}
            className="flex items-start space-x-2 p-3 border rounded cursor-pointer hover:bg-gray-100"
          >
            <input
              type="radio"
              name="option"
              value={letter}
              checked={selectedOption === letter}
              onChange={() => setSelectedOption(letter)}
              className="mt-1"
            />
            <span><strong>{letter}.</strong> {text}</span>
          </label>
        ))}
      </div>

      {/* Answer panel */}
      {currentUserAnswer ? (
        <div className="mt-4 p-4 bg-gray-100 rounded">
          <p>
            <strong>Your Answer:</strong> {currentUserAnswer.userAnswer}
          </p>
          <p className={getScoreColor(currentUserAnswer.evaluation.score)}>
            ✅ Score: {currentUserAnswer.evaluation.score}% — {currentUserAnswer.evaluation.correct ? "Correct" : "Incorrect"}
          </p>

          {showDetailedFeedback ? (
            <div className="mt-2 space-y-1">
              <p>
                <strong>Feedback:</strong> {currentUserAnswer.evaluation.feedback}
              </p>
              <p>
                <strong>Justification:</strong> {currentUserAnswer.evaluation.justification}
              </p>
            </div>
          ) : (
            <button
              className="text-sm text-blue-600 underline mt-2"
              onClick={() => setShowDetailedFeedback(true)}
            >
              Show Detailed Feedback
            </button>
          )}
        </div>
      ) : (
        <button
          onClick={handleSubmitAnswer}
          disabled={!selectedOption}
          className="bg-blue-600 text-white px-5 py-2 rounded"
        >
          Submit Answer
        </button>
      )}

      {/* Nav controls */}
      <div className="flex justify-between mt-8 text-gray-700">
        <button onClick={handlePrev} disabled={currentChallenge === 0}>
          ← Previous
        </button>
        <button
          onClick={handleNext}
          disabled={currentChallenge === challenges.length - 1 || !currentUserAnswer}
        >
          Next →
        </button>
      </div>
    </div>
  );
};

export default ChallengeMode;

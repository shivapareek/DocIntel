import React, { useState, useEffect } from "react";
import { useDocument } from "../context/DocContext";

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

  const [selectedOption, setSelectedOption] = useState("");
  const [showResults, setShowResults] = useState(false);

  useEffect(() => {
    setSelectedOption("");
  }, [currentChallenge]);

  const handleStartChallenge = async () => {
    await generateChallenges();
    setShowResults(false);
    setSelectedOption("");
  };

  const handleSubmitAnswer = async () => {
    if (!selectedOption || currentChallenge === null) return;
    await submitChallengeAnswer(currentChallenge, selectedOption);
    setSelectedOption("");
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

  const getCurrentAnswer = () => {
    return userAnswers.find((a) => a.questionIndex === currentChallenge);
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-600";
    if (score >= 60) return "text-yellow-600";
    return "text-red-600";
  };

  const getOverallScore = () => {
    if (userAnswers.length === 0) return 0;
    const total = userAnswers.reduce(
      (sum, a) => sum + (a.evaluation?.score || 0),
      0
    );
    return Math.round(total / userAnswers.length);
  };

  const currentQuestion = challenges[currentChallenge];
  const currentUserAnswer = getCurrentAnswer();

  if (!isUploaded) {
    return (
      <div className="p-8 bg-white rounded shadow text-center">
        <p className="text-xl">📄 Upload a document to start</p>
      </div>
    );
  }

  if (showResults && userAnswers.length > 0) {
    const overallScore = getOverallScore();

    return (
      <div className="p-6 bg-white rounded shadow">
        <div className="flex justify-between mb-6">
          <h2 className="text-xl font-bold">Challenge Results</h2>
          <button
            className="bg-blue-600 text-white px-4 py-2 rounded"
            onClick={handleStartChallenge}
          >
            Retry
          </button>
        </div>

        <div className="mb-4 text-lg font-semibold">
          Overall Score:{" "}
          <span className={getScoreColor(overallScore)}>{overallScore}%</span>
        </div>

        {userAnswers.map((ans, i) => {
          const q = challenges.find((c) => c.id === ans.questionId);
          return (
            <div key={i} className="border p-4 rounded mb-4">
              <p className="font-bold">
                Q{i + 1}: {q?.question}
              </p>
              <p>
                <strong>Your Answer:</strong> {ans.userAnswer}
              </p>
              <p className={getScoreColor(ans.evaluation.score)}>
                ✅ Score: {ans.evaluation.score}% —{" "}
                {ans.evaluation.correct ? "Correct" : "Incorrect"}
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

  if (challenges.length === 0) {
    return (
      <div className="p-8 bg-white rounded shadow text-center">
        <p className="text-2xl mb-4">🧠 Challenge Mode</p>
        <button
          onClick={handleStartChallenge}
          className="bg-blue-600 text-white px-6 py-3 rounded"
        >
          Start Challenge
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white rounded shadow">
      <div className="flex justify-between mb-4">
        <h2 className="text-xl font-semibold">Challenge Mode</h2>
        <button
          onClick={() => setShowResults(true)}
          className="text-blue-600 underline"
        >
          View Results
        </button>
      </div>

      <h3 className="mb-2 font-medium">
        Question {currentChallenge + 1}: {currentQuestion.question}
      </h3>

      <div className="space-y-2 mb-4">
        {Object.entries(currentQuestion.options).map(([letter, opt], idx) => (
          <label
            key={idx}
            className="block p-2 border rounded cursor-pointer hover:bg-gray-100"
          >
            <input
              type="radio"
              name="option"
              value={letter}
              checked={selectedOption === letter}
              onChange={() => setSelectedOption(letter)}
              className="mr-2"
            />
            <strong>{letter}.</strong> {opt}
          </label>
        ))}
      </div>

      {currentUserAnswer ? (
        <div className="mt-4 p-4 bg-gray-100 rounded">
          <p>
            <strong>Your Answer:</strong> {currentUserAnswer.userAnswer}
          </p>
          <p className={getScoreColor(currentUserAnswer.evaluation.score)}>
            ✅ Score: {currentUserAnswer.evaluation.score}% —{" "}
            {currentUserAnswer.evaluation.correct ? "Correct" : "Incorrect"}
          </p>
          <p>
            <strong>Feedback:</strong> {currentUserAnswer.evaluation.feedback}
          </p>
          <p>
            <strong>Justification:</strong>{" "}
            {currentUserAnswer.evaluation.justification}
          </p>
        </div>
      ) : (
        <button
          onClick={handleSubmitAnswer}
          disabled={!selectedOption}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          Submit Answer
        </button>
      )}

      <div className="flex justify-between mt-6">
        <button
          onClick={handlePrev}
          disabled={currentChallenge === 0}
          className="text-gray-600"
        >
          ← Previous
        </button>
        <button
          onClick={handleNext}
          disabled={
            currentChallenge === challenges.length - 1 || !currentUserAnswer
          }
          className="text-gray-600"
        >
          Next →
        </button>
      </div>
    </div>
  );
};

export default ChallengeMode;

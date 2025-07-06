import React, { useState, useEffect } from "react";
import {
  BookText,
  BrainCircuit,
  CheckCircle2,
  XCircle,
  Lightbulb,
  ChevronLeft,
  ChevronRight,
  RefreshCcw,
} from "lucide-react";
import { useDocument } from "../context/DocContext";

/**
 * ChallengeMode – MCQ practice component
 * -------------------------------------------------------------
 * • Generates document‑aware questions via backend.
 * • Modern glassy UI, blue‑cyan palette, no emojis.
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

  const [selectedOption, setSelectedOption] = useState("");
  const [showResults, setShowResults] = useState(false);
  const [showDetailed, setShowDetailed] = useState(false);

  useEffect(() => {
    setSelectedOption("");
    setShowDetailed(false);
  }, [currentChallenge]);

  /* --------------------------- helpers --------------------------- */
  const getAnswer = () => userAnswers.find((a) => a.questionIndex === currentChallenge);
  const color = (score) =>
    score >= 80 ? "text-emerald-600" : score >= 60 ? "text-amber-500" : "text-rose-600";
  const overall = () =>
    userAnswers.length
      ? Math.round(userAnswers.reduce((s, a) => s + (a.evaluation.score || 0), 0) / userAnswers.length)
      : 0;

  /* --------------------------- actions -------------------------- */
  const start = async () => {
    await generateChallenges();
    setShowResults(false);
  };
  const submit = async () => {
    if (!selectedOption) return;
    await submitChallengeAnswer(currentChallenge, selectedOption);
    setShowDetailed(true);
  };
  const next = () => currentChallenge < challenges.length - 1 && setCurrentChallenge(currentChallenge + 1);
  const prev = () => currentChallenge > 0 && setCurrentChallenge(currentChallenge - 1);

  /* ------------------------- UI states -------------------------- */
  if (!isUploaded)
    return (
      <div className="min-h-[300px] flex flex-col items-center justify-center rounded-3xl bg-white/80 dark:bg-slate-800/80 border border-slate-100 dark:border-slate-700 shadow-lg backdrop-blur-xl p-10 text-center">
        <BookText className="h-10 w-10 text-sky-600 mb-4" />
        <p className="text-lg text-slate-600 dark:text-slate-300">Upload a document to unlock Challenge Mode.</p>
      </div>
    );

  /* Results */
  if (showResults && userAnswers.length)
    return (
      <div className="max-w-3xl mx-auto w-full bg-white dark:bg-slate-900 rounded-3xl shadow-xl p-8 space-y-6 animate-fade-in">
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold flex items-center gap-2"><BrainCircuit className="h-6 w-6" /> Results</h2>
          <button onClick={start} className="flex items-center gap-2 bg-sky-600 hover:bg-sky-700 text-white px-4 py-2 rounded-lg">
            <RefreshCcw className="h-4 w-4" /> Retry
          </button>
        </div>
        <p className="text-lg font-semibold">Overall Score: <span className={`${color(overall())}`}>{overall()}%</span></p>
        {userAnswers.map((ans, i) => {
          const q = challenges.find((c) => c.id === ans.questionId);
          return (
            <div key={i} className="border border-slate-200 dark:border-slate-700 rounded-2xl p-5">
              <p className="font-medium mb-2">Q{i + 1}. {q?.question}</p>
              <p><span className="font-semibold">Your:</span> {ans.userAnswer}</p>
              <p className={`${color(ans.evaluation.score)} font-semibold mt-1`}>Score: {ans.evaluation.score}%</p>
              <p className="mt-1"><span className="font-semibold">Feedback:</span> {ans.evaluation.feedback}</p>
              <p className="mt-1"><span className="font-semibold">Justification:</span> {ans.evaluation.justification}</p>
            </div>
          );
        })}
      </div>
    );

  /* Start screen */
  if (!challenges.length)
    return (
      <div className="flex flex-col items-center justify-center bg-white dark:bg-slate-900 rounded-3xl shadow-xl p-12 space-y-6 max-w-xl mx-auto animate-fade-in">
        <BrainCircuit className="h-12 w-12 text-sky-600" />
        <h2 className="text-2xl font-bold">Challenge Mode</h2>
        <button onClick={start} className="bg-sky-600 hover:bg-sky-700 text-white px-8 py-3 rounded-xl">
          {isLoading ? "Loading…" : "Start Challenge"}
        </button>
      </div>
    );

  /* Quiz view */
  const q = challenges[currentChallenge];
  const answer = getAnswer();

  return (
    <div className="max-w-3xl mx-auto w-full bg-white dark:bg-slate-900 rounded-3xl shadow-xl p-8 space-y-6 animate-fade-in">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold flex items-center gap-2"><BrainCircuit className="h-5 w-5" /> Question {currentChallenge + 1}</h2>
        <button onClick={() => setShowResults(true)} className="text-sky-600 hover:underline text-sm">View Results</button>
      </div>
      <p className="text-lg font-medium mb-2">{q.question}</p>

      <div className="space-y-3">
        {Object.entries(q.options).map(([opt, txt]) => (
          <label key={opt} className={`flex items-start gap-3 p-4 rounded-xl border ${
            selectedOption === opt ? 'border-sky-500 bg-sky-50 dark:bg-sky-800/30' : 'border-slate-200 dark:border-slate-700'
          } cursor-pointer`}>
            <input type="radio" name="option" value={opt} checked={selectedOption === opt} onChange={() => setSelectedOption(opt)} className="mt-1" />
            <span><strong>{opt}.</strong> {txt}</span>
          </label>
        ))}
      </div>

      {answer ? (
        <div className={`mt-4 p-5 rounded-xl ${
          answer.evaluation.correct ? 'bg-emerald-50 dark:bg-emerald-800/20 border border-emerald-200 dark:border-emerald-600' : 'bg-rose-50 dark:bg-rose-800/20 border border-rose-200 dark:border-rose-600'
        }`}>
          <p className="flex items-center gap-2 font-medium">
            {answer.evaluation.correct ? <CheckCircle2 className="h-5 w-5 text-emerald-600" /> : <XCircle className="h-5 w-5 text-rose-600" />} 
            Score: {answer.evaluation.score}%
          </p>
          <p className="mt-1"><span className="font-semibold">Your:</span> {answer.userAnswer}</p>
          {showDetailed ? (
            <div className="mt-2 space-y-1 text-sm">
              <p><span className="font-semibold">Feedback:</span> {answer.evaluation.feedback}</p>
              <p><span className="font-semibold">Justification:</span> {answer.evaluation.justification}</p>
            </div>
          ) : (
            <button onClick={() => setShowDetailed(true)} className="text-sky-600 text-xs mt-2 hover:underline">Show Details</button>
          )}
        </div>
      ) : (
        <button onClick={submit} disabled={!selectedOption} className="bg-sky-600 hover:bg-sky-700 text-white px-8 py-2 rounded-xl disabled:opacity-40">Submit Answer</button>
      )}

      <div className="flex justify-between pt-6 text-slate-700 dark:text-slate-300 text-sm">
        <button onClick={prev} disabled={currentChallenge === 0} className="flex items-center gap-1 disabled:opacity-40"><ChevronLeft className="h-4 w-4"/>Prev</button>
        <button onClick={next} disabled={currentChallenge === challenges.length - 1 || !answer} className="flex items-center gap-1 disabled:opacity-40">Next<ChevronRight className="h-4 w-4"/></button>
      </div>
    </div>
  );
};

export default ChallengeMode;

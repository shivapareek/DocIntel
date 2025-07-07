import React, { useState, useEffect } from 'react';
import {
  FileText,
  ChevronDown,
  ChevronUp,
  BarChart,
  Target,
  HelpCircle,
  Clock,
} from 'lucide-react';

const DocumentSummary = ({ summary = '', fileName = 'Unknown file' }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [briefSummary, setBriefSummary] = useState('');

  useEffect(() => {
    if (!summary) return;
    const sentences = summary
      .split(/[.!?]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    const importantKeywords = [
  'main',
  'key',
  'important',
  'conclusion',
  'summary',
  'findings',
  'results',
  'analysis',
];

const keyPoints = [];
sentences.forEach((sent) => {
  const hasKeyword = importantKeywords.some((k) => sent.toLowerCase().includes(k));
  if (hasKeyword && keyPoints.length < 3) keyPoints.push(sent);
});

    const brief = (keyPoints.length ? keyPoints : sentences.slice(0, 3)).join('. ') + '.';
    setBriefSummary(brief);
  }, [summary]);

  if (!summary) return null;

  const wordCount = summary.split(/\s+/).length;
  const briefWordCount = briefSummary.split(/\s+/).length;

  return (
    <div className="relative rounded-2xl bg-white/80 dark:bg-slate-900/70 backdrop-blur-xl p-8 border border-white/20 dark:border-slate-700/50 shadow-xl shadow-blue-300/10 animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-sky-500 to-cyan-500 text-white rounded-xl flex items-center justify-center shadow-md">
            <FileText size={18} />
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white tracking-tight">Document Summary</h2>
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
            {isExpanded ? `${wordCount} words` : `${briefWordCount} words`}
          </span>
        </div>
        <button
          onClick={() => setIsExpanded((prev) => !prev)}
          className="flex items-center text-sm font-medium text-sky-600 dark:text-sky-300 hover:underline"
        >
          {isExpanded ? 'Show Brief' : 'Show Full'}
          {isExpanded ? <ChevronUp size={16} className="ml-1" /> : <ChevronDown size={16} className="ml-1" />}
        </button>
      </div>

      {isExpanded ? (
        <>
          <div className="mb-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-gray-600 dark:text-gray-300">
            <div className="bg-gradient-to-br from-blue-100 to-sky-100 dark:from-blue-900/20 dark:to-sky-900/20 rounded-xl px-4 py-3 flex items-center gap-2">
              <FileText size={14} className="text-blue-600 dark:text-blue-400" />
              <div>
                <strong className="block font-medium text-blue-700 dark:text-blue-300">Source</strong>
                {fileName}
              </div>
            </div>
            <div className="bg-gradient-to-br from-blue-100 to-sky-100 dark:from-blue-900/20 dark:to-sky-900/20 rounded-xl px-4 py-3 flex items-center gap-2">
              <Clock size={14} className="text-blue-600 dark:text-blue-400" />
              <div>
                <strong className="block font-medium text-blue-700 dark:text-blue-300">Generated</strong>
                {new Date().toLocaleString()}
              </div>
            </div>
          </div>

          <div className="prose max-w-none text-gray-800 dark:text-gray-100 leading-relaxed">
            {summary.split('\n').map((p, i) => p.trim() ? <p key={i} className="mb-4 last:mb-0">{p.trim()}</p> : null)}
          </div>

          <div className="mt-6 flex flex-wrap gap-3 text-sm">
            <span className="flex items-center gap-2 bg-sky-100 dark:bg-sky-900/40 text-sky-700 dark:text-sky-300 px-3 py-1 rounded-full">
              <BarChart size={14} /> Detailed Analysis
            </span>
            <span className="flex items-center gap-2 bg-blue-100 dark:bg-blue-800/40 text-blue-700 dark:text-blue-300 px-3 py-1 rounded-full">
              <Target size={14} /> Key Insights
            </span>
            <span className="flex items-center gap-2 bg-green-100 dark:bg-green-800/40 text-green-700 dark:text-green-300 px-3 py-1 rounded-full">
              <HelpCircle size={14} /> Ready for Q&A
            </span>
          </div>
        </>
      ) : (
        <>
          <div className="bg-gradient-to-br from-sky-50 to-blue-100 dark:from-blue-900/20 dark:to-sky-900/10 border-l-4 border-blue-400 rounded-xl p-4 text-gray-800 dark:text-gray-100 leading-relaxed">
            <h3 className="font-semibold text-blue-800 dark:text-blue-300 mb-2">Quick Summary</h3>
            <p>{briefSummary}</p>
          </div>

          <div className="mt-6 flex items-center justify-between text-xs text-gray-600 dark:text-gray-400">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1"><FileText size={12} /> {fileName}</span>
              <span className="flex items-center gap-1"><Clock size={12} /> Short Read</span>
            </div>
            <button
              onClick={() => setIsExpanded(true)}
              className="text-blue-600 hover:underline dark:text-blue-400 font-medium"
            >
              Read full summary →
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default DocumentSummary;

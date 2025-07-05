import React, { useState, useEffect } from 'react';

const DocumentSummary = ({ summary = '', fileName = 'Unknown file' }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [briefSummary, setBriefSummary] = useState('');

  /* ── Build a 2‑3 sentence brief summary ── */
  useEffect(() => {
    if (!summary) return;

    const sentences = summary
      .split(/[.!?]+/)
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

    /* Grab first 3 or sentences with key words */
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
      const hasKeyword = importantKeywords.some((k) =>
        sent.toLowerCase().includes(k),
      );
      if (hasKeyword && keyPoints.length < 3) keyPoints.push(sent);
    });

    const brief =
      (keyPoints.length ? keyPoints : sentences.slice(0, 3)).join('. ') + '.';
    setBriefSummary(brief);
  }, [summary]);

  if (!summary) return null;

  const wordCount = summary.split(/\s+/).length;
  const briefWordCount = briefSummary.split(/\s+/).length;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Heading */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <h2 className="text-xl font-semibold text-gray-900">
            Document Summary
          </h2>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            {isExpanded ? `${wordCount} words` : `${briefWordCount} words`}
          </span>
        </div>
        <button
          onClick={() => setIsExpanded((prev) => !prev)}
          className="text-sm text-gray-600 hover:text-gray-800 font-medium flex items-center space-x-1 transition-colors"
        >
          <span>{isExpanded ? 'Show Brief' : 'Show Full'}</span>
          <span
            className={`transform transition-transform ${
              isExpanded ? 'rotate-180' : ''
            }`}
          >
            ▼
          </span>
        </button>
      </div>

      {/* ── FULL SUMMARY ── */}
      {isExpanded ? (
        <div className="space-y-4">
          {/* Meta */}
          <div className="bg-gray-50 rounded-md p-4">
            <div className="flex items-center space-x-2 mb-1">
              <span className="text-sm font-medium text-gray-700">Source:</span>
              <span className="text-sm text-gray-600">{fileName}</span>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">
                Generated:
              </span>
              <span className="text-sm text-gray-600">
                {new Date().toLocaleString()}
              </span>
            </div>
          </div>

          {/* Body */}
          <div className="prose max-w-none text-gray-800 leading-relaxed">
            {summary.split('\n').map((p, i) =>
              p.trim() ? (
                <p key={i} className="mb-3 last:mb-0">
                  {p.trim()}
                </p>
              ) : null,
            )}
          </div>

          {/* Footer badges */}
          <div className="border-t pt-4 flex items-center justify-between text-sm text-gray-600">
            <div className="flex items-center space-x-4">
              <span className="flex items-center space-x-1">
                <span>📊</span>
                <span>Detailed analysis</span>
              </span>
              <span className="flex items-center space-x-1">
                <span>🎯</span>
                <span>Complete insights</span>
              </span>
            </div>
            <div className="flex items-center space-x-1">
              <span className="w-2 h-2 bg-green-400 rounded-full"></span>
              <span>Ready for questions</span>
            </div>
          </div>
        </div>
      ) : (
        /* ── BRIEF SUMMARY ── */
        <div className="space-y-4">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-md p-4 border-l-4 border-blue-400">
            <div className="flex items-start space-x-2">
              <span className="text-blue-600 mt-1">📋</span>
              <div>
                <h3 className="text-sm font-semibold text-blue-900 mb-1">
                  Quick Summary
                </h3>
                <p className="text-gray-700 text-sm leading-relaxed">
                  {briefSummary}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-md p-3">
            <div className="flex items-center justify-between text-xs text-gray-600">
              <div className="flex items-center space-x-3">
                <span className="flex items-center space-x-1">
                  <span>📄</span>
                  <span>Source: {fileName}</span>
                </span>
                <span className="flex items-center space-x-1">
                  <span>⏱️</span>
                  <span>Quick read</span>
                </span>
              </div>
              <button
                onClick={() => setIsExpanded(true)}
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                Read full summary →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentSummary;

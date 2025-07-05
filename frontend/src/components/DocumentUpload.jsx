import React, { useState, useRef } from "react";
import { useDocument } from "../context/DocContext";

const DocumentUpload = ({ setSummary, setFileName }) => {
  const {
    uploadDocument,          // context fn – does the real fetch
    isUploaded,
    fileName,
    fileSize,
    isLoading,
    error,
    resetDocument,
  } = useDocument();

  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  /* ───────────────── handleSelect ───────────────── */
  const handleFileSelect = async (file) => {
    if (!file) return;

    /* validate */
    const allowed = ["application/pdf", "text/plain"];
    if (!allowed.includes(file.type))
      return alert("Please upload only PDF or TXT files");
    if (file.size > 10 * 1024 * 1024)
      return alert("File size must be < 10 MB");

    try {
      /* ▸ trigger context upload (shows loader) */
      const data = await uploadDocument(file);   // <- single source of truth

      /* ▸ pass summary + filename up to App */
      setSummary(data.summary);
      setFileName(file.name);
    } catch (err) {
      console.error("Upload failed:", err);
    }
  };

  /* ───── drag‑n‑drop helpers ───── */
  const handleDrop = (e) => { e.preventDefault(); setDragOver(false); handleFileSelect(e.dataTransfer.files[0]); };
  const handleDragOver = (e) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setDragOver(false); };
  const handleInputChange = (e) => handleFileSelect(e.target.files[0]);
  const browseClick = () => fileInputRef.current?.click();

  /* pretty size */
  const fmt = (b) => { if (!b) return "0 Bytes"; const k=1024,i=Math.floor(Math.log(b)/Math.log(k)); return (b/Math.pow(k,i)).toFixed(2)+" "+["Bytes","KB","MB","GB"][i]; };

  /* ───────── Uploaded state ───────── */
  if (isUploaded) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Document Uploaded</h2>
          <button onClick={resetDocument} className="text-sm text-red-600 hover:text-red-800 font-medium">
            Upload New Document
          </button>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-md p-4">
          <div className="flex items-center">
            <span className="text-2xl">📄</span>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">{fileName}</h3>
              <p className="text-sm text-green-600">{fmt(fileSize)}</p>
            </div>
            <span className="ml-auto px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              ✓ Ready
            </span>
          </div>
        </div>

        <p className="mt-4 text-sm text-gray-600">
          You can now ask questions, take challenges, or view the summary below.
        </p>
      </div>
    );
  }

  /* ───────── Upload form ───────── */
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* heading */}
      <h2 className="text-xl font-semibold text-gray-900 mb-2">Upload Document</h2>
      <p className="text-sm text-gray-600 mb-4">
        Upload a PDF or TXT file to start analysing with AI assistance.
      </p>

      {/* error */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-3 flex">
          <span className="text-red-400 mr-2">⚠️</span>
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragOver ? "border-blue-400 bg-blue-50" : "border-gray-300 hover:border-gray-400"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt"
          onChange={handleInputChange}
          className="hidden"
        />
        <div className="space-y-4">
          <div className="text-6xl">📄</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            {dragOver ? "Drop your file here" : "Drag and drop your document"}
          </h3>
          <p className="text-sm text-gray-600">
            or{" "}
            <button
              onClick={browseClick}
              className="text-blue-600 hover:text-blue-800 font-medium"
              disabled={isLoading}
            >
              browse
            </button>
          </p>
          <p className="text-xs text-gray-500">PDF or TXT • Max 10 MB</p>
        </div>
      </div>

      {/* loader */}
      {isLoading && (
        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-md p-3 flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
          <p className="ml-3 text-sm text-blue-800">Processing your document…</p>
        </div>
      )}

      {/* what happens next */}
      <div className="mt-6 bg-gray-50 rounded-md p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">What happens next?</h4>
        <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
          <li>AI extracts text & builds vector index.</li>
          <li>Generates a brief 125‑150 word summary.</li>
          <li>You can ask questions or take a challenge quiz.</li>
          <li>Every answer cites exact document snippets.</li>
        </ul>
      </div>
    </div>
  );
};

export default DocumentUpload;

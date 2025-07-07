import React, { useState, useRef } from "react";
import { useDocument } from "../context/DocContext";
import { Upload, Loader2, CheckCircle2 } from "lucide-react";
import { useToast } from "../context/ToastContext"; // ✅ import

const DocumentUpload = ({ setSummary, setFileName }) => {
  const { showToast } = useToast(); // ✅ call toast
  const {
    uploadDocument,
    isUploaded,
    fileName,
    fileSize,
    isLoading,
    error,
    resetDocument,
  } = useDocument();

  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelect = async (file) => {
    if (!file) return;
    
    console.log("📁 File selected:", file.name, "Size:", file.size, "Type:", file.type);
    
    const allowed = ["application/pdf", "text/plain"];
    if (!allowed.includes(file.type)) {
      console.error("❌ Invalid file type:", file.type);
      showToast({ message: "Please upload only PDF or TXT files", type: "error" });
      return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
      console.error("❌ File too large:", file.size);
      showToast({ message: "File size must be < 10 MB", type: "error" });
      return;
    }

    // ✅ Check if file is empty
    if (file.size === 0) {
      console.error("❌ File is empty");
      showToast({ message: "Selected file is empty", type: "error" });
      return;
    }

    // ✅ For text files, let's read content to verify
    if (file.type === "text/plain") {
      try {
        const text = await file.text();
        console.log("📝 Text content preview:", text.substring(0, 100));
        
        if (!text.trim()) {
          console.error("❌ Text file has no content");
          showToast({ message: "Text file appears to be empty", type: "error" });
          return;
        }
      } catch (error) {
        console.error("❌ Error reading text file:", error);
        showToast({ message: "Error reading text file", type: "error" });
        return;
      }
    }

    try {
      console.log("🚀 Starting upload process...");
      const data = await uploadDocument(file);
      console.log("✅ Upload successful:", data);
      
      setSummary(data.summary);
      setFileName(file.name);
      showToast({ message: `${file.name} uploaded successfully!`, type: "success" });
      
    } catch (err) {
      console.error("❌ Upload failed:", err);
      showToast({ message: "Upload failed. Try again.", type: "error" });
    }
  };

  const handleDrop = (e) => { 
    e.preventDefault(); 
    setDragOver(false); 
    console.log("📂 File dropped:", e.dataTransfer.files[0]?.name);
    handleFileSelect(e.dataTransfer.files[0]); 
  };
  
  const handleDragOver = (e) => { 
    e.preventDefault(); 
    setDragOver(true); 
  };
  
  const handleDragLeave = (e) => { 
    e.preventDefault(); 
    setDragOver(false); 
  };
  
  const handleInputChange = (e) => {
    console.log("📁 File input changed:", e.target.files[0]?.name);
    handleFileSelect(e.target.files[0]);
  };
  
  const browseClick = () => fileInputRef.current?.click();
  
  const fmt = (b) => { 
    if (!b) return "0 Bytes"; 
    const k = 1024, i = Math.floor(Math.log(b) / Math.log(k)); 
    return (b / Math.pow(k, i)).toFixed(2) + " " + ["Bytes", "KB", "MB", "GB"][i]; 
  };

  if (isUploaded) {
    return (
      <div className="relative group animate-fade-in">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-2xl blur opacity-20 group-hover:opacity-30 transition-opacity"></div>
        <div className="relative bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-2xl p-8 border border-white/20 dark:border-slate-700/50 text-center">
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center">
              <CheckCircle2 className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-2xl font-bold text-blue-800 dark:text-cyan-300">Document Successfully Uploaded!</h2>
            <p className="text-sm text-gray-700 dark:text-gray-300">Filename: <span className="font-semibold">{fileName}</span> ({fmt(fileSize)})</p>
            <p className="text-sm text-gray-500 dark:text-gray-400">You can now view the summary, ask questions or take a challenge.</p>
            <button onClick={resetDocument} className="mt-4 px-6 py-2 rounded-xl font-medium bg-gradient-to-r from-rose-500 to-pink-500 text-white hover:shadow-lg hover:shadow-red-500/30 transition-all">Upload Another</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative group">
      <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-2xl blur opacity-25 group-hover:opacity-40 transition-opacity"></div>
      <div className="relative bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl rounded-2xl p-10 border border-white/20 dark:border-slate-700/50">
        <div className="text-center space-y-8">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center">
            <Upload className="w-8 h-8 text-white" />
          </div>
          <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
            Upload Your Document
          </h3>

          {error && <p className="text-red-500 text-sm font-medium">⚠ {error}</p>}

          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`transition-all duration-300 ease-in-out p-10 rounded-2xl border-2 border-dashed cursor-pointer ${
              dragOver
                ? "border-blue-400 bg-blue-100/40 dark:bg-blue-900/20"
                : "border-gray-300 hover:border-blue-400 dark:border-slate-600 dark:hover:border-blue-500"
            }`}
            onClick={browseClick}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt"
              onChange={handleInputChange}
              className="hidden"
            />
            <div className="space-y-2">
              <p className="text-xl font-semibold text-gray-800 dark:text-gray-100">
                {dragOver ? "Drop your file here" : "Drag and drop a file here"}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">or click anywhere to browse</p>
              <p className="text-xs text-gray-400">PDF or TXT • Max 10 MB</p>
            </div>
          </div>

          {isLoading && (
            <div className="mt-6 flex flex-col items-center gap-3 animate-pulse">
              <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
              <p className="text-sm font-medium text-blue-700 dark:text-blue-300">Processing your document…</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Extracting content, summarizing and building context...</p>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;
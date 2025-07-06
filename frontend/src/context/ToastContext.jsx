import React, { createContext, useContext, useState } from "react";

const ToastContext = createContext();

export const ToastProvider = ({ children }) => {
  const [toast, setToast] = useState(null);

  const showToast = ({ message, type = "success", duration = 3000 }) => {
    setToast({ message, type });
    setTimeout(() => setToast(null), duration);
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 animate-fade-in-up">
          <div
            className={`relative px-5 py-4 rounded-2xl shadow-xl backdrop-blur-md border border-white/20 dark:border-slate-700/40 text-sm font-semibold
              ${
                toast.type === "success"
                  ? "bg-gradient-to-r from-emerald-400/30 to-green-500/20 text-green-900 dark:text-green-200"
                  : "bg-gradient-to-r from-red-400/30 to-pink-500/20 text-red-900 dark:text-red-200"
              }`}
          >
            <div className="absolute top-0 left-0 w-full h-full rounded-2xl bg-white/10 dark:bg-black/10 blur-sm opacity-10 pointer-events-none"></div>
            <span className="relative z-10">{toast.message}</span>
          </div>
        </div>
      )}
    </ToastContext.Provider>
  );
};

export const useToast = () => useContext(ToastContext);

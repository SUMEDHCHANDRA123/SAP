import { createContext, useCallback, useContext, useState } from "react";

const ToastContext = createContext(null);

const TOAST_STYLES = {
  success: "bg-emerald-700 text-white border-emerald-600",
  error: "bg-red-600 text-white border-red-500",
  warning: "bg-amber-500 text-white border-amber-400",
};

function ToastItem({ toast, onDismiss }) {
  return (
    <div
      className={`animate-toast-in flex min-w-[280px] max-w-sm items-start justify-between gap-3 rounded-xl border px-4 py-3 text-sm shadow-xl ${TOAST_STYLES[toast.type] || TOAST_STYLES.success}`}
      role="alert"
    >
      <span className="flex-1 font-medium">{toast.message}</span>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        className="shrink-0 rounded p-0.5 opacity-80 hover:bg-white/20 hover:opacity-100"
        aria-label="Dismiss"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    (message, type = "success") => {
      const id = crypto.randomUUID();
      setToasts((prev) => [...prev, { id, message, type }]);
      setTimeout(() => dismiss(id), 3000);
    },
    [dismiss]
  );

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return ctx;
}

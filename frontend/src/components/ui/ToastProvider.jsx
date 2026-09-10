import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import { createContext, useCallback, useContext, useRef, useState } from "react";

const ToastContext = createContext(null);

const TONE_META = {
  success: { icon: CheckCircle2, className: "toast-success" },
  error: { icon: XCircle, className: "toast-error" },
  warning: { icon: AlertTriangle, className: "toast-warning" },
  info: { icon: Info, className: "toast-info" },
};

let idCounter = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const lastMessage = useRef({ text: "", at: 0 });

  const dismiss = useCallback((id) => {
    setToasts((list) => list.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback((text, tone = "info") => {
    // Collapse accidental duplicate toasts from one operation firing twice.
    const now = Date.now();
    if (lastMessage.current.text === text && now - lastMessage.current.at < 800) return;
    lastMessage.current = { text, at: now };

    const id = ++idCounter;
    setToasts((list) => [...list, { id, text, tone }]);
    setTimeout(() => dismiss(id), 4500);
  }, [dismiss]);

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div className="toast-stack" role="status" aria-live="polite">
        {toasts.map((t) => {
          const meta = TONE_META[t.tone] || TONE_META.info;
          const Icon = meta.icon;
          return (
            <div key={t.id} className={`toast ${meta.className}`}>
              <Icon size={17} />
              <span>{t.text}</span>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

/** useToast()("Athlete created successfully.", "success") */
export function useToast() {
  return useContext(ToastContext);
}

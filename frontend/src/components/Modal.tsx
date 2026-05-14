import { ReactNode, useEffect } from "react";
import { X } from "lucide-react";
export function Modal({ open, onClose, title, children }: {
  open: boolean; onClose: () => void; title: string; children: ReactNode;
}) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    if (open) window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-elegant w-full max-w-lg" onClick={(e)=>e.stopPropagation()}>
        <div className="flex items-center justify-between px-5 py-3 border-b">
          <h3 className="font-display text-xl">{title}</h3>
          <button onClick={onClose} className="text-ink/60 hover:text-ink"><X size={20}/></button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

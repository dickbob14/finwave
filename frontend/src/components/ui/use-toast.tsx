"use client"

import * as React from "react"

export interface Toast {
  id: string
  title?: string
  description?: string
  action?: React.ReactNode
  variant?: "default" | "destructive"
}

interface ToastContextType {
  toasts: Toast[]
  toast: (toast: Omit<Toast, "id">) => void
  dismiss: (toastId?: string) => void
}

const ToastContext = React.createContext<ToastContextType | undefined>(undefined)

let toastCount = 0

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([])

  const toast = React.useCallback((toast: Omit<Toast, "id">) => {
    const id = String(toastCount++)
    setToasts((toasts) => [...toasts, { ...toast, id }])
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
      setToasts((toasts) => toasts.filter((t) => t.id !== id))
    }, 5000)
  }, [])

  const dismiss = React.useCallback((toastId?: string) => {
    setToasts((toasts) => 
      toastId === undefined
        ? []
        : toasts.filter((t) => t.id !== toastId)
    )
  }, [])

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
      <div className="fixed bottom-0 right-0 z-50 m-4 flex flex-col gap-2">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={cn(
              "rounded-md p-4 shadow-lg",
              toast.variant === "destructive" 
                ? "bg-red-600 text-white" 
                : "bg-white border"
            )}
          >
            {toast.title && (
              <div className="font-medium">{toast.title}</div>
            )}
            {toast.description && (
              <div className="mt-1 text-sm opacity-90">{toast.description}</div>
            )}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = React.useContext(ToastContext)
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider")
  }
  return context
}

function cn(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}
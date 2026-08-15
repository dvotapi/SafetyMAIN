"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

export interface ModalEntry {
  id: string;
  node: ReactNode;
}

interface ModalStackContextValue {
  stack: ModalEntry[];
  push: (entry: ModalEntry) => void;
  pop: () => void;
  replace: (entry: ModalEntry) => void;
  clear: () => void;
}

const ModalStackContext = createContext<ModalStackContextValue | null>(null);

export function ModalStackProvider({ children }: { children: ReactNode }) {
  const [stack, setStack] = useState<ModalEntry[]>([]);

  const push = useCallback((entry: ModalEntry) => {
    setStack((current) => [...current, entry]);
  }, []);

  const pop = useCallback(() => {
    setStack((current) => current.slice(0, -1));
  }, []);

  const replace = useCallback((entry: ModalEntry) => {
    setStack((current) =>
      current.length === 0 ? [entry] : [...current.slice(0, -1), entry],
    );
  }, []);

  const clear = useCallback(() => {
    setStack([]);
  }, []);

  const value = useMemo(
    () => ({ stack, push, pop, replace, clear }),
    [stack, push, pop, replace, clear],
  );

  return (
    <ModalStackContext.Provider value={value}>
      {children}
      {stack.map((entry) => (
        <div key={entry.id}>{entry.node}</div>
      ))}
    </ModalStackContext.Provider>
  );
}

export function useModalStack() {
  const context = useContext(ModalStackContext);
  if (!context) {
    throw new Error("useModalStack must be used within ModalStackProvider");
  }
  return context;
}

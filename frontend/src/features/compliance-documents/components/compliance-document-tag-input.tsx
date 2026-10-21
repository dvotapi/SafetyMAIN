"use client";

import { useState, type KeyboardEvent } from "react";

import { Chip, Input } from "@/components";

export function ComplianceDocumentTagInput({
  id,
  values,
  onChange,
  disabled,
  invalid,
  placeholder,
}: {
  id: string;
  values: string[];
  onChange: (next: string[]) => void;
  disabled?: boolean;
  invalid?: boolean;
  placeholder?: string;
}) {
  const [draft, setDraft] = useState("");

  function commit() {
    const value = draft.trim();
    if (!value) return;
    if (values.includes(value)) {
      setDraft("");
      return;
    }
    onChange([...values, value]);
    setDraft("");
  }

  function remove(index: number) {
    const next = values.slice();
    next.splice(index, 1);
    onChange(next);
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      commit();
    } else if (event.key === "Backspace" && draft === "" && values.length > 0) {
      event.preventDefault();
      remove(values.length - 1);
    }
  }

  return (
    <div style={{ display: "grid", gap: "var(--sm-space-2)" }}>
      {values.length > 0 ? (
        <div
          style={{
            display: "flex",
            gap: "var(--sm-space-2)",
            flexWrap: "wrap",
          }}
        >
          {values.map((value, index) => (
            <Chip
              key={`${value}-${index}`}
              {...(!disabled
                ? {
                    onRemove: () => remove(index),
                    removeLabel: `Удалить ${value}`,
                  }
                : {})}
            >
              {value}
            </Chip>
          ))}
        </div>
      ) : null}
      <Input
        id={id}
        value={draft}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={onKeyDown}
        onBlur={commit}
        {...(disabled !== undefined ? { disabled } : {})}
        {...(invalid !== undefined ? { invalid } : {})}
        placeholder={placeholder ?? "Введите значение и Enter"}
        autoComplete="off"
      />
    </div>
  );
}

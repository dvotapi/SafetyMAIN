"use client";

import { forwardRef, type ChangeEvent } from "react";

import { Input, SearchInput } from "@/components/primitives/Input";
import { cx } from "@/utils/cx";

import styles from "./Filters.module.css";

export interface SearchProps {
  value?: string;
  onChange?: (value: string) => void;
  onClear?: () => void;
  placeholder?: string;
  useSearchInput?: boolean;
  className?: string;
  name?: string;
  "aria-label"?: string;
}

export const Search = forwardRef<HTMLInputElement, SearchProps>(function Search(
  {
    value,
    onChange,
    onClear,
    placeholder = "Поиск…",
    useSearchInput = true,
    className,
    name = "search",
    "aria-label": ariaLabel = "Поиск",
  },
  ref,
) {
  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    onChange?.(event.target.value);
  };

  if (useSearchInput) {
    return (
      <div className={cx(styles.searchWrap, className)}>
        <SearchInput
          ref={ref}
          name={name}
          value={value}
          placeholder={placeholder}
          aria-label={ariaLabel}
          onChange={handleChange}
          {...(onClear ? { onClear } : {})}
        />
      </div>
    );
  }

  return (
    <div className={cx(styles.searchWrap, className)}>
      <Input
        ref={ref}
        type="search"
        name={name}
        value={value}
        placeholder={placeholder}
        aria-label={ariaLabel}
        onChange={handleChange}
      />
    </div>
  );
});

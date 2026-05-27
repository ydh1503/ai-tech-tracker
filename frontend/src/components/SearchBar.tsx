"use client";

import { useState, useRef, type FormEvent, type KeyboardEvent } from "react";
import { useRouter } from "next/navigation";
import { fetchAutocomplete } from "@/lib/api";

interface SearchBarProps {
  defaultValue?: string;
  placeholder?: string;
}

export default function SearchBar({
  defaultValue = "",
  placeholder = "기술명 또는 키워드 검색...",
}: SearchBarProps) {
  const router = useRouter();
  const [query, setQuery] = useState(defaultValue);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    setShowSuggestions(false);
    router.push(`/search?q=${encodeURIComponent(trimmed)}`);
  }

  function handleInputChange(value: string) {
    setQuery(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!value.trim()) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      const results = await fetchAutocomplete(value);
      setSuggestions(results);
      setShowSuggestions(results.length > 0);
      setSelectedIndex(-1);
    }, 300);
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (!showSuggestions) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((i) => Math.min(i + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((i) => Math.max(i - 1, -1));
    } else if (e.key === "Enter" && selectedIndex >= 0) {
      e.preventDefault();
      const chosen = suggestions[selectedIndex];
      setQuery(chosen);
      setShowSuggestions(false);
      router.push(`/search?q=${encodeURIComponent(chosen)}`);
    } else if (e.key === "Escape") {
      setShowSuggestions(false);
    }
  }

  function handleSuggestionClick(suggestion: string) {
    setQuery(suggestion);
    setShowSuggestions(false);
    router.push(`/search?q=${encodeURIComponent(suggestion)}`);
  }

  return (
    <form onSubmit={handleSubmit} className="flex w-full max-w-xl gap-2">
      <div className="relative flex-1">
        {/* 돋보기 아이콘 */}
        <svg
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400"
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z"
          />
        </svg>
        <input
          type="search"
          value={query}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          placeholder={placeholder}
          className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 py-2 pl-9 pr-3 text-sm text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />

        {/* 자동완성 드롭다운 */}
        {showSuggestions && suggestions.length > 0 && (
          <ul className="absolute z-50 mt-1 w-full rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-lg max-h-60 overflow-auto">
            {suggestions.map((suggestion, index) => (
              <li key={suggestion}>
                <button
                  type="button"
                  onMouseDown={() => handleSuggestionClick(suggestion)}
                  className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                    index === selectedIndex
                      ? "bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300"
                      : "text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700"
                  }`}
                >
                  {suggestion}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      <button
        type="submit"
        className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
      >
        검색
      </button>
    </form>
  );
}

"use client";

import { useState, useRef, useEffect } from "react";

interface FilterInputProps {
  className?: string;
  onFilterAdded?: (filterId?: string) => void;
}

export default function FilterInput({ className = "", onFilterAdded }: FilterInputProps) {
  const [filterUrl, setFilterUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-focus the input when component mounts
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!filterUrl.trim()) {
      setError("Please enter a filter URL");
      return;
    }

    setIsLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const response = await fetch('/api/filters', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filterUrl: filterUrl.trim() }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setFilterUrl(""); // Clear input on success
        
        // Only show success message for new filters, not existing ones
        if (!data.isExistingFilter) {
          setSuccess(true);
          setTimeout(() => setSuccess(false), 2000); // Hide success message after 2s
        }
        
        // Notify parent component about the filter (new or existing)
        if (onFilterAdded) {
          onFilterAdded(data.filterId);
        }
      } else {
        setError(data.error || "Failed to process filter");
      }
    } catch (err) {
      setError("Network error occurred");
      console.error('Filter submission error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div ref={containerRef} className={`flex flex-col items-center gap-3 w-full max-w-[260px] ${className}`}>
      <form onSubmit={handleSubmit} className="relative w-full max-w-[260px]">
        <input
          ref={inputRef}
          type="url"
          value={filterUrl}
          onChange={(e) => setFilterUrl(e.target.value)}
          placeholder="Pipedrive filter URL"
          disabled={isLoading}
          className="w-full max-h-[36px] pl-3 pr-[60px] py-2 text-[12px] tracking-[0.03em] leading-[16px] font-light border border-gray-300 bg-white text-gray-900 focus:outline-none focus:border-gray-400 placeholder:text-gray-500 disabled:bg-gray-50 disabled:text-gray-500"
        />
        <button
          type="submit"
          disabled={isLoading || !filterUrl.trim()}
          className={`absolute right-3 top-1/2 transform -translate-y-1/2 px-[6px] py-[2px] text-[8px] leading-[12px] uppercase font-light transition-colors ${
            isLoading || !filterUrl.trim()
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-black text-white hover:bg-gray-800'
          }`}
        >
          {isLoading ? 'PROCESSING...' : 'SUBMIT'}
        </button>
      </form>
      
      {/* Error message */}
      {error && (
        <div className="text-[12px] text-red-600 font-light">
          {error}
        </div>
      )}
      
      {/* Success message */}
      {success && (
        <div className="text-[12px] text-green-600 font-light">
          Filter processed successfully
        </div>
      )}
    </div>
  );
}

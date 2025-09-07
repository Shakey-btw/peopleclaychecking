"use client";

import { useState, useEffect, useRef } from "react";

interface Filter {
  filter_id: string | null;
  filter_name: string;
  filter_url: string | null;
  organizations_count: number | null;
  created_at: string | null;
  last_used: string | null;
}

interface FilterSelectorProps {
  className?: string;
  onFilterSelect?: (filterId: string | null) => void;
  refreshTrigger?: number; // Add refresh trigger prop
  newlyAddedFilterId?: string | null; // Add newly added filter ID prop
  onShowFilterInput?: () => void; // Add callback for showing filter input
  isFilterInputVisible?: boolean; // Add prop to track if filter input is visible
}

export default function FilterSelector({ className = "", onFilterSelect, refreshTrigger, newlyAddedFilterId, onShowFilterInput, isFilterInputVisible = false }: FilterSelectorProps) {
  const [filters, setFilters] = useState<Filter[]>([]);
  const [selectedFilterId, setSelectedFilterId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fetch filters on component mount and when refreshTrigger changes
  useEffect(() => {
    fetchFilters();
  }, [refreshTrigger]);

  // Auto-select filter on mount or refresh
  useEffect(() => {
    if (filters.length > 0) {
      // If we have a newly added filter ID, select that specific filter
      if (newlyAddedFilterId) {
        const newlyAddedFilter = filters.find(f => f.filter_id === newlyAddedFilterId);
        if (newlyAddedFilter) {
          setSelectedFilterId(newlyAddedFilter.filter_id);
          if (onFilterSelect) {
            onFilterSelect(newlyAddedFilter.filter_id);
          }
        }
      } else if (selectedFilterId === null) {
        // Auto-select "Original Data" (null filterId) for UI state only
        setSelectedFilterId(null);
        if (onFilterSelect) {
          onFilterSelect(null);
        }
      }
    }
  }, [filters, newlyAddedFilterId]);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (isDropdownOpen && dropdownRef.current) {
        const target = event.target as Element;
        if (!dropdownRef.current.contains(target)) {
          setIsDropdownOpen(false);
        }
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  const fetchFilters = async () => {
    try {
      const response = await fetch('/api/filters');
      const data = await response.json();
      
      if (response.ok && data.filters) {
        setFilters(data.filters);
        // Don't set selectedFilterId here - let the useEffect handle it
      } else {
        setError(data.error || "Failed to fetch filters");
      }
    } catch (err) {
      setError("Network error occurred");
      console.error('Filter fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFilterClick = async (filterId: string | null) => {
    if (isProcessing) return;
    
    setSelectedFilterId(filterId);
    setIsProcessing(true);
    setError(null);

    try {
      const response = await fetch('/api/matching', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filterId, forceRefresh: false }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        // Log whether results came from cache or were freshly calculated
        if (data.fromCache) {
          console.log(`Results retrieved from cache for filter: ${filterId || 'All Organizations'}`);
        } else {
          console.log(`Results freshly calculated for filter: ${filterId || 'All Organizations'}`);
        }
        
        // Call the optional callback with filterId
        if (onFilterSelect) {
          onFilterSelect(filterId);
        }
      } else {
        setError(data.error || "Failed to run matching");
        // Revert selection on error
        setSelectedFilterId(selectedFilterId);
      }
    } catch (err) {
      setError("Network error occurred");
      console.error('Matching error:', err);
      // Revert selection on error
      setSelectedFilterId(selectedFilterId);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAddNewClick = () => {
    // Close the dropdown
    setIsDropdownOpen(false);
    // Show the filter input
    if (onShowFilterInput) {
      onShowFilterInput();
    }
  };

  if (isLoading) {
    return (
      <div className={`flex flex-col items-end gap-2 ${className}`}>
        <div className="text-[12px] text-gray-500 font-light">
          Loading filters...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex flex-col items-end gap-2 ${className}`}>
        <div className="text-[12px] text-red-600 font-light">
          {error}
        </div>
        <button
          onClick={fetchFilters}
          className="text-[12px] text-gray-600 font-light hover:text-gray-800 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div ref={dropdownRef} className="relative">
      <button 
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className={`text-[12px] tracking-[0.03em] leading-[16px] uppercase font-light mb-4 text-right pr-4 transition-colors cursor-pointer ${
          (isDropdownOpen || isFilterInputVisible) ? 'text-[#A9A9A9]' : 'text-black hover:opacity-70 transition-opacity'
        }`}
      >
        Filter
      </button>
      
      <div className={`absolute top-[38px] right-0 flex flex-col items-end gap-2 pr-4 ease-out overflow-hidden ${
        isDropdownOpen 
          ? 'opacity-100 max-h-96 pointer-events-auto transition-all duration-250' 
          : 'opacity-0 max-h-0 pointer-events-none transition-all duration-150'
      } ${className}`}>
          <div className="w-full max-w-[200px]">
              <div className="flex justify-between items-center">
                <span className="text-[12px] leading-[16px] uppercase font-light text-black tracking-[0.03em]">ALL</span>
                <button 
                  onClick={handleAddNewClick}
                  className="flex items-center gap-1 hover:opacity-70 transition-opacity cursor-pointer"
                >
                  <img src="/PlusIcon.svg" alt="Add" className="w-2 h-2" />
                  <span className="text-[12px] leading-[16px] uppercase font-light text-black tracking-[0.03em]">ADD NEW</span>
                </button>
              </div>
          </div>
          
          <div className="flex flex-col gap-1 max-w-[200px]">
          {filters.map((filter) => {
            const isSelected = selectedFilterId === filter.filter_id;
            const isOriginalData = filter.filter_id === null;
            
            return (
              <button
                key={filter.filter_id || 'original'}
                onClick={() => handleFilterClick(filter.filter_id)}
                disabled={isProcessing}
                className={`text-left px-[14px] py-1 text-[12px] tracking-[0.03em] leading-[16px] uppercase font-light transition-colors ${
                  isSelected
                    ? 'bg-[#1C1C1C] text-white'
                    : 'bg-[#E8E8E8] text-[#949494] hover:bg-[#E8E8E8]'
                } ${isProcessing ? 'opacity-50 cursor-default' : 'cursor-pointer'}`}
              >
                <div className="min-w-0">
                  <span className="block truncate">{filter.filter_name}</span>
                </div>
              </button>
            );
          })}
        </div>
        
          {isProcessing && (
            <div className="text-[12px] text-gray-500 font-light">
              Processing...
            </div>
          )}
        </div>
    </div>
  );
}

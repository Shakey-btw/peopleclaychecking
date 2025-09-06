// Shared types for the entire application

// API Response types (for future backend integration)
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface NormalizeOptions {
  trim: boolean;
  caseInsensitive: boolean;
}

export interface CompanyCheckingResult {
  aTotal: number;
  bTotal: number;
  aUnique: number;
  bUnique: number;
  matches: Set<string>;
  onlyA: Set<string>;
  onlyB: Set<string>;
}

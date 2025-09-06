import { NormalizeOptions } from "@/types";

export function splitLines(raw: string): string[] {
  if (!raw) return [];
  // Normalize CRLF/CR to LF and split
  return raw.replace(/\r\n?/g, "\n").split("\n");
}

export function normalizeLine(line: string, options: NormalizeOptions): string {
  let result = line;
  // Replace non-breaking spaces with regular spaces to avoid hidden mismatches
  result = result.replace(/\u00A0/g, " ");
  if (options.trim) {
    result = result.trim();
  }
  if (options.caseInsensitive) {
    result = result.toLowerCase();
  }
  return result;
}

export function toUniqueSet(
  lines: string[],
  options: NormalizeOptions
): {
  set: Set<string>;
  normalizedToOriginals: Map<string, string[]>;
  totalCount: number;
  uniqueCount: number;
} {
  const set = new Set<string>();
  const normalizedToOriginals = new Map<string, string[]>();
  let totalCount = 0;

  for (const raw of lines) {
    const normalized = normalizeLine(raw, options);
    if (normalized.length === 0) continue; // ignore blanks
    totalCount += 1;
    if (!set.has(normalized)) {
      set.add(normalized);
    }
    const arr = normalizedToOriginals.get(normalized) ?? [];
    arr.push(raw);
    normalizedToOriginals.set(normalized, arr);
  }

  return { set, normalizedToOriginals, totalCount, uniqueCount: set.size };
}



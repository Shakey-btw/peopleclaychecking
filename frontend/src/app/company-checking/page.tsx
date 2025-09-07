"use client";

import { useMemo, useState } from "react";
import { splitLines, toUniqueSet } from "@/lib/parse";
import { setDifference, setIntersection } from "@/lib/compare";
import { useDebouncedValue } from "@/hooks/useDebouncedValue";
import { NormalizeOptions } from "@/types";
import TopLeftNav from "@/components/navigation/TopLeftNav";

export default function Home() {
  const [textA, setTextA] = useState("");
  const [textB, setTextB] = useState("");
  const [trim, setTrim] = useState(false);
  const [caseInsensitive, setCaseInsensitive] = useState(false);

  // Navigation items for this page
  const navItems = [
    { id: "network-commit", label: "NETWORK UPLOAD", href: "/network-commit" },
    { id: "company-checking", label: "PEOPLE CHECKING", href: "/company-checking" },
    { id: "approach", label: "APPROACH", href: "/approach" },
  ];

  const debouncedA = useDebouncedValue(textA, 150);
  const debouncedB = useDebouncedValue(textB, 150);

  const options: NormalizeOptions = useMemo(
    () => ({ trim, caseInsensitive }),
    [trim, caseInsensitive]
  );

  const results = useMemo(() => {
    const linesA = splitLines(debouncedA);
    const linesB = splitLines(debouncedB);

    const a = toUniqueSet(linesA, options);
    const b = toUniqueSet(linesB, options);

    const matches = setIntersection(a.set, b.set);
    const onlyA = setDifference(a.set, b.set);
    const onlyB = setDifference(b.set, a.set);

    return {
      aTotal: a.totalCount,
      bTotal: b.totalCount,
      aUnique: a.uniqueCount,
      bUnique: b.uniqueCount,
      matches,
      onlyA,
      onlyB,
    };
  }, [debouncedA, debouncedB, options]);

  // no expandable lists; copy-only chips

  return (
    <main className="min-h-screen bg-white p-4 sm:p-6 flex flex-col items-center">
      {/* Top Left Navigation */}
      <div className="absolute top-[40px] left-6">
        <TopLeftNav items={navItems} />
      </div>
      
      <div className="w-full max-w-4xl flex-1 flex flex-col justify-center">
        {/* Top controls removed (moved under right input) */}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <section className="flex flex-col">
            <div className="mb-2">
              <h2 className="text-xs tracking-wide uppercase font-normal text-gray-900">COMPANY LEVEL</h2>
            </div>
            <textarea
              value={textA}
              onChange={(e) => setTextA(e.target.value)}
              placeholder={`Paste company names here, one per line`}
              className="w-full h-[300px] resize-none font-mono whitespace-pre-wrap break-words p-3 rounded-none border border-gray-300 bg-white text-gray-900 focus:outline-none focus:border-gray-400 placeholder:text-gray-500"
            />
          </section>

          <section className="flex flex-col">
            <div className="mb-2">
              <h2 className="text-xs tracking-wide uppercase font-normal text-gray-900">PEOPLE LEVEL</h2>
            </div>
            <textarea
              value={textB}
              onChange={(e) => setTextB(e.target.value)}
              placeholder={`Paste company names here, one per line`}
              className="w-full h-[300px] resize-none font-mono whitespace-pre-wrap break-words p-3 rounded-none border border-gray-300 bg-white text-gray-900 focus:outline-none focus:border-gray-400 placeholder:text-gray-500"
            />
          </section>
        </div>

        {/* Labels + Toggles in one row with space-between */}
        <div className="mt-5 flex items-center justify-between gap-3">
          <CopyChips
            results={results}
            options={options}
            textA={debouncedA}
            textB={debouncedB}
            className="flex flex-wrap gap-3"
          />

          <div className="hidden flex items-center justify-end gap-3">
            <label className="flex items-center gap-2 text-[12px] text-gray-800">
              <input type="checkbox" className="h-4 w-4 accent-black" checked={trim} onChange={(e) => setTrim(e.target.checked)} />
              Trim spaces
            </label>
            <label className="flex items-center gap-2 text-[12px] text-gray-800">
              <input
                type="checkbox"
                className="h-4 w-4 accent-black"
                checked={caseInsensitive}
                onChange={(e) => setCaseInsensitive(e.target.checked)}
              />
              Case insensitive
            </label>
          </div>
        </div>
      </div>
    </main>
  );
}

function CopyChips({
  results,
  options,
  textA,
  textB,
  className,
}: {
  results: {
    aTotal: number;
    bTotal: number;
    aUnique: number;
    bUnique: number;
    matches: Set<string>;
    onlyA: Set<string>;
    onlyB: Set<string>;
  };
  options: NormalizeOptions;
  textA: string;
  textB: string;
  className?: string;
}) {
  const [cooldown, setCooldown] = useState<string | null>(null);

  function getOriginalList(keys: Set<string>): string[] {
    // Prefer originals from A, fall back to B
    const a = toUniqueSet(splitLines(textA), options);
    const b = toUniqueSet(splitLines(textB), options);
    const out: string[] = [];
    for (const k of keys) {
      const originals = a.normalizedToOriginals.get(k) ?? b.normalizedToOriginals.get(k) ?? [k];
      out.push(originals[0]);
    }
    return out;
  }

  async function copy(label: string, keys: Set<string>) {
    if (cooldown) return;
    const lines = getOriginalList(keys).join("\n");
    await navigator.clipboard.writeText(lines);
    setCooldown(label);
    setTimeout(() => setCooldown(null), 1000);
  }

  const base = "cursor-pointer rounded px-2 py-1 text-sm select-none transition-colors";
  const normal = "bg-gray-100 text-gray-800";
  const active = "bg-gray-200"; // ~5-10% darker

  return (
    <div className={className ?? "mt-6 flex flex-wrap gap-3"}>
      <button
        type="button"
        disabled={cooldown === "onlyA"}
        onClick={() => copy("onlyA", results.onlyA)}
        className={`${base} ${cooldown === "onlyA" ? active : normal}`}
        title="Copy only-in-A to clipboard"
      >
        <span className="text-[12px]">Clay missed: {results.onlyA.size}</span>
      </button>
      <button
        type="button"
        disabled={cooldown === "matches"}
        onClick={() => copy("matches", results.matches)}
        className={`${base} ${cooldown === "matches" ? active : normal}`}
        title="Copy matches to clipboard"
      >
        <span className="text-[12px]">Matches: {results.matches.size}</span>
      </button>
      <button
        type="button"
        disabled={cooldown === "onlyB"}
        onClick={() => copy("onlyB", results.onlyB)}
        className={`${base} ${cooldown === "onlyB" ? active : normal} hidden`}
        title="Copy only-in-B to clipboard"
      >
        <span className="text-[12px]">Only in B: {results.onlyB.size}</span>
      </button>
    </div>
  );
}


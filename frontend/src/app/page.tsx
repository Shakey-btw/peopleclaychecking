"use client";

import TopLeftNav from "@/components/navigation/TopLeftNav";

export default function Home() {
  // Navigation items for this page
  const navItems = [
    { id: "network-commit", label: "NETWORK UPLOAD", href: "/network-commit" },
    { id: "company-checking", label: "PEOPLE CHECKING", href: "/company-checking" },
    { id: "approach", label: "APPROACH", href: "/approach" },
  ];

  return (
    <main className="min-h-screen bg-white p-4 sm:p-6">
      {/* Top Left Navigation */}
      <div className="absolute top-[40px] left-6">
        <TopLeftNav items={navItems} />
      </div>
      
      <div className="mx-auto max-w-4xl">
        {/* Heading removed */}
      </div>
    </main>
  );
}

"use client";

import { useState, useEffect, useRef } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";

export type NavItem = {
  id: string;
  label: string;
  href: string;
  icon?: React.ReactNode;
};

export type TopLeftNavProps = {
  items: NavItem[];
  className?: string;
};

export default function TopLeftNav({ items, className = "" }: TopLeftNavProps) {
  const pathname = usePathname();
  const [activeId, setActiveId] = useState<string>("");
  const itemRefs = useRef<Record<string, HTMLDivElement | null>>({});

  // Set initial active state based on current route
  useEffect(() => {
    const currentItem = items.find(item => item.href === pathname);
    setActiveId(currentItem?.id || ""); // No fallback - if no match, no active item
  }, [pathname, items]);

  // Calculate dot position based on active item
  const getDotPosition = () => {
    if (!activeId || !itemRefs.current[activeId]) return 0;
    const element = itemRefs.current[activeId];
    if (!element) return 0;
    
    const rect = element.getBoundingClientRect();
    const containerRect = element.closest('.nav-container')?.getBoundingClientRect();
    
    if (!containerRect) return rect.top;
    return rect.top - containerRect.top + rect.height / 2 - 3; // Center dot vertically
  };

  const handleItemClick = (item: NavItem) => {
    setActiveId(item.id);
  };

  if (!items.length) return null;

  return (
    <nav className={`relative nav-container ${className}`}>
      {/* Animated dot indicator - only show when there's an active item */}
      {activeId && (
        <motion.div
          className="absolute left-0 w-[6px] h-[6px] bg-black rounded-full z-10"
          animate={{ top: getDotPosition() }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          style={{ top: getDotPosition() }}
        />
      )}
      
      {/* Navigation items */}
      <div className="flex flex-col items-start gap-[4px] pl-4">
        {items.map((item) => (
                      <div
              key={item.id}
              ref={(el) => {
                itemRefs.current[item.id] = el;
              }}
              className="relative"
            >
            <Link
              href={item.href}
              onClick={() => handleItemClick(item)}
              className={`flex items-center gap-[6px] pl-0 pr-2 py-1 text-[12px] tracking-[0.03em] leading-[16px] uppercase font-light transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-black focus-visible:ring-offset-2 ${
                activeId === item.id
                  ? "font-light text-black"
                  : "text-black/70 hover:text-black"
              }`}
            >
              {item.icon && <span className="w-4 h-4">{item.icon}</span>}
              {item.label}
            </Link>
          </div>
        ))}
      </div>
    </nav>
  );
}

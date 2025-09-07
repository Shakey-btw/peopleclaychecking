"use client";

import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import TopLeftNav from "@/components/navigation/TopLeftNav";
import FilterSelector from "@/components/FilterSelector";
import FilterInput from "@/components/FilterInput";

interface PieData {
  running: number;
  notActive: number;
}

export default function ApproachPage() {
  const svgRef = useRef<SVGSVGElement>(null);
  const [pieData, setPieData] = useState<PieData | null>(null);
  const [selectedFilterId, setSelectedFilterId] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [newlyAddedFilterId, setNewlyAddedFilterId] = useState<string | null>(null);
  const [showFilterInput, setShowFilterInput] = useState(false);
  const previousPieDataRef = useRef<PieData | null>(null);

  // Helper function to format numbers with dots as thousands separators
  const formatNumber = (num: number): string => {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  };

  // Navigation items for this page
  const navItems = [
    { id: "network-commit", label: "NETWORK UPLOAD", href: "/network-commit" },
    { id: "company-checking", label: "PEOPLE CHECKING", href: "/company-checking" },
    { id: "approach", label: "APPROACH", href: "/approach" },
  ];

  // Function to fetch data from backend with filter context
  const fetchPieData = async (filterId: string | null = null) => {
    try {
      const url = filterId !== null 
        ? `/api/pie-data?filterId=${encodeURIComponent(filterId)}`
        : '/api/pie-data?filterId=null';
      
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.hasData) {
        setPieData({ running: data.running, notActive: data.notActive });
        console.log(`Pie data updated for filter: ${data.filterName || 'All Organizations'} (${data.running} running, ${data.notActive} not active)`);
      } else {
        // No data available for this filter yet
        setPieData({ running: 0, notActive: 0 });
        console.log(`No data available for filter: ${filterId || 'All Organizations'}`);
      }
    } catch (error) {
      console.error('Error fetching pie data:', error);
      // Fallback to default data
      setPieData({ running: 426, notActive: 8682 });
    }
  };

  // Handle filter selection from FilterSelector
  const handleFilterSelect = (filterId: string | null) => {
    setSelectedFilterId(filterId);
    // Fetch pie data for the selected filter
    fetchPieData(filterId);
  };

  // Handle when a new filter is added
  const handleFilterAdded = (filterId?: string) => {
    // Store the newly added filter ID
    setNewlyAddedFilterId(filterId || null);
    
    // Refresh the filter list in FilterSelector
    setRefreshTrigger(prev => prev + 1);
    
    // Hide the filter input after successful addition
    setShowFilterInput(false);
  };

  // Handle showing the filter input
  const handleShowFilterInput = () => {
    setShowFilterInput(true);
  };

  useEffect(() => {
    // Fetch data when component mounts (default to "All Organizations")
    fetchPieData(null);
  }, []);

  // Handle click outside to close filter input
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (showFilterInput) {
        const target = event.target as Element;
        // Check if click is outside the filter input container
        const filterInputContainer = document.querySelector('[data-filter-input]');
        if (filterInputContainer && !filterInputContainer.contains(target)) {
          setShowFilterInput(false);
        }
      }
    };

    if (showFilterInput) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showFilterInput]);

  useEffect(() => {
    if (!svgRef.current || !pieData) return;

    // Use dynamic data from state - running is the light gray piece, notActive is the black piece
    const data = [pieData.notActive, pieData.running]; // Black piece first, then running piece
    const total = pieData.notActive + pieData.running;

    // Set up dimensions - increased to accommodate hover text
    const pieSize = 360;
    const hoverPadding = 80; // Extra space for hover text
    const width = pieSize + hoverPadding;
    const height = pieSize + hoverPadding;
    const radius = pieSize / 2;

    // Create or get existing SVG
    let svg = d3.select(svgRef.current);
    let g = svg.select<SVGGElement>(".pie-group");
    
    // If this is the first render, create the SVG structure
    if (g.empty()) {
      svg = d3.select(svgRef.current)
        .attr("width", width)
        .attr("height", height);

      g = svg.append("g")
        .attr("class", "pie-group")
        .attr("transform", `translate(${width / 2}, ${height / 2})`);
    }

    // Create pie generator
    const pie = d3.pie<number>()
      .value((d: number) => d)
      .padAngle(0.03) // 6px gap between pieces (approximately 0.03 radians)
      .startAngle(-Math.PI / 0.8); // Start more to the left (8:00 o'clock position)

    // Create arc generator for donut chart
    const arc = d3.arc<d3.PieArcDatum<number>>()
      .innerRadius(radius * 0.4) // 40% of outer radius for donut hole
      .outerRadius(radius)
      .cornerRadius(10); // 10px corner radius

    // Get or create arcs group
    let arcs = g.selectAll(".arc");

    // Check if this is the first render or if we have previous data for smooth transitions
    const isFirstRender = previousPieDataRef.current === null;
    const previousData = previousPieDataRef.current ? 
      [previousPieDataRef.current.notActive, previousPieDataRef.current.running] : 
      data;

    // Create centered label group for donut hole (only if it doesn't exist)
    let centerGroup = g.select<SVGGElement>(".center-label");
    if (centerGroup.empty()) {
      centerGroup = g.append("g")
        .attr("class", "center-label")
        .style("opacity", 0);
    }

    // Handle smooth transitions for arc paths
    if (isFirstRender) {
      // First render - create arcs without transition
      arcs = (arcs as any).data(pie(data))
        .enter()
        .append("g")
        .attr("class", "arc");

      arcs.append("path")
        .attr("d", (d: any) => arc(d))
        .attr("fill", (d: any, i: number) => i === 0 ? "#1C1C1C" : "#E8E8E8")
        .style("cursor", "pointer")
        .each(function(d: any) { (this as any)._current = d; }); // Store current data for future transitions
    } else {
      // Subsequent renders - smooth transitions
      arcs = (arcs as any).data(pie(data));

      // Update existing paths with smooth transitions
      arcs.select("path")
        .transition()
        .duration(800)
        .ease(d3.easeCubicInOut)
        .attrTween("d", function(d: any) {
          const current = (this as any)._current;
          const interpolate = d3.interpolate(current, d);
          (this as any)._current = interpolate(0);
          return function(t: number) {
            return arc(interpolate(t)) || "";
          };
        });

      // Handle new arcs (if any)
      const newArcs = arcs.enter()
        .append("g")
        .attr("class", "arc");

      newArcs.append("path")
        .attr("d", (d: any) => arc(d))
        .attr("fill", (d: any, i: number) => i === 0 ? "#1C1C1C" : "#E8E8E8")
        .style("cursor", "pointer")
        .each(function(d: any) { (this as any)._current = d; });

      // Remove old arcs (if any)
      arcs.exit()
        .transition()
        .duration(400)
        .style("opacity", 0)
        .remove();
    }

    // Add hover interactions to all paths
    g.selectAll(".arc path")
      .on("mouseover", function(event, d) {
        // Add lift effect to the hovered piece
        const path = d3.select(this);
        const arcData = d as d3.PieArcDatum<number>;
        
        // Apply lift effect: scale up and add shadow
        path.transition()
          .duration(200)
          .attr("transform", `translate(${arc.centroid(arcData)[0] * 0.025}, ${arc.centroid(arcData)[1] * 0.025}) scale(1.0125)`)
          .style("filter", "drop-shadow(0 1px 2px rgba(0, 0, 0, 0.05))");
        
        // Smooth transition: fade out, change content, fade in
        centerGroup.transition()
          .duration(86)
          .style("opacity", 0)
          .on("end", function() {
            // Clear existing center label content
            centerGroup.selectAll("*").remove();
            
            // Add status text (first line)
            centerGroup.append("text")
              .attr("text-anchor", "middle")
              .attr("font-family", "Libre Franklin, system-ui, -apple-system, sans-serif")
              .attr("font-size", "14px")
              .attr("line-height", "18px")
              .attr("letter-spacing", "0.03em")
              .attr("font-weight", "300")
              .attr("fill", "#000000")
              .attr("y", -9) // Center vertically with line height
              .text(arcData.index === 0 ? "not active" : "running");
            
            // Add company count (second line)
            centerGroup.append("text")
              .attr("text-anchor", "middle")
              .attr("font-family", "Libre Franklin, system-ui, -apple-system, sans-serif")
              .attr("font-size", "14px")
              .attr("line-height", "18px")
              .attr("letter-spacing", "0.03em")
              .attr("font-weight", "300")
              .attr("fill", "#949494")
              .attr("y", 9) // Center vertically with line height
              .text(formatNumber(arcData.value));
            
            // Animate fade-in
            centerGroup.transition()
              .duration(86)
              .style("opacity", 1);
          });
      })
      .on("mouseout", function() {
        // Remove lift effect
        const path = d3.select(this);
        path.transition()
          .duration(200)
          .attr("transform", "translate(0, 0) scale(1)")
          .style("filter", "none");
        
        // Fade out center label
        centerGroup.transition()
          .duration(120)
          .style("opacity", 0);
      });

    // No permanent labels - only hover labels in center

    // Store current pie data for next transition
    previousPieDataRef.current = pieData;

  }, [pieData]); // Re-render when pieData changes

  return (
    <main className="min-h-screen bg-white flex items-center justify-center">
      {/* Top Left Navigation */}
      <div className="absolute top-[40px] left-6">
        <TopLeftNav items={navItems} />
      </div>
      
      {/* Top Right Filter Selector */}
      <div className="absolute top-[40px] right-6">
        <FilterSelector 
          onFilterSelect={handleFilterSelect} 
          refreshTrigger={refreshTrigger}
          newlyAddedFilterId={newlyAddedFilterId}
          onShowFilterInput={handleShowFilterInput}
          isFilterInputVisible={showFilterInput}
        />
      </div>
      
      {/* Filter Input - positioned below FilterSelector when showFilterInput is true */}
      {showFilterInput && (
        <div data-filter-input className="absolute top-[76px] right-6 w-full max-w-[260px] pr-4">
          <FilterInput onFilterAdded={handleFilterAdded} />
        </div>
      )}
      
      <svg ref={svgRef}></svg>
    </main>
  );
}

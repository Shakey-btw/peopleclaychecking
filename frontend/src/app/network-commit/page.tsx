"use client";

import { useState } from "react";
import TopLeftNav from "@/components/navigation/TopLeftNav";

export default function NetworkCommit() {
  const [headers, setHeaders] = useState<string[]>([]);
  const [rows, setRows] = useState<string[][]>([]);
  const [showPopup, setShowPopup] = useState(false);
  const [headerMappings, setHeaderMappings] = useState<Record<string, 'Company name' | 'Person Email' | null>>({});
  const [checkedHeaders, setCheckedHeaders] = useState<Set<number>>(new Set());
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Navigation items for this page
  const navItems = [
    { id: "network-commit", label: "NETWORK UPLOAD", href: "/network-commit" },
    { id: "company-checking", label: "PEOPLE CHECKING", href: "/company-checking" },
    { id: "approach", label: "APPROACH", href: "/approach" },
  ];

  // Reset function to return to initial state
  const resetToInitialState = () => {
    setHeaders([]);
    setRows([]);
    setShowPopup(false);
    setHeaderMappings({});
    setCheckedHeaders(new Set());
    setIsSubmitting(false);
    
    // Reset the file input so it can be used again
    const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = '';
    }
    
    console.log('Reset to initial state completed');
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      console.log('Selected file:', file.name);
      
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        const lines = text.split('\n');
        
        if (lines.length > 0) {
          // Extract headers (first line) and clean them
          const headers = lines[0].split(',').map(header => header.trim().replace(/"/g, ''));
          setHeaders(headers);
          
          // Extract rows (remaining lines, excluding empty ones)
          const rows = lines.slice(1)
            .filter(line => line.trim() !== '')
            .map(line => line.split(',').map(cell => cell.trim()));
          setRows(rows);
          
          // Show the popup
          setShowPopup(true);
        }
      };
      reader.readAsText(file);
    }
  };

  return (
    <main className="h-screen max-h-screen bg-white p-4 sm:p-6 overflow-hidden">
      {/* Top Left Navigation */}
      <div className="absolute top-[40px] left-6">
        <TopLeftNav items={navItems} />
      </div>
      
      {/* Main Content - Centered */}
      <div className="flex items-center justify-center h-full">
        <label className="cursor-pointer">
        <input
          type="file"
          accept=".csv"
          onChange={handleFileUpload}
          className="hidden"
        />
        <div className="inline-flex items-center gap-[4px] px-6 py-3 text-[12px] tracking-[0.03em] leading-[16px] font-light">
          <svg className="w-[12px] h-[12px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          UPLOAD CSV FILE
        </div>
      </label>
      </div>

      {/* Popup Overlay */}
      {showPopup && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          {/* Main Popup Container */}
          <div className="w-[620px] h-[500px] bg-white border border-[#C1C1C1] border-opacity-50 flex flex-col pt-5 px-2">
            {/* Top Section - Fixed Headings (Not Scrollable) */}
            <div className="flex gap-6 p-4 bg-white">
              <div className="flex-1">
                <h3 className="text-[12px] tracking-[0.03em] leading-[16px] font-light">
                  
                  DETECTED COLUMNS
                </h3>
              </div>
              <div className="flex-1">
                <h3 className="text-[12px] tracking-[0.03em] leading-[16px] font-light">
                  CHOSEN COLUMNS
                </h3>
              </div>
            </div>
            
            {/* Middle Section - Scrollable Content */}
            <div className="flex gap-6 p-4 flex-1 overflow-y-auto">
              {/* Left Side - Detected Columns */}
              <div className="flex-1">
                <div className="space-y-5">
                  {headers.map((header, index) => (
                    <div key={index} className="h-6 flex items-center gap-[6px]">
                      <input
                        type="checkbox"
                        className="w-4 h-4 accent-black"
                        checked={checkedHeaders.has(index)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setCheckedHeaders(prev => new Set([...prev, index]));
                          } else {
                            setCheckedHeaders(prev => {
                              const newSet = new Set(prev);
                              newSet.delete(index);
                              return newSet;
                            });
                            // Clear the mapping when unchecking
                            setHeaderMappings(prev => {
                              const newMappings = { ...prev };
                              delete newMappings[header];
                              return newMappings;
                            });
                          }
                        }}
                      />
                      <span className="text-[16px] tracking-[0.03em] leading-[16px] font-light">
                        {header}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Right Side - Chosen Columns */}
              <div className="flex-1">
                <div className="space-y-5">
                  {headers.map((header, index) => (
                    <div key={index} className="h-6 flex items-center justify-center">
                      {/* Dropdown is always in the same div, just hidden/shown */}
                      {checkedHeaders.has(index) && (
                        <select 
                          className={`w-full text-[16px] tracking-[0.03em] leading-[16px] font-light border border-[#A8A8A8] border-opacity-50 px-1 py-1 bg-white`}
                          value={headerMappings[header] || ""}
                          onChange={(e) => {
                            setHeaderMappings(prev => ({
                              ...prev,
                              [header]: e.target.value as 'Company name' | 'Person Email'
                            }));
                          }}
                        >
                          <option value="">select</option>
                          {/* Only show options that aren't already selected in other dropdowns */}
                          {!Object.values(headerMappings).includes('Company name') && (
                            <option value="Company name">Company name</option>
                          )}
                          {!Object.values(headerMappings).includes('Person Email') && (
                            <option value="Person Email">Person Email</option>
                          )}
                        </select>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
            
            {/* Bottom Section - Submit Button */}
            <div className="py-3 px-4 bg-white flex justify-end">
              {Object.values(headerMappings).includes('Company name') && Object.values(headerMappings).includes('Person Email') && (
                <button
                  className={`text-white text-[12px] tracking-[0.03em] leading-[16px] font-light py-[6px] px-[10px] rounded-none mr-[14px] ${isSubmitting ? 'bg-gray-500 cursor-not-allowed' : 'bg-black hover:bg-gray-800'}`}
                  disabled={isSubmitting}
                  onClick={async () => {
                    if (isSubmitting) return;
                    
                    setIsSubmitting(true);
                    console.log('Starting submission...');
                    
                    try {
                      // Step 4: Process and send data to make
                      const companyHeader = Object.keys(headerMappings).find(key => headerMappings[key] === 'Company name');
                      const emailHeader = Object.keys(headerMappings).find(key => headerMappings[key] === 'Person Email');
                      
                      console.log('Mapped headers:', { companyHeader, emailHeader });
                      console.log('Current headerMappings:', headerMappings);
                      
                      if (!companyHeader || !emailHeader) {
                        throw new Error('Required headers not found');
                      }
                      
                      const companyIndex = headers.indexOf(companyHeader);
                      const emailIndex = headers.indexOf(emailHeader);
                      
                      console.log('Column indices:', { companyIndex, emailIndex });
                      console.log('Total rows:', rows.length);
                      
                      // Extract mapped column data with headers
                      const processedData = {
                        headers: {
                          company: companyHeader,
                          email: emailHeader
                        },
                        data: rows.map(row => ({
                          company: (row[companyIndex] || '').replace(/"/g, '').trim(),
                          email: (row[emailIndex] || '').replace(/"/g, '').trim()
                        })).filter(item => item.company !== '' || item.email !== '') // Filter out empty rows
                      };
                      
                      console.log('Processed data:', processedData);
                      
                      // Send to make webhook
                      const response = await fetch('https://hook.eu1.make.com/7rtu9lm9cdstm2qfdnktpy6jnn9irhph', {
                        method: 'POST',
                        headers: {
                          'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(processedData)
                      });
                      
                      if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                      }
                      
                      console.log('Success! Response status:', response.status);
                      
                      // Success - reset to initial state
                      resetToInitialState();
                      
                    } catch (error) {
                      console.error('Error sending data:', error);
                      
                      // Error - also reset to initial state
                      resetToInitialState();
                    } finally {
                      setIsSubmitting(false);
                    }
                  }}
                >
                  {isSubmitting ? 'Sending...' : 'Submit'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

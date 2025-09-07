import { NextRequest, NextResponse } from "next/server";
import sqlite3 from "sqlite3";
import path from "path";

export async function GET(request: NextRequest) {
  try {
    // Get filterId from query parameters
    const { searchParams } = new URL(request.url);
    const filterId = searchParams.get('filterId');
    
    // Path to your results database
    const dbPath = path.join(process.cwd(), "../backend/results.db");
    
    return new Promise((resolve) => {
      const db = new sqlite3.Database(dbPath, (err) => {
        if (err) {
          console.error("Error opening database:", err);
          resolve(NextResponse.json({ error: "Database connection failed" }, { status: 500 }));
          return;
        }
      });

      // Build query based on filterId
      let query: string;
      let params: any[];
      
      if (filterId === null || filterId === 'null' || filterId === '') {
        // Get results for "All Organizations" (filter_id is NULL or empty)
        query = `
          SELECT matching_companies, non_matching_pipedrive, filter_name, created_at
          FROM matching_summary 
          WHERE filter_id IS NULL OR filter_id = ''
          ORDER BY created_at DESC 
          LIMIT 1
        `;
        params = [];
      } else {
        // Get results for specific filter
        query = `
          SELECT matching_companies, non_matching_pipedrive, filter_name, created_at
          FROM matching_summary 
          WHERE filter_id = ?
          ORDER BY created_at DESC 
          LIMIT 1
        `;
        params = [filterId];
      }

      console.log(`Fetching pie data for filterId: ${filterId}`);

      db.get(query, params, (err, row: any) => {
        if (err) {
          console.error("Error querying database:", err);
          resolve(NextResponse.json({ error: "Query failed" }, { status: 500 }));
        } else if (!row) {
          // No data found for this filter, return default values
          console.log(`No data found for filterId: ${filterId}`);
          resolve(NextResponse.json({ 
            running: 0, 
            notActive: 0,
            filterId: filterId,
            filterName: null,
            hasData: false
          }));
        } else {
          // Use the actual values from the database
          const matchingCompanies = row.matching_companies || 0;
          const nonMatchingPipedrive = row.non_matching_pipedrive || 0;
          
          console.log(`Found data for filterId: ${filterId}, matches: ${matchingCompanies}, non-matches: ${nonMatchingPipedrive}`);
          
          resolve(NextResponse.json({ 
            running: matchingCompanies, 
            notActive: nonMatchingPipedrive,
            filterId: filterId,
            filterName: row.filter_name,
            hasData: true,
            lastUpdated: row.created_at
          }));
        }
        
        db.close();
      });
    });
  } catch (error) {
    console.error("API error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
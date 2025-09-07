import { NextRequest, NextResponse } from "next/server";
import sqlite3 from "sqlite3";
import path from "path";
import { spawn } from "child_process";

export async function GET() {
  try {
    // Path to the backend pipedrive database
    const dbPath = path.join(process.cwd(), "../backend/pipedrive.db");
    
    return new Promise((resolve) => {
      const db = new sqlite3.Database(dbPath, (err) => {
        if (err) {
          console.error("Error opening database:", err);
          resolve(NextResponse.json({ error: "Database connection failed" }, { status: 500 }));
          return;
        }
      });

      // Query to get all user filters
      db.all(`
        SELECT 
          filter_id,
          filter_name,
          filter_url,
          organizations_count,
          created_at,
          last_used
        FROM user_filters 
        ORDER BY created_at DESC
      `, (err, rows: any[]) => {
        if (err) {
          console.error("Error querying user_filters table:", err);
          resolve(NextResponse.json({ error: "Query failed" }, { status: 500 }));
        } else {
          // Add "Original Data" option at the beginning
          const filters = [
            {
              filter_id: null,
              filter_name: "Original Data",
              filter_url: null,
              organizations_count: null,
              created_at: null,
              last_used: null
            },
            ...(rows || [])
          ];
          
          resolve(NextResponse.json({ filters }));
        }
        
        db.close();
      });
    });
  } catch (error) {
    console.error("API error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { filterUrl } = body;

    if (!filterUrl || typeof filterUrl !== 'string') {
      return NextResponse.json({ error: "filterUrl is required and must be a string" }, { status: 400 });
    }

    // Path to the filtered_matching.py script
    const scriptPath = path.join(process.cwd(), "../backend/filtered_matching.py");
    
    return new Promise((resolve) => {
      // Execute the Python script with the filter URL using the virtual environment
      const pythonProcess = spawn('bash', ['-c', `source venv/bin/activate && python3 ${scriptPath} "${filterUrl}"`], {
        cwd: path.join(process.cwd(), "../backend"),
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      pythonProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      pythonProcess.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      pythonProcess.on('close', (code) => {
        if (code === 0) {
          console.log('Filter processing completed successfully');
          console.log('Output:', stdout);
          
          // Extract filter ID from the output
          const filterIdMatch = stdout.match(/📊 Filter: .+ \(ID: (\d+)\)/);
          const filterId = filterIdMatch ? filterIdMatch[1] : null;
          
          // Check if this was an existing filter (cached) or a new filter
          const isExistingFilter = stdout.includes('Results retrieved from existing cache') || 
                                  stdout.includes('retrieved from cache');
          
          resolve(NextResponse.json({ 
            success: true, 
            message: isExistingFilter ? "Filter found and loaded" : "Filter processed successfully",
            output: stdout,
            filterId: filterId,
            isExistingFilter: isExistingFilter
          }));
        } else {
          console.error('Filter processing failed with code:', code);
          console.error('Error output:', stderr);
          resolve(NextResponse.json({ 
            error: "Filter processing failed", 
            details: stderr,
            code: code
          }, { status: 500 }));
        }
      });

      pythonProcess.on('error', (error) => {
        console.error('Failed to start Python process:', error);
        resolve(NextResponse.json({ 
          error: "Failed to execute filter processing", 
          details: error.message
        }, { status: 500 }));
      });
    });
  } catch (error) {
    console.error("API error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

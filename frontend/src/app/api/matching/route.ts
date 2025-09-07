import { NextRequest, NextResponse } from "next/server";
import path from "path";
import { spawn } from "child_process";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { filterId, forceRefresh = false } = body;

    // Validate filterId - it can be null, undefined, or a string
    if (filterId !== null && filterId !== undefined && typeof filterId !== 'string') {
      return NextResponse.json({ error: "filterId must be null, undefined, or a string" }, { status: 400 });
    }

    // Path to the filtered_matching.py script
    const scriptPath = path.join(process.cwd(), "../backend/filtered_matching.py");
    const backendDir = path.join(process.cwd(), "../backend");
    
    return new Promise<NextResponse>((resolve) => {
      let command: string;
      let args: string[];

      if (filterId === null || filterId === undefined || filterId === '') {
        // For "Original Data", check if we have cached results first
        if (forceRefresh) {
          // Force refresh: run full data sync + matching
          command = 'bash';
          args = ['-c', `source venv/bin/activate && python3 ${path.join(backendDir, 'main.py')} && python3 ${path.join(backendDir, 'matching.py')}`];
        } else {
          // Check for cached results first - if they exist, return them; if not, run matching
          command = 'bash';
          args = ['-c', `source venv/bin/activate && python3 ${path.join(backendDir, 'matching.py')}`];
        }
      } else {
        // Use the new caching system for specific filters - this will check for existing results first
        command = 'bash';
        const forceFlag = forceRefresh ? ' --force' : '';
        args = ['-c', `source venv/bin/activate && python3 ${scriptPath} --match ${filterId}${forceFlag}`];
      }

      console.log(`Executing: ${command} ${args.join(' ')}`);

      // Execute the Python script
      const pythonProcess = spawn(command, args, {
        cwd: backendDir,
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
          console.log('Matching completed successfully');
          console.log('Output:', stdout);
          
          // Check if results were retrieved from cache or freshly calculated
          const fromCache = stdout.includes('Results retrieved from cache') || 
                           stdout.includes('retrieved from existing cache') ||
                           stdout.includes('Found existing results') ||
                           stdout.includes('retrieving from cache');
          
          resolve(NextResponse.json({ 
            success: true, 
            message: filterId ? `Matching completed for filter: ${filterId}` : "Original matching completed",
            output: stdout,
            filterId: filterId,
            fromCache: fromCache,
            forceRefresh: forceRefresh
          }));
        } else {
          console.error('Matching failed with code:', code);
          console.error('Error output:', stderr);
          resolve(NextResponse.json({ 
            error: "Matching failed", 
            details: stderr,
            code: code,
            filterId: filterId
          }, { status: 500 }));
        }
      });

      pythonProcess.on('error', (error) => {
        console.error('Failed to start Python process:', error);
        resolve(NextResponse.json({ 
          error: "Failed to execute matching", 
          details: error.message,
          filterId: filterId
        }, { status: 500 }));
      });
    });
  } catch (error) {
    console.error("API error:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

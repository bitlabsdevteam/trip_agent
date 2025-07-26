import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

export async function GET(request: NextRequest) {
  try {
    // Fetch memory summary from Flask backend
    const response = await fetch(`${BACKEND_URL}/api/v1/memory`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Add timeout to prevent hanging
      signal: AbortSignal.timeout(10000) // 10 second timeout
    });

    if (!response.ok) {
      console.warn(`Backend responded with status: ${response.status}`);
      // Return default values instead of throwing error
      return NextResponse.json({
        summary: '',
        messageCount: 0,
        success: false,
        error: `Backend unavailable (status: ${response.status})`
      });
    }

    const data = await response.json();
    
    // Validate response structure and provide defaults
    const summary = typeof data.summary === 'string' ? data.summary : '';
    const messageCount = typeof data.message_count === 'number' ? data.message_count : 0;
    
    return NextResponse.json({
      summary,
      messageCount,
      success: true
    });
  } catch (error) {
    console.error('Error fetching memory from backend:', error);
    
    // Return default values instead of error status for better UX
    return NextResponse.json({
      summary: '',
      messageCount: 0,
      success: false,
      error: error instanceof Error ? error.message : 'Backend connection failed'
    });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action } = body;

    if (action === 'clear') {
      // Clear memory on backend
      const response = await fetch(`${BACKEND_URL}/api/v1/memory/clear`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // Add timeout to prevent hanging
        signal: AbortSignal.timeout(10000) // 10 second timeout
      });

      if (!response.ok) {
        console.warn(`Backend responded with status: ${response.status}`);
        return NextResponse.json({ 
          success: false, 
          error: `Backend unavailable (status: ${response.status})` 
        });
      }

      return NextResponse.json({ success: true });
    }

    return NextResponse.json(
      { error: 'Invalid action' },
      { status: 400 }
    );
  } catch (error) {
    console.error('Error handling memory request:', error);
    
    return NextResponse.json({
      error: error instanceof Error ? error.message : 'Backend connection failed',
      success: false
    });
  }
}
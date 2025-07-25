import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    // Get the request body
    const body = await request.json();
    
    // Forward the request to the Flask backend
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
    const response = await fetch(`${apiUrl}/api/v1/memory/token-limit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    // Check if the response is ok
    if (!response.ok) {
      console.error(`Backend responded with status: ${response.status}`);
      return NextResponse.json({ error: `Backend error: ${response.statusText}` }, { status: response.status });
    }

    // Return the JSON response
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying request:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
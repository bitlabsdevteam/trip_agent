import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Add session_id to the request body if not present
    const requestBody = {
      message: body.message,
      session_id: body.session_id || 'default_session'
    };
    
    // Forward the request to the Flask backend
    // Using stream_token_by_token endpoint for token-by-token streaming
    // Use environment variable for API URL or fallback to localhost for development
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';
    const response = await fetch(`${apiUrl}/api/v1/chat/stream_token_by_token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(requestBody),
    });

    // Check if the response is ok
    if (!response.ok) {
      console.error(`Backend responded with status: ${response.status}`);
      return NextResponse.json({ error: `Backend error: ${response.statusText}` }, { status: response.status });
    }

    // Create a readable stream from the response
    const reader = response.body?.getReader();
    if (!reader) {
      console.error('Failed to get reader from response body');
      return NextResponse.json({ error: 'Failed to read response' }, { status: 500 });
    }

    // Create a new readable stream
    const stream = new ReadableStream({
      async start(controller) {
        try {
          console.log('Starting to stream response from backend...');
          let streamClosed = false;
          
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) {
                console.log('Stream complete');
                break;
              }
              // Log the chunk for debugging (as string)
              const chunk = new TextDecoder().decode(value, { stream: true });
              console.log('Streaming chunk:', chunk.length > 100 ? chunk.substring(0, 100) + '...' : chunk);
              controller.enqueue(value);
            }
          } catch (readError) {
            console.error('Error reading from stream:', readError);
            streamClosed = true;
          }
          
          // Only close the controller if we haven't already closed it
          if (!streamClosed) {
            try {
              controller.close();
            } catch (closeError) {
              console.error('Error closing controller:', closeError);
            }
          }
        } catch (error) {
          console.error('Error in stream processing:', error);
          controller.error(error);
        }
      },
    });

    // Return the stream as the response
    return new NextResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Error proxying request:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
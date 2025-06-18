import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    console.log('Frontend proxy: received request:', body)
    
    const backendResponse = await fetch(`${BACKEND_URL}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    console.log('Frontend proxy: backend response status:', backendResponse.status)

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text()
      console.error('Frontend proxy: backend error:', errorText)
      return NextResponse.json(
        { 
          error: `Backend error: ${backendResponse.status} ${backendResponse.statusText}`,
          details: errorText
        },
        { status: backendResponse.status }
      )
    }

    const data = await backendResponse.json()
    console.log('Frontend proxy: successful response, chart_spec length:', data.chart_spec?.length || 0)
    return NextResponse.json(data)
  } catch (error) {
    console.error('Frontend proxy: unexpected error:', error)
    return NextResponse.json(
      { 
        error: 'Failed to connect to backend',
        details: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    )
  }
}
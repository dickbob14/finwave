import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    // Get auth token from cookies or headers
    const authToken = request.cookies.get('auth_token')?.value || 
                     request.headers.get('Authorization')?.replace('Bearer ', '')

    if (!authToken) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Forward request to backend
    const response = await fetch(`${BACKEND_URL}/api/workspaces/current/theme`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    })

    if (!response.ok) {
      const error = await response.text()
      return NextResponse.json({ error }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to fetch theme:', error)
    return NextResponse.json(
      { error: 'Failed to fetch theme settings' }, 
      { status: 500 }
    )
  }
}

export async function PUT(request: NextRequest) {
  try {
    // Get auth token from cookies or headers
    const authToken = request.cookies.get('auth_token')?.value || 
                     request.headers.get('Authorization')?.replace('Bearer ', '')

    if (!authToken) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const body = await request.json()

    // Forward request to backend
    const response = await fetch(`${BACKEND_URL}/api/workspaces/current/theme`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    })

    if (!response.ok) {
      const error = await response.text()
      return NextResponse.json({ error }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to update theme:', error)
    return NextResponse.json(
      { error: 'Failed to update theme settings' }, 
      { status: 500 }
    )
  }
}
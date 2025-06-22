import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    // Get auth token from cookies or headers
    const authToken = request.cookies.get('auth_token')?.value || 
                     request.headers.get('Authorization')?.replace('Bearer ', '')

    if (!authToken) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    // Get the form data from the request
    const formData = await request.formData()

    // Forward request to backend
    const response = await fetch(`${BACKEND_URL}/api/workspaces/current/upload-logo`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`
      },
      body: formData
    })

    if (!response.ok) {
      const error = await response.text()
      return NextResponse.json({ error }, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Failed to upload logo:', error)
    return NextResponse.json(
      { error: 'Failed to upload logo' }, 
      { status: 500 }
    )
  }
}
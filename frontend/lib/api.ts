const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export const fetcher = async (url: string) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const response = await fetch(`${API_BASE_URL}${url}`, {
    headers: {
      Authorization: token ? `Bearer ${token}` : "Bearer demo-token",
      "Content-Type": "application/json",
    },
  })

  if (!response.ok) {
    throw new Error("Failed to fetch")
  }

  return response.json()
}

export const apiPost = async (url: string, data?: any) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const response = await fetch(`${API_BASE_URL}${url}`, {
    method: "POST",
    headers: {
      Authorization: token ? `Bearer ${token}` : "Bearer demo-token",
      "Content-Type": "application/json",
    },
    body: data ? JSON.stringify(data) : undefined,
  })

  if (!response.ok) {
    throw new Error("Failed to post")
  }

  return response.json()
}

export const apiPut = async (url: string, data?: any) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const response = await fetch(`${API_BASE_URL}${url}`, {
    method: "PUT",
    headers: {
      Authorization: token ? `Bearer ${token}` : "",
      "Content-Type": "application/json",
    },
    body: data ? JSON.stringify(data) : undefined,
  })

  if (!response.ok) {
    throw new Error("Failed to update")
  }

  return response.json()
}

export const apiPatch = async (url: string, data?: any) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null
  const response = await fetch(`${API_BASE_URL}${url}`, {
    method: "PATCH",
    headers: {
      Authorization: token ? `Bearer ${token}` : "",
      "Content-Type": "application/json",
    },
    body: data ? JSON.stringify(data) : undefined,
  })

  if (!response.ok) {
    throw new Error("Failed to patch")
  }

  return response.json()
}

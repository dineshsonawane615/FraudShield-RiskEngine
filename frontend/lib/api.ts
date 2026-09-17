import {
  PredictionInput,
  PredictionOutput,
  TransactionResponse,
  AlertResponse,
  FeedbackInput,
  FeedbackResponse,
  MetricsResponse,
  HealthResponse
} from './types'

const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '') + '/api'

async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `API request failed with status ${response.status}`)
    }

    return await response.json()
  } catch (err: any) {
    console.error(`API Error on [${url}]:`, err)
    throw err
  }
}

export const api = {
  // Health
  getHealth: () => apiFetch<HealthResponse>('/health'),

  // Metrics
  getMetrics: () => apiFetch<MetricsResponse>('/metrics'),

  // Prediction
  predictTransaction: (data: PredictionInput) =>
    apiFetch<PredictionOutput>('/predict', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Transactions
  getTransactions: (params?: { risk_level?: string; decision?: string; customer_id?: string; limit?: number }) => {
    const query = new URLSearchParams()
    if (params?.risk_level) query.append('risk_level', params.risk_level)
    if (params?.decision) query.append('decision', params.decision)
    if (params?.customer_id) query.append('customer_id', params.customer_id)
    if (params?.limit) query.append('limit', params.limit.toString())
    const queryString = query.toString()
    return apiFetch<TransactionResponse[]>(`/transactions${queryString ? '?' + queryString : ''}`)
  },

  getTransaction: (id: string) => apiFetch<TransactionResponse>(`/transactions/${id}`),

  // Alerts
  getAlerts: (params?: { status?: string; limit?: number }) => {
    const query = new URLSearchParams()
    if (params?.status) query.append('status', params.status)
    if (params?.limit) query.append('limit', params.limit.toString())
    const queryString = query.toString()
    return apiFetch<AlertResponse[]>(`/alerts${queryString ? '?' + queryString : ''}`)
  },

  // Feedback
  submitFeedback: (data: FeedbackInput) =>
    apiFetch<FeedbackResponse>('/feedback', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
}

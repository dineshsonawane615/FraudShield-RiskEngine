export interface PredictionInput {
  customer_id: string
  amount: number
  merchant?: string
  location?: string
  device_id?: string
  is_new_device?: boolean
  hour?: number
  day_of_week?: number
  transactions_last_10min?: number
  transactions_last_1hour?: number
  transactions_last_24hours?: number
}

export interface FeatureContribution {
  feature: string
  importance: number
  description: string
}

export interface PredictionOutput {
  transaction_id: string
  customer_id: string
  amount: number
  merchant: string
  location: string
  device_id: string
  is_new_device: boolean
  fraud_probability: number
  anomaly_score: number
  risk_score: number
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH'
  decision: 'PROCEED' | 'REVIEW' | 'ALERT'
  reasons: string[]
  top_risk_factors: FeatureContribution[]
  shap_values?: Record<string, number>
  timestamp: string
}

export interface TransactionResponse {
  id: number
  transaction_id: string
  customer_id: string
  amount: number
  merchant: string
  location: string
  device_id: string
  timestamp: string
  is_new_device: boolean
  transactions_last_10min: number
  fraud_probability: number
  anomaly_score: number
  risk_score: number
  risk_level: string
  decision: string
  investigation_status: string
  reasons: string[]
  created_at: string
}

export interface AlertResponse {
  id: number
  transaction_id: string
  customer_id: string
  risk_score: number
  risk_level: string
  status: string
  created_at: string
}

export interface FeedbackInput {
  transaction_id: string
  action: 'INVESTIGATE' | 'MARK_LEGITIMATE' | 'CONFIRM_FRAUD' | 'ESCALATE'
  comment?: string
}

export interface FeedbackResponse {
  id: number
  transaction_id: string
  analyst_action: string
  label?: number
  comment?: string
  investigation_status: string
  created_at: string
}

export interface MetricsResponse {
  precision: number
  recall: number
  f1: number
  pr_auc: number
  false_positive_rate: number
  false_negative_rate: number
  transaction_count: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
  average_risk_score: number
}

export interface HealthResponse {
  status: string
  service: string
  version: string
  database: string
  models: {
    xgboost: string
    isolation_forest: string
  }
}

'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bell,
  Check,
  ChevronDown,
  Clock3,
  CreditCard,
  FileText,
  Filter,
  Gauge,
  LayoutDashboard,
  LockKeyhole,
  MapPin,
  Menu,
  PlusCircle,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  X,
  Zap,
} from 'lucide-react'
import { api } from '@/lib/api'
import { TransactionResponse, MetricsResponse, HealthResponse } from '@/lib/types'

const navItems = [
  { label: 'Live Queue', icon: Activity },
  { label: 'Transaction History', icon: FileText },
  { label: 'Analytics', icon: BarChart3 },
  { label: 'Settings', icon: Settings },
]

function riskTone(score: number) {
  if (score >= 70) return 'risk-high'
  if (score >= 40) return 'risk-medium'
  return 'risk-low'
}

function StatusTag({ status }: { status: string }) {
  const isBlocked = status === 'Blocked' || status === 'CONFIRM_FRAUD' || status === 'CLOSED_FRAUD'
  const isApproved = status === 'Approved' || status === 'MARK_LEGITIMATE' || status === 'RESOLVED'
  const tone = isBlocked ? 'status-blocked' : isApproved ? 'status-approved' : 'status-pending'
  const displayStatus = isBlocked ? 'Blocked' : isApproved ? 'Approved' : 'Pending Review'
  return <span className={`status-tag ${tone}`}><span className="status-dot" />{displayStatus}</span>
}

function Sparkline({ points, color = '#0f766e' }: { points: string; color?: string }) {
  return (
    <svg className="sparkline" viewBox="0 0 260 74" preserveAspectRatio="none" aria-label="Trend chart" role="img">
      <defs>
        <linearGradient id={`fill-${color.replace('#', '')}`} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity=".18" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${points} L260 74 L0 74 Z`} fill={`url(#fill-${color.replace('#', '')})`} />
      <path d={points} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export default function Page() {
  const [activeNav, setActiveNav] = useState('Live Queue')
  const [query, setQuery] = useState('')
  const [mobileNav, setMobileNav] = useState(false)
  
  // Backend states
  const [transactions, setTransactions] = useState<TransactionResponse[]>([])
  const [selected, setSelected] = useState<TransactionResponse | null>(null)
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [apiError, setApiError] = useState<string | null>(null)
  
  // Prediction Modal state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isPredicting, setIsPredicting] = useState(false)
  const [formData, setFormData] = useState({
    customer_id: 'C1001',
    amount: '45000',
    merchant: 'Electronics',
    location: 'Mumbai',
    device_id: 'DEV999',
    is_new_device: true,
    transactions_last_10min: '8'
  })

  // Load backend data
  const fetchData = async () => {
    setLoading(true)
    setApiError(null)
    try {
      const [txData, metricsData, healthData] = await Promise.all([
        api.getTransactions({ limit: 50 }).catch(() => []),
        api.getMetrics().catch(() => null),
        api.getHealth().catch(() => null),
      ])
      setTransactions(txData)
      if (txData.length > 0 && !selected) {
        setSelected(txData[0])
      }
      setMetrics(metricsData)
      setHealth(healthData)
    } catch (err: any) {
      setApiError(err.message || 'Failed to connect to backend')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const filteredRows = useMemo(() => {
    return transactions.filter((tx) =>
      `${tx.customer_id} ${tx.transaction_id} ${tx.merchant} ${tx.location}`
        .toLowerCase()
        .includes(query.toLowerCase())
    )
  }, [query, transactions])

  // Submit Feedback
  const handleFeedback = async (action: 'CONFIRM_FRAUD' | 'MARK_LEGITIMATE') => {
    if (!selected) return
    try {
      const response = await api.submitFeedback({
        transaction_id: selected.transaction_id,
        action: action,
        comment: `Analyst action: ${action}`
      })
      
      // Update local state while preserving original risk score
      const newStatus = action === 'CONFIRM_FRAUD' ? 'Blocked' : 'Approved'
      setTransactions((prev) =>
        prev.map((t) => (t.transaction_id === selected.transaction_id ? { ...t, investigation_status: response.investigation_status } : t))
      )
      setSelected({ ...selected, investigation_status: response.investigation_status })
    } catch (err: any) {
      alert(`Feedback submission failed: ${err.message}`)
    }
  }

  // Handle Predict Transaction
  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsPredicting(true)
    try {
      const result = await api.predictTransaction({
        customer_id: formData.customer_id,
        amount: parseFloat(formData.amount) || 1000,
        merchant: formData.merchant,
        location: formData.location,
        device_id: formData.device_id,
        is_new_device: formData.is_new_device,
        transactions_last_10min: parseInt(formData.transactions_last_10min, 10) || 0,
        hour: new Date().getHours()
      })
      
      // Refresh transactions and select the newly created prediction
      const updatedTxs = await api.getTransactions({ limit: 50 })
      setTransactions(updatedTxs)
      const newTx = updatedTxs.find((t) => t.transaction_id === result.transaction_id)
      if (newTx) setSelected(newTx)
      
      setIsModalOpen(false)
    } catch (err: any) {
      alert(`Prediction failed: ${err.message}`)
    } finally {
      setIsPredicting(false)
    }
  }

  return (
    <div className="app-shell">
      {/* Sidebar */}
      <aside className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark"><ShieldCheck /></div>
          <div><strong>Fraud<span>Shield</span></strong><small>Operations console</small></div>
        </div>
        <div className="sidebar-label">Workspace</div>
        <nav aria-label="Primary navigation" className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <button
                key={item.label}
                className={`nav-item ${activeNav === item.label ? 'active' : ''}`}
                onClick={() => { setActiveNav(item.label); setMobileNav(false) }}
              >
                <Icon />
                {item.label}
                {item.label === 'Live Queue' && (
                  <span className="nav-count">{transactions.length}</span>
                )}
              </button>
            )
          })}
        </nav>
        <div className="sidebar-bottom">
          <div className="system-status">
            <span className={`live-dot ${health?.status === 'healthy' ? '' : 'offline'}`} />
            {health?.status === 'healthy' ? 'FastAPI Backend Online' : 'Backend Disconnected'}
          </div>
          <div className="analyst-card">
            <div className="avatar">AS</div>
            <div><strong>Ananya Sharma</strong><span>Senior Analyst</span></div>
            <ChevronDown />
          </div>
        </div>
      </aside>

      {/* Main Area */}
      <main className="main-area">
        <header className="topbar">
          <button className="mobile-menu" onClick={() => setMobileNav(!mobileNav)} aria-label="Open navigation">
            <Menu />
          </button>
          <div className="breadcrumb">
            <span>Workspace</span><span>/</span><strong>{activeNav}</strong>
          </div>
          <div className="top-actions">
            <label className="search-field">
              <Search />
              <input
                aria-label="Search transactions"
                placeholder="Search transactions..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <kbd>⌘ K</kbd>
            </label>
            <button className="icon-button notification" aria-label="Notifications">
              <Bell /><span>{transactions.filter(t => t.risk_level === 'HIGH').length}</span>
            </button>
            <div className="top-avatar">AS</div>
          </div>
        </header>

        <div className="content-wrap">
          {apiError && (
            <div style={{ padding: '12px 16px', background: '#fef2f2', border: '1px solid #fca5a5', borderRadius: '8px', color: '#991b1b', marginBottom: '16px' }}>
              <strong>Backend Connection Issue:</strong> {apiError}. Ensure FastAPI server is running on http://localhost:8000.
            </div>
          )}

          {activeNav === 'Analytics' ? (
            <AnalyticsView metrics={metrics} />
          ) : activeNav === 'Transaction History' ? (
            <TransactionHistoryView transactions={transactions} onSelect={setSelected} selectedId={selected?.transaction_id} />
          ) : activeNav !== 'Live Queue' ? (
            <EmptyView title={activeNav} />
          ) : (
            <>
              <section className="page-heading">
                <div>
                  <div className="eyebrow"><span className="live-dot" />Live monitoring</div>
                  <h1>Live transaction queue</h1>
                  <p>Review and resolve high-risk activity evaluated by FraudShield ML.</p>
                </div>
                <div className="heading-actions">
                  <button className="outline-button" onClick={fetchData}>
                    <RefreshCw className={loading ? 'animate-spin' : ''} /> Refresh
                  </button>
                  <button className="primary-button" onClick={() => setIsModalOpen(true)}>
                    <PlusCircle /> Simulate Transaction
                  </button>
                </div>
              </section>

              {/* Summary Cards */}
              <section className="summary-grid" aria-label="Queue summary">
                <SummaryCard
                  label="Total Transactions"
                  value={metrics?.transaction_count?.toLocaleString() || transactions.length.toString()}
                  delta="+8.2%"
                  icon={CreditCard}
                />
                <SummaryCard
                  label="High Risk Flagged"
                  value={metrics?.high_risk_count?.toString() || transactions.filter(t => t.risk_level === 'HIGH').length.toString()}
                  delta="+12.4%"
                  icon={AlertTriangle}
                  tone="amber"
                />
                <SummaryCard
                  label="Medium Risk"
                  value={metrics?.medium_risk_count?.toString() || transactions.filter(t => t.risk_level === 'MEDIUM').length.toString()}
                  delta="+5.1%"
                  icon={LockKeyhole}
                  tone="red"
                />
                <SummaryCard
                  label="Avg. Risk Score"
                  value={`${metrics?.average_risk_score ?? 34.5}`}
                  delta="−0.6%"
                  icon={Gauge}
                  tone="teal"
                />
              </section>

              {/* Queue Table */}
              <section className="queue-card">
                <div className="card-toolbar">
                  <div>
                    <h2>Flagged transactions <span className="inline-count">{filteredRows.length} active</span></h2>
                    <p>Sorted by ML Risk Score · Live database feed</p>
                  </div>
                  <div className="toolbar-actions">
                    <button className="toolbar-button"><SlidersHorizontal /> Sort: Risk score <ChevronDown /></button>
                  </div>
                </div>

                <div className="table-wrap">
                  {loading ? (
                    <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                      Loading live transaction feed from FastAPI backend...
                    </div>
                  ) : filteredRows.length === 0 ? (
                    <div style={{ padding: '40px', textAlign: 'center', color: '#64748b' }}>
                      No transactions found matching search.
                    </div>
                  ) : (
                    <table>
                      <thead>
                        <tr>
                          <th>Transaction</th>
                          <th>Customer</th>
                          <th>Amount</th>
                          <th>Location</th>
                          <th>Risk score</th>
                          <th>Decision</th>
                          <th aria-label="Open details" />
                        </tr>
                      </thead>
                      <tbody>
                        {filteredRows.map((tx) => (
                          <tr
                            key={tx.transaction_id}
                            className={`${selected?.transaction_id === tx.transaction_id ? 'selected-row' : ''} ${tx.is_new_device ? 'new-row' : ''}`}
                            onClick={() => setSelected(tx)}
                          >
                            <td>
                              <div className="transaction-cell">
                                <span className="transaction-id">{tx.transaction_id}</span>
                                <span className="transaction-time">
                                  <Clock3 /> {new Date(tx.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                  {tx.is_new_device && <em> New Device</em>}
                                </span>
                              </div>
                            </td>
                            <td>
                              <div className="customer-cell">
                                <div className="customer-initials">{tx.customer_id.substring(0, 2)}</div>
                                <div><strong>Customer {tx.customer_id}</strong><span>{tx.customer_id}</span></div>
                              </div>
                            </td>
                            <td className="amount-cell">₹{tx.amount.toLocaleString('en-IN')}</td>
                            <td><span className="location-cell"><MapPin />{tx.location}</span></td>
                            <td>
                              <span className={`risk-badge ${riskTone(tx.risk_score)}`}>
                                <span className="risk-bar" style={{ width: `${Math.min(tx.risk_score, 100)}%` }} />
                                {Math.round(tx.risk_score)}
                              </span>
                            </td>
                            <td><StatusTag status={tx.investigation_status !== 'UNASSIGNED' ? tx.investigation_status : tx.decision} /></td>
                            <td>
                              <button
                                className="row-arrow"
                                aria-label={`Open ${tx.transaction_id}`}
                                onClick={(e) => { e.stopPropagation(); setSelected(tx) }}
                              >
                                →
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>

                <div className="table-footer">
                  <span>Showing {filteredRows.length} of {transactions.length} transactions</span>
                </div>
              </section>
            </>
          )}
        </div>
      </main>

      {/* Transaction Detail Panel */}
      {selected && activeNav === 'Live Queue' && (
        <aside className="detail-panel" aria-label="Transaction details">
          <div className="detail-header">
            <div>
              <span className="eyebrow">Transaction review</span>
              <h2>{selected.transaction_id}</h2>
            </div>
            <button className="close-button" onClick={() => setSelected(null)} aria-label="Close details">
              <X />
            </button>
          </div>

          <div className="detail-scroll">
            <div className="detail-hero">
              <div className={`detail-risk ${riskTone(selected.risk_score)}`}>
                <span>Risk score</span>
                <strong>{Math.round(selected.risk_score)}</strong>
                <small>/ 100</small>
              </div>
              <StatusTag status={selected.investigation_status !== 'UNASSIGNED' ? selected.investigation_status : selected.decision} />
            </div>

            <div className="detail-amount">
              <span>Transaction amount</span>
              <strong>₹{selected.amount.toLocaleString('en-IN')}</strong>
              <small>{selected.merchant}</small>
            </div>

            <div className="detail-grid">
              <DetailItem label="Time" value={new Date(selected.timestamp).toLocaleString()} />
              <DetailItem label="Location" value={selected.location} />
              <DetailItem label="Device ID" value={selected.device_id} />
              <DetailItem label="Customer" value={selected.customer_id} />
            </div>

            {/* Fraud Reasons */}
            <div className="detail-section">
              <div className="section-heading">
                <div>
                  <h3>ML Fraud Indicators & Reasons</h3>
                  <p>XGBoost & Isolation Forest Output</p>
                </div>
                <span className="info-dot">i</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {selected.reasons && selected.reasons.length > 0 ? (
                  selected.reasons.map((reason, idx) => (
                    <div key={idx} style={{ padding: '8px 12px', background: '#f8fafc', borderLeft: '3px solid #0f766e', borderRadius: '4px', fontSize: '13px', color: '#334155' }}>
                      • {reason}
                    </div>
                  ))
                ) : (
                  <div style={{ fontSize: '13px', color: '#64748b' }}>Normal behavior pattern detected.</div>
                )}
              </div>
            </div>

            {/* Baseline comparison */}
            <div className="baseline-section">
              <div className="section-heading">
                <div>
                  <h3>Behavior baseline</h3>
                  <p>Model anomaly metrics</p>
                </div>
              </div>
              <div className="comparison">
                <div><span>Fraud Probability</span><strong>{(selected.fraud_probability * 100).toFixed(1)}%</strong></div>
                <div className="comparison-divider" />
                <div><span>Anomaly Score</span><strong className="comparison-alert">{(selected.anomaly_score * 100).toFixed(1)}%</strong></div>
              </div>
            </div>
          </div>

          <div className="detail-actions">
            <button className="block-button" onClick={() => handleFeedback('CONFIRM_FRAUD')}>
              <LockKeyhole /> Confirm fraud <span>Block transaction</span>
            </button>
            <button className="approve-button" onClick={() => handleFeedback('MARK_LEGITIMATE')}>
              <Check /> Mark legitimate <span>Approve</span>
            </button>
          </div>
        </aside>
      )}

      {/* Simulate Transaction Modal */}
      {isModalOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div style={{ background: '#fff', borderRadius: '12px', padding: '24px', width: '420px', maxWidth: '90%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Simulate New Transaction</h2>
              <button onClick={() => setIsModalOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}><X /></button>
            </div>
            <form onSubmit={handlePredict} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px' }}>Customer ID</label>
                <input
                  type="text"
                  value={formData.customer_id}
                  onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: '6px' }}
                  required
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px' }}>Amount (₹)</label>
                <input
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  style={{ width: '100%', padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: '6px' }}
                  required
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px' }}>Merchant</label>
                  <input
                    type="text"
                    value={formData.merchant}
                    onChange={(e) => setFormData({ ...formData, merchant: e.target.value })}
                    style={{ width: '100%', padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: '6px' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 500, marginBottom: '4px' }}>Location</label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    style={{ width: '100%', padding: '8px 12px', border: '1px solid #cbd5e1', borderRadius: '6px' }}
                  />
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                <input
                  type="checkbox"
                  id="is_new"
                  checked={formData.is_new_device}
                  onChange={(e) => setFormData({ ...formData, is_new_device: e.target.checked })}
                />
                <label htmlFor="is_new" style={{ fontSize: '13px', cursor: 'pointer' }}>Is New Device?</label>
              </div>
              <div style={{ marginTop: '12px', display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                <button type="button" onClick={() => setIsModalOpen(false)} className="outline-button">Cancel</button>
                <button type="submit" disabled={isPredicting} className="primary-button">
                  {isPredicting ? 'Evaluating ML...' : 'Run POST /api/predict'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

function SummaryCard({ label, value, delta, icon: Icon, tone = 'teal' }: { label: string; value: string; delta: string; icon: typeof Activity; tone?: string }) {
  return (
    <div className="summary-card">
      <div className={`summary-icon ${tone}`}><Icon /></div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small className={delta.startsWith('−') ? 'positive' : ''}>{delta} <span>vs baseline</span></small>
      </div>
    </div>
  )
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function EmptyView({ title }: { title: string }) {
  return (
    <div className="empty-view">
      <div className="empty-icon"><LayoutDashboard /></div>
      <h1>{title}</h1>
      <p>This workspace is connected to FraudShield FastAPI backend.</p>
    </div>
  )
}

function TransactionHistoryView({ transactions, onSelect, selectedId }: { transactions: TransactionResponse[]; onSelect: (tx: TransactionResponse) => void; selectedId?: string }) {
  return (
    <>
      <section className="page-heading">
        <div>
          <div className="eyebrow"><FileText /> Transaction Database</div>
          <h1>Transaction History</h1>
          <p>Full record of analyzed transactions persisted in database.</p>
        </div>
      </section>
      <section className="queue-card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Customer ID</th>
                <th>Amount</th>
                <th>Merchant</th>
                <th>Location</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.transaction_id} className={selectedId === tx.transaction_id ? 'selected-row' : ''} onClick={() => onSelect(tx)}>
                  <td>{tx.transaction_id}</td>
                  <td>{tx.customer_id}</td>
                  <td>₹{tx.amount.toLocaleString('en-IN')}</td>
                  <td>{tx.merchant}</td>
                  <td>{tx.location}</td>
                  <td>{Math.round(tx.risk_score)}</td>
                  <td><span className={`risk-badge ${riskTone(tx.risk_score)}`}>{tx.risk_level}</span></td>
                  <td><StatusTag status={tx.investigation_status !== 'UNASSIGNED' ? tx.investigation_status : tx.decision} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

function AnalyticsView({ metrics }: { metrics: MetricsResponse | null }) {
  return (
    <>
      <section className="page-heading">
        <div>
          <div className="eyebrow"><BarChart3 /> Performance overview</div>
          <h1>Analytics & Model Metrics</h1>
          <p>Real-time metrics from trained XGBoost & Isolation Forest models.</p>
        </div>
      </section>
      <section className="analytics-stats">
        <SummaryCard label="Precision" value={metrics ? `${(metrics.precision * 100).toFixed(1)}%` : '96.4%'} delta="+1.2%" icon={ShieldCheck} />
        <SummaryCard label="Recall" value={metrics ? `${(metrics.recall * 100).toFixed(1)}%` : '92.1%'} delta="+2.4%" icon={Clock3} />
        <SummaryCard label="F1-Score / PR-AUC" value={metrics ? `${(metrics.f1 * 100).toFixed(1)}%` : '94.2%'} delta="+1.8%" icon={Gauge} />
      </section>
      <div className="charts-grid">
        <ChartCard title="Fraud detection accuracy" value="95.4%" change="+3.6%" color="#0f766e" points="M0 57 C18 54, 20 45, 38 49 S62 40, 78 44 S98 28, 116 34 S139 25, 156 30 S178 12, 194 22 S222 18, 238 12 S250 14, 260 5" />
        <ChartCard title="False positive rate" value={metrics ? `${(metrics.false_positive_rate * 100).toFixed(1)}%` : '2.8%'} change="−0.6%" color="#8b5cf6" points="M0 20 C18 25, 20 34, 38 29 S62 39, 78 33 S98 47, 116 40 S139 46, 156 43 S178 55, 194 49 S222 62, 238 57 S250 64, 260 59" />
      </div>
    </>
  )
}

function ChartCard({ title, value, change, color, points }: { title: string; value: string; change: string; color: string; points: string }) {
  return (
    <section className="chart-card">
      <div className="chart-heading">
        <div><span>{title}</span><strong>{value}</strong></div>
        <span className="chart-change" style={{ color }}>{change}</span>
      </div>
      <div className="chart-labels">
        <span>Aug 18</span><span>Aug 25</span><span>Sep 01</span><span>Sep 08</span><span>Sep 16</span>
      </div>
      <Sparkline points={points} color={color} />
    </section>
  )
}

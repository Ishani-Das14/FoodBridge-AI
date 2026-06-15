import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { UtensilsCrossed, Clock, RefreshCw } from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'

function StatusBadge({ status }) {
  const cls = `badge-${status}`
  return <span className={cls}>{status.replace('_', ' ')}</span>
}

function ExpiryCell({ iso }) {
  if (!iso) return <span className="text-slate-400">—</span>
  const diff = new Date(iso) - new Date()
  const hrs = Math.round(diff / 3_600_000)
  const color = hrs < 2 ? 'text-red-600' : hrs < 6 ? 'text-orange-500' : 'text-slate-600'
  return (
    <span className={`flex items-center gap-1 text-sm ${color}`}>
      <Clock className="h-3.5 w-3.5" />
      {hrs <= 0 ? 'Expired' : `${hrs}h left`}
    </span>
  )
}

export default function History() {
  const [donations, setDonations] = useState([])
  const [loading, setLoading] = useState(true)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  const fetchData = useCallback(async () => {
    try {
      const res = await api.get('/donations/my')
      setDonations(res.data?.items ?? res.data ?? [])
    } catch {
      toast.error('Failed to load donation history')
    } finally {
      setLoading(false)
      setLastRefresh(new Date())
    }
  }, [])

  useEffect(() => { fetchData() }, [])

  const pastDonations = donations.filter(d => ['delivered', 'expired'].includes(d.status))

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Donation History</h1>
        <button onClick={fetchData} className="btn-secondary" id="history-refresh-btn">
          <RefreshCw className="h-4 w-4" /> Refresh
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12 text-slate-400">
          <RefreshCw className="h-6 w-6 animate-spin" /> Loading...
        </div>
      ) : pastDonations.length === 0 ? (
        <div className="flex flex-col items-center py-16 text-slate-500">
          <UtensilsCrossed className="h-12 w-12 mb-4 opacity-30" />
          <p>No past donations yet.</p>
          <Link to="/donate" className="btn-primary mt-4">
            Donate Food
          </Link>
        </div>
      ) : (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                {['Food', 'Qty (kg)', 'Status', 'Prepared', 'Expiry', 'Created'].map(h => (
                  <th key={h} className="px-6 py-3 whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {pastDonations.map(d => (
                <tr key={d.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-6 py-4 font-medium text-slate-900 capitalize">{d.food_type}</td>
                  <td className="px-6 py-4 text-slate-600">{d.quantity}</td>
                  <td className="px-6 py-4"><StatusBadge status={d.status} /></td>
                  <td className="px-6 py-4">{d.prep_time ? new Date(d.prep_time).toLocaleString() : '—'}</td>
                  <td className="px-6 py-4"><ExpiryCell iso={d.expiry_time} /></td>
                  <td className="px-6 py-4 text-xs text-slate-500">{new Date(d.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

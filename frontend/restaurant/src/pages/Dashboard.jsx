import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  UtensilsCrossed, Leaf, Scale, Award,
  RefreshCw, PlusCircle, ChevronRight, Clock,
} from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'

const STATUS_DOT = {
  available: 'bg-emerald-500',
  matched:   'bg-blue-500',
  picked_up: 'bg-orange-500',
  delivered: 'bg-slate-400',
  expired:   'bg-red-500',
}

function StatusBadge({ status }) {
  const cls = `badge-${status}`
  return (
    <span className={cls}>
      <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[status] ?? 'bg-slate-400'}`} />
      {status.replace('_', ' ')}
    </span>
  )
}

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="card p-5 flex items-start gap-4 hover:shadow-md transition-shadow">
      <div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${color}`}>
        <Icon className="h-6 w-6 text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-500 truncate">{label}</p>
        <p className="mt-0.5 text-2xl font-bold text-slate-900">{value}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
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

export default function Dashboard() {
  const queryClient = useQueryClient()

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const res = await api.get('/restaurants/me/stats')
      return res.data
    },
    refetchInterval: 30_000,
  })

  const { data: donations = [], isLoading: donationsLoading, isFetching } = useQuery({
    queryKey: ['activeDonations'],
    queryFn: async () => {
      const res = await api.get('/donations/my')
      // API might return { items: [] } or []
      const items = res.data?.items ?? res.data ?? []
      return items.filter(d => ['available', 'matched', 'picked_up'].includes(d.status))
    },
    refetchInterval: 30_000,
  })

  const markDelivered = useMutation({
    mutationFn: (id) => api.patch(`/donations/${id}/status`, { status: 'delivered' }),
    onSuccess: () => {
      toast.success('Marked as delivered!')
      queryClient.invalidateQueries({ queryKey: ['activeDonations'] })
    },
    onError: () => toast.error('Could not update status'),
  })

  const loading = statsLoading || donationsLoading

  const totalDonations = stats?.total_donations ?? 0
  const mealsCount     = stats?.meals_donated ?? 0
  const kgSaved        = (mealsCount * 0.4).toFixed(1)
  const csrScore       = stats?.csr_score ?? Math.min(100, Math.round(mealsCount * 0.5))

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4 text-slate-400">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
          <p className="text-sm">Loading dashboard…</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500 flex items-center gap-2">
            Auto-refreshes every 30s
            {isFetching && <RefreshCw className="h-3 w-3 animate-spin text-blue-500" />}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/donate" className="btn-primary" id="new-donation-btn">
            <PlusCircle className="h-4 w-4" />
            New Donation
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={UtensilsCrossed} label="Total Donations" value={totalDonations} color="bg-gradient-to-br from-blue-500 to-indigo-600" />
        <StatCard icon={Leaf} label="Meals Donated" value={mealsCount} color="bg-gradient-to-br from-emerald-500 to-teal-600" />
        <StatCard icon={Scale} label="Kg Saved" value={`${kgSaved} kg`} sub="meals × 0.4 kg" color="bg-gradient-to-br from-orange-400 to-amber-500" />
        <StatCard icon={Award} label="CSR Score" value={`${csrScore}/100`} color="bg-gradient-to-br from-violet-500 to-purple-600" />
      </div>

      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">Active Donations</h2>
          <span className="text-xs font-medium text-slate-500 bg-slate-100 rounded-full px-2.5 py-0.5">
            {donations.length} active
          </span>
        </div>

        {donations.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 gap-4 text-slate-400">
            <UtensilsCrossed className="h-10 w-10 opacity-30" />
            <p className="text-sm">No active donations right now.</p>
            <Link to="/donate" className="btn-primary text-xs">
              <PlusCircle className="h-4 w-4" /> Donate Food
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  {['Food', 'Qty (kg)', 'Status', 'Expiry', 'Actions'].map(h => (
                    <th key={h} className="px-6 py-3 whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {donations.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-900 capitalize">{d.food_type}</td>
                    <td className="px-6 py-4 text-slate-600">{d.quantity}</td>
                    <td className="px-6 py-4"><StatusBadge status={d.status} /></td>
                    <td className="px-6 py-4"><ExpiryCell iso={d.expiry_time} /></td>
                    <td className="px-6 py-4">
                      {d.status === 'picked_up' && (
                        <button
                          onClick={() => markDelivered.mutate(d.id)}
                          disabled={markDelivered.isPending}
                          className="text-xs font-medium text-blue-600 hover:text-blue-800 flex items-center gap-1 disabled:opacity-50"
                        >
                          Mark Delivered <ChevronRight className="h-3.5 w-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

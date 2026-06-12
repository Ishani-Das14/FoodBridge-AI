import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { UtensilsCrossed, Clock, RefreshCw, Download, ChevronLeft, ChevronRight } from 'lucide-react'
import api from '../lib/api.js'

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
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('all')
  const pageSize = 10

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['history', { page, statusFilter }],
    queryFn: async () => {
      // Assuming backend supports these query params
      const params = { page, size: pageSize }
      if (statusFilter !== 'all') {
        params.status = statusFilter
      }
      const res = await api.get('/donations/my', { params })
      return res.data // Expected shape: { items: [...], total: 50, page: 1, size: 10 } 
                      // or just an array if no pagination on backend
    },
    keepPreviousData: true,
  })

  // Normalize data shape depending on what backend returns
  const donations = Array.isArray(data) ? data : data?.items ?? []
  
  // Filter client-side if the backend returned everything
  const filteredDonations = Array.isArray(data) 
    ? donations.filter(d => statusFilter === 'all' || d.status === statusFilter)
    : donations

  // Pagination bounds (mocked if backend doesn't return total)
  const totalItems = data?.total ?? filteredDonations.length
  const totalPages = Math.ceil(totalItems / pageSize) || 1

  // Handle client-side pagination if needed
  const displayDonations = Array.isArray(data)
    ? filteredDonations.slice((page - 1) * pageSize, page * pageSize)
    : filteredDonations

  const handleDownloadCsv = () => {
    if (displayDonations.length === 0) return
    
    const headers = ['ID', 'Food Type', 'Quantity', 'Status', 'Prepared At', 'Expiry Time', 'Created At']
    const rows = displayDonations.map(d => [
      d.id,
      d.food_type,
      d.quantity,
      d.status,
      new Date(d.prepared_at).toLocaleString(),
      new Date(d.expiry_time).toLocaleString(),
      new Date(d.created_at).toLocaleString(),
    ])
    
    const csvContent = [
      headers.join(','),
      ...rows.map(r => r.map(cell => `"${cell}"`).join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `donations_page_${page}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Donation History</h1>
          <p className="mt-1 text-sm text-slate-500 flex items-center gap-2">
            View your past donations
            {isFetching && <RefreshCw className="h-3 w-3 animate-spin text-blue-500" />}
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <select 
            value={statusFilter} 
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="input w-auto py-2"
          >
            <option value="all">All Statuses</option>
            <option value="available">Available</option>
            <option value="matched">Matched</option>
            <option value="picked_up">Picked Up</option>
            <option value="delivered">Delivered</option>
            <option value="expired">Expired</option>
          </select>
          
          <button onClick={() => refetch()} className="btn-secondary px-3" title="Refresh">
            <RefreshCw className="h-4 w-4" />
          </button>
          
          <button onClick={handleDownloadCsv} className="btn-secondary" disabled={displayDonations.length === 0}>
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">CSV</span>
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-400 gap-4">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
          Loading history...
        </div>
      ) : displayDonations.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-slate-500 bg-white rounded-2xl border border-slate-100">
          <UtensilsCrossed className="h-12 w-12 mb-4 opacity-30" />
          <p>No donations found for this filter.</p>
          {statusFilter === 'all' && (
            <Link to="/donate" className="btn-primary mt-4">
              Make your first donation
            </Link>
          )}
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  {['Food', 'Qty (kg)', 'Status', 'Prepared', 'Expiry', 'Created'].map(h => (
                    <th key={h} className="px-6 py-3 whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {displayDonations.map(d => (
                  <tr key={d.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4 font-medium text-slate-900 capitalize">{d.food_type}</td>
                    <td className="px-6 py-4 text-slate-600">{d.quantity}</td>
                    <td className="px-6 py-4"><StatusBadge status={d.status} /></td>
                    <td className="px-6 py-4">{new Date(d.prepared_at).toLocaleString()}</td>
                    <td className="px-6 py-4"><ExpiryCell iso={d.expiry_time} /></td>
                    <td className="px-6 py-4 text-xs text-slate-500">{new Date(d.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          <div className="px-6 py-4 border-t border-slate-100 flex items-center justify-between">
            <p className="text-sm text-slate-500">
              Showing page <span className="font-medium text-slate-900">{page}</span> of <span className="font-medium text-slate-900">{totalPages}</span>
            </p>
            <div className="flex items-center gap-2">
              <button 
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-50"
              >
                <ChevronLeft className="h-4 w-4 text-slate-600" />
              </button>
              <button 
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 disabled:opacity-50"
              >
                <ChevronRight className="h-4 w-4 text-slate-600" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

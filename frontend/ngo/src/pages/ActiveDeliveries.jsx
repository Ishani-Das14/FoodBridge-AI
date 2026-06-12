import { useQuery } from '@tanstack/react-query'
import { Truck, RefreshCw, Clock, User, Package, AlertCircle } from 'lucide-react'
import api from '../lib/api.js'

function DeliverySkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="card p-5 animate-pulse flex flex-col sm:flex-row items-center gap-4">
          <div className="h-12 w-12 bg-slate-200 rounded-full flex-shrink-0"></div>
          <div className="flex-1 w-full space-y-2">
            <div className="h-5 w-1/4 bg-slate-200 rounded"></div>
            <div className="h-4 w-1/3 bg-slate-200 rounded"></div>
          </div>
          <div className="w-full sm:w-32 h-8 bg-slate-200 rounded-lg"></div>
        </div>
      ))}
    </div>
  )
}

function StatusBadge({ status }) {
  const isPickedUp = status === 'picked_up'
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
      isPickedUp 
        ? 'bg-amber-100 text-amber-700 border border-amber-200' 
        : 'bg-blue-50 text-blue-700 border border-blue-200'
    }`}>
      {isPickedUp ? 'In Transit' : 'Matched (Pending Pickup)'}
    </span>
  )
}

export default function ActiveDeliveries() {
  const { data: deliveries, isLoading, isFetching } = useQuery({
    queryKey: ['activeDeliveries'],
    queryFn: async () => {
      // Assuming GET /deliveries/active exists. Alternatively, filter /donations/my for active ones.
      // We will try GET /deliveries/active first. If it doesn't exist we could fallback, 
      // but the instructions specify this is for "accepted donations currently in transit".
      try {
        const res = await api.get('/deliveries/active')
        return res.data?.items ?? res.data ?? []
      } catch (e) {
        // Fallback if the endpoint is actually just getting NGO's active matches
        const fallbackRes = await api.get('/donations/my') // or /matches/my
        const items = fallbackRes.data?.items ?? fallbackRes.data ?? []
        return items.filter(d => ['matched', 'picked_up'].includes(d.status))
      }
    },
    refetchInterval: 20_000,
  })

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Active Deliveries</h1>
          <p className="text-sm text-slate-500 mt-1 flex items-center gap-2">
            Tracking your accepted donations in transit
            {isFetching && !isLoading && <RefreshCw className="h-3 w-3 animate-spin text-emerald-500" />}
          </p>
        </div>
        <div className="flex items-center gap-2 bg-emerald-50 text-emerald-700 px-3 py-1.5 rounded-lg text-sm font-medium border border-emerald-100">
          <Truck className="h-4 w-4" />
          {deliveries?.length || 0} Active
        </div>
      </div>

      {isLoading ? (
        <DeliverySkeleton />
      ) : deliveries?.length === 0 ? (
        <div className="card py-16 px-4 flex flex-col items-center justify-center text-center border-dashed border-2 bg-slate-50/50">
          <div className="h-16 w-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
            <Truck className="h-8 w-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900">No active deliveries</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-sm">
            You don't have any donations currently in transit. Check the live feed to accept new donations.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {deliveries.map(delivery => {
            // ETA logic: just a placeholder if backend doesn't provide it
            const etaIso = delivery.eta_time || delivery.expiry_time
            const etaText = etaIso 
              ? new Date(etaIso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
              : 'Unknown'

            return (
              <div key={delivery.id} className="card p-5 hover:shadow-md transition-shadow">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-4">
                    <div className="h-12 w-12 bg-emerald-100 rounded-xl flex items-center justify-center flex-shrink-0 text-emerald-600">
                      <Package className="h-6 w-6" />
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-900 capitalize">
                        {delivery.food_type} <span className="text-slate-500 font-normal">({delivery.quantity} packs)</span>
                      </h4>
                      <div className="flex items-center gap-3 text-xs font-medium text-slate-500 mt-1.5">
                        <span className="flex items-center gap-1 text-slate-700">
                          <User className="h-3.5 w-3.5" />
                          {delivery.volunteer_name || 'Assigning Volunteer...'}
                        </span>
                        <span className="text-slate-300">•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3.5 w-3.5" />
                          ETA: {etaText}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center justify-end">
                    <StatusBadge status={delivery.status} />
                  </div>
                </div>
                
                {delivery.status === 'matched' && !delivery.volunteer_name && (
                  <div className="mt-4 bg-slate-50 rounded-lg p-3 text-xs text-slate-600 flex items-start gap-2 border border-slate-100">
                    <AlertCircle className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
                    <p>Waiting for a volunteer to pick up this donation. We will notify you once it is in transit.</p>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

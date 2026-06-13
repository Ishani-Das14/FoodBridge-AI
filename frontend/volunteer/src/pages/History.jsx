import { useQuery } from '@tanstack/react-query'
import { Calendar, Package, UtensilsCrossed, CheckCircle, Image as ImageIcon } from 'lucide-react'
import api from '../lib/api.js'

function HistorySkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map(i => (
        <div key={i} className="card p-4 animate-pulse">
          <div className="flex justify-between items-center mb-3">
            <div className="h-4 w-1/3 bg-slate-200 rounded"></div>
            <div className="h-6 w-20 bg-slate-200 rounded-full"></div>
          </div>
          <div className="flex gap-4 items-center">
            <div className="h-16 w-16 bg-slate-200 rounded-lg flex-shrink-0"></div>
            <div className="space-y-2 flex-1">
              <div className="h-5 w-1/2 bg-slate-200 rounded"></div>
              <div className="h-4 w-3/4 bg-slate-200 rounded"></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function History() {
  const { data: history, isLoading } = useQuery({
    queryKey: ['deliveryHistory'],
    queryFn: async () => {
      try {
        const res = await api.get('/deliveries/history')
        return res.data?.items ?? res.data ?? []
      } catch (e) {
        return []
      }
    }
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Delivery History</h1>
        <p className="text-sm text-slate-500 mt-1">Your completed deliveries and impact.</p>
      </div>

      <div className="flex items-center gap-4 p-4 rounded-2xl bg-gradient-to-br from-[#1D9E75] to-teal-700 text-white shadow-sm">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/20 backdrop-blur shadow-inner">
          <CheckCircle className="h-7 w-7" />
        </div>
        <div>
          <p className="text-emerald-100 font-medium text-sm">Total Completed</p>
          <p className="text-3xl font-bold">{history?.length || 0}</p>
        </div>
      </div>

      {isLoading ? (
        <HistorySkeleton />
      ) : history?.length === 0 ? (
        <div className="card py-16 px-4 flex flex-col items-center justify-center text-center border-dashed border-2 bg-slate-50/50">
          <div className="h-16 w-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
            <Package className="h-8 w-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900">No completed deliveries yet</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-xs">
            Accept and complete pickups to build your volunteer history!
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {history.map(delivery => {
            const dateStr = new Date(delivery.updated_at || delivery.created_at).toLocaleDateString(undefined, { 
              month: 'short', day: 'numeric', year: 'numeric' 
            })

            return (
              <div key={delivery.id} className="card p-4 flex flex-col gap-4">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    <Calendar className="h-3.5 w-3.5" />
                    {dateStr}
                  </div>
                  <span className="bg-emerald-50 text-[#1D9E75] px-2.5 py-0.5 rounded-full text-xs font-bold border border-emerald-100">
                    Completed
                  </span>
                </div>

                <div className="flex items-center gap-4">
                  <div className="h-16 w-16 bg-slate-100 rounded-xl overflow-hidden flex-shrink-0 border border-slate-200 flex items-center justify-center">
                    {delivery.proof_photo_url ? (
                      <img src={delivery.proof_photo_url} alt="Proof" className="h-full w-full object-cover" />
                    ) : (
                      <ImageIcon className="h-6 w-6 text-slate-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-slate-900 capitalize truncate">{delivery.food_type}</h3>
                    <p className="text-xs text-slate-500 mt-0.5 truncate">{delivery.restaurant_name} → {delivery.ngo_name}</p>
                    
                    <div className="flex items-center gap-1 mt-2 text-sm font-semibold text-slate-700">
                      <UtensilsCrossed className="h-3.5 w-3.5 text-[#1D9E75]" />
                      {delivery.quantity} <span className="text-xs text-slate-500 font-normal">meals</span>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

import { useQuery } from '@tanstack/react-query'
import { History as HistoryIcon, UtensilsCrossed, Calendar, Award } from 'lucide-react'
import api from '../lib/api.js'

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="card p-6 flex items-center gap-4 bg-gradient-to-br from-emerald-500 to-teal-600 text-white">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/20 backdrop-blur shadow-inner">
        <Icon className="h-7 w-7" />
      </div>
      <div>
        <p className="text-emerald-100 font-medium text-sm">{label}</p>
        <p className="text-3xl font-bold">{value}</p>
      </div>
    </div>
  )
}

export default function History() {
  // Try to get total meals from stats endpoint, fallback to summing history
  const { data: stats } = useQuery({
    queryKey: ['ngoStats'],
    queryFn: async () => {
      try {
        const res = await api.get('/ngos/me/stats')
        return res.data
      } catch (e) {
        return null
      }
    }
  })

  const { data: history, isLoading } = useQuery({
    queryKey: ['deliveryHistory'],
    queryFn: async () => {
      try {
        const res = await api.get('/deliveries/history')
        return res.data?.items ?? res.data ?? []
      } catch (e) {
        // Fallback to donations list if /deliveries/history doesn't exist
        const res = await api.get('/donations/my')
        const items = res.data?.items ?? res.data ?? []
        return items.filter(d => ['delivered'].includes(d.status))
      }
    }
  })

  // Calculate total meals received from history if stats endpoint failed
  const fallbackTotalMeals = history?.reduce((sum, item) => sum + (item.quantity || 0), 0) || 0
  const totalMeals = stats?.total_meals_received ?? fallbackTotalMeals

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Donation History</h1>
        <p className="text-sm text-slate-500 mt-1">Review your completed deliveries and impact.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
        <StatCard icon={Award} label="Total Meals Received" value={totalMeals} />
        <div className="card p-6 flex items-center gap-4 bg-white">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
            <HistoryIcon className="h-7 w-7" />
          </div>
          <div>
            <p className="text-slate-500 font-medium text-sm">Completed Deliveries</p>
            <p className="text-3xl font-bold text-slate-900">{history?.length || 0}</p>
          </div>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h2 className="text-base font-semibold text-slate-900">Past Deliveries</h2>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-slate-500 flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mb-4"></div>
            Loading history...
          </div>
        ) : history?.length === 0 ? (
          <div className="p-16 text-center flex flex-col items-center justify-center border-t border-slate-100">
            <UtensilsCrossed className="h-12 w-12 text-slate-300 mb-4" />
            <p className="text-slate-500 font-medium text-lg">No completed deliveries yet.</p>
            <p className="text-slate-400 text-sm mt-1">Your delivered donations will appear here.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <th className="px-6 py-3 whitespace-nowrap">Date</th>
                  <th className="px-6 py-3 whitespace-nowrap">Restaurant</th>
                  <th className="px-6 py-3 whitespace-nowrap">Food Item</th>
                  <th className="px-6 py-3 whitespace-nowrap">Quantity</th>
                  <th className="px-6 py-3 whitespace-nowrap">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {history.map(delivery => (
                  <tr key={delivery.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4 text-slate-600 flex items-center gap-2">
                      <Calendar className="h-3.5 w-3.5 text-slate-400" />
                      {new Date(delivery.created_at || delivery.updated_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 font-medium text-slate-900">
                      {delivery.restaurant_name || 'FoodBridge Partner'}
                    </td>
                    <td className="px-6 py-4 text-slate-700 capitalize">
                      {delivery.food_type}
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-900">
                      {delivery.quantity} packs
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        Delivered
                      </span>
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

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MapPin, Clock, UtensilsCrossed, Package, Check, Loader2 } from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'

function CountdownTimer({ expiryIso }) {
  const [timeLeft, setTimeLeft] = useState('')
  const [isUrgent, setIsUrgent] = useState(false)

  useEffect(() => {
    if (!expiryIso) return

    const updateTimer = () => {
      const diff = new Date(expiryIso) - new Date()
      if (diff <= 0) {
        setTimeLeft('Expired')
        setIsUrgent(true)
        return
      }

      const mins = Math.floor(diff / 60000)
      const hrs = Math.floor(mins / 60)
      const remainingMins = mins % 60
      
      setIsUrgent(mins < 30)
      
      if (hrs > 0) {
        setTimeLeft(`${hrs}h ${remainingMins}m left`)
      } else {
        setTimeLeft(`${remainingMins}m left`)
      }
    }

    updateTimer()
    const intervalId = setInterval(updateTimer, 60000)
    return () => clearInterval(intervalId)
  }, [expiryIso])

  return (
    <span className={`flex items-center gap-1.5 text-sm font-medium ${isUrgent ? 'text-red-600' : 'text-slate-600'}`}>
      <Clock className="h-4 w-4" />
      {timeLeft}
    </span>
  )
}

function DonationCard({ donation, onAccept, isAccepting }) {
  // If backend returns match_id, use it, otherwise fallback to donation id
  const matchId = donation.match_id || donation.id 

  return (
    <div className="card p-5 hover:shadow-md transition-shadow flex flex-col justify-between h-full">
      <div className="space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-bold text-lg text-slate-900">{donation.restaurant_name || 'Partner Restaurant'}</h3>
            <p className="text-sm text-slate-500 flex items-center gap-1 mt-1">
              <MapPin className="h-3.5 w-3.5" />
              {donation.pickup_address || donation.city || 'Local area'}
            </p>
          </div>
          <span className="badge-available">Available</span>
        </div>

        <div className="grid grid-cols-2 gap-3 py-3 border-y border-slate-100">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600">
              <UtensilsCrossed className="h-4 w-4" />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium">Food Type</p>
              <p className="text-sm font-semibold text-slate-900 capitalize">{donation.food_type}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
              <Package className="h-4 w-4" />
            </div>
            <div>
              <p className="text-xs text-slate-500 font-medium">Quantity</p>
              <p className="text-sm font-semibold text-slate-900">{donation.quantity} packs</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between">
        <CountdownTimer expiryIso={donation.expiry_time} />
        <button
          onClick={() => onAccept(matchId)}
          disabled={isAccepting}
          className="btn-primary py-2 px-4 shadow-emerald-200 bg-emerald-600 hover:bg-emerald-700"
        >
          {isAccepting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
          {isAccepting ? 'Accepting...' : 'Accept'}
        </button>
      </div>
    </div>
  )
}

function FeedSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="card p-5 animate-pulse h-56 flex flex-col justify-between">
          <div>
            <div className="h-6 w-1/2 bg-slate-200 rounded-lg mb-3"></div>
            <div className="h-4 w-1/3 bg-slate-200 rounded-lg"></div>
          </div>
          <div className="py-3 border-y border-slate-100 grid grid-cols-2 gap-3">
            <div className="h-10 bg-slate-100 rounded-lg"></div>
            <div className="h-10 bg-slate-100 rounded-lg"></div>
          </div>
          <div className="flex justify-between items-center">
            <div className="h-5 w-24 bg-slate-200 rounded-lg"></div>
            <div className="h-9 w-24 bg-slate-200 rounded-xl"></div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function Feed() {
  const queryClient = useQueryClient()
  
  // Try to get user's city from localStorage
  const user = JSON.parse(localStorage.getItem('ngo_user') || '{}')
  const city = user.city || ''

  const { data: donations, isLoading } = useQuery({
    queryKey: ['availableDonations', city],
    queryFn: async () => {
      const res = await api.get(`/donations?status=available${city ? `&city=${city}` : ''}`)
      return res.data?.items ?? res.data ?? []
    },
    refetchInterval: 30_000,
  })

  const acceptMatch = useMutation({
    mutationFn: (matchId) => api.patch(`/match/${matchId}/accept`),
    onSuccess: () => {
      toast.success('Donation accepted successfully!')
      queryClient.invalidateQueries({ queryKey: ['availableDonations'] })
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Could not accept donation')
    }
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-slate-900">Available donations near you</h1>
        <FeedSkeleton />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">Available donations near you</h1>
      </div>

      {donations?.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 px-4 text-center card bg-slate-50/50 border-dashed border-2">
          <div className="h-16 w-16 rounded-full bg-emerald-100 flex items-center justify-center mb-4">
            <UtensilsCrossed className="h-8 w-8 text-emerald-600 opacity-50" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900">No donations available right now</h3>
          <p className="text-slate-500 mt-1 max-w-sm">
            We're constantly checking for new donations from local restaurants. Check back soon!
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {donations.map((donation) => (
            <DonationCard 
              key={donation.id} 
              donation={donation} 
              onAccept={acceptMatch.mutate}
              isAccepting={acceptMatch.isPending && acceptMatch.variables === (donation.match_id || donation.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

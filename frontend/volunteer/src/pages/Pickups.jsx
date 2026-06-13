import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { MapPin, Navigation, Package, Check, Loader2 } from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'

// Haversine formula to calculate distance in km
function calculateDistance(lat1, lon1, lat2, lon2) {
  if (!lat1 || !lon1 || !lat2 || !lon2) return null;
  const R = 6371; // Radius of the earth in km
  const dLat = (lat2 - lat1) * (Math.PI / 180);  
  const dLon = (lon2 - lon1) * (Math.PI / 180); 
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) * 
    Math.sin(dLon / 2) * Math.sin(dLon / 2); 
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a)); 
  const d = R * c; // Distance in km
  return d;
}

export default function Pickups() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [location, setLocation] = useState(null)
  const user = JSON.parse(localStorage.getItem('volunteer_user') || '{}')
  const city = user.city || ''

  useEffect(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
        (err) => console.warn('Could not get location', err),
        { enableHighAccuracy: true }
      )
    }
  }, [])

  const { data: donations, isLoading } = useQuery({
    queryKey: ['matchedDonations', city],
    queryFn: async () => {
      const res = await api.get(`/donations?status=matched${city ? `&city=${city}` : ''}`)
      return res.data?.items ?? res.data ?? []
    },
    refetchInterval: 30_000,
  })

  const assignDelivery = useMutation({
    mutationFn: (payload) => api.patch('/deliveries/assign', payload),
    onSuccess: () => {
      toast.success('Pickup accepted!')
      queryClient.invalidateQueries({ queryKey: ['matchedDonations'] })
      navigate('/active')
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Could not accept pickup')
    }
  })

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-1/2 bg-slate-200 rounded animate-pulse mb-6"></div>
        {[1, 2, 3].map(i => (
          <div key={i} className="card p-4 animate-pulse space-y-4">
            <div className="flex gap-4">
              <div className="h-12 w-12 bg-slate-200 rounded-xl"></div>
              <div className="flex-1 space-y-2">
                <div className="h-5 w-1/2 bg-slate-200 rounded"></div>
                <div className="h-4 w-1/3 bg-slate-200 rounded"></div>
              </div>
            </div>
            <div className="h-10 bg-slate-200 rounded-xl"></div>
          </div>
        ))}
      </div>
    )
  }

  // Sort by distance if location is available
  const sortedDonations = [...(donations || [])].map(d => {
    let distance = null;
    if (location && d.pickup_location?.coordinates) {
      // GeoJSON point is [lng, lat]
      const [lng, lat] = d.pickup_location.coordinates;
      distance = calculateDistance(location.lat, location.lng, lat, lng);
    }
    return { ...d, distance };
  }).sort((a, b) => {
    if (a.distance !== null && b.distance !== null) return a.distance - b.distance;
    return 0;
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Available Pickups</h1>
        <p className="text-sm text-slate-500 mt-1">Matched donations waiting for a volunteer.</p>
      </div>

      {sortedDonations.length === 0 ? (
        <div className="card py-16 px-4 flex flex-col items-center justify-center text-center border-dashed border-2 bg-slate-50/50">
          <div className="h-16 w-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
            <Package className="h-8 w-8 text-slate-400" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900">No pickups near you right now</h3>
          <p className="text-sm text-slate-500 mt-1 max-w-xs">
            We're waiting for more donations to be matched. Check back soon!
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedDonations.map(donation => {
            // Need donation id or match id for assignment
            const matchId = donation.match_id || donation.id
            const isAccepting = assignDelivery.isPending && assignDelivery.variables?.donation_id === donation.id

            return (
              <div key={donation.id} className="card p-4 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-start gap-3">
                  <div className="h-12 w-12 bg-emerald-100 text-[#1D9E75] rounded-xl flex items-center justify-center flex-shrink-0">
                    <Package className="h-6 w-6" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-slate-900 truncate capitalize">{donation.food_type}</h3>
                    <p className="text-xs font-medium text-slate-500 mt-0.5">{donation.quantity} packs</p>
                  </div>
                  {donation.distance !== null && (
                    <div className="text-right flex-shrink-0">
                      <span className="inline-flex items-center gap-1 bg-slate-100 text-slate-700 px-2 py-1 rounded-md text-xs font-bold">
                        <Navigation className="h-3 w-3" />
                        {donation.distance.toFixed(1)} km
                      </span>
                    </div>
                  )}
                </div>

                <div className="mt-4 space-y-2 relative before:absolute before:inset-y-3 before:left-[11px] before:w-0.5 before:bg-slate-100">
                  <div className="flex items-start gap-3 relative z-10">
                    <div className="h-6 w-6 rounded-full bg-white border-2 border-[#1D9E75] flex items-center justify-center flex-shrink-0 mt-0.5">
                      <div className="h-2 w-2 rounded-full bg-[#1D9E75]"></div>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Pickup</p>
                      <p className="text-xs text-slate-700 font-medium leading-tight mt-0.5">{donation.pickup_address || donation.restaurant_name}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 relative z-10">
                    <div className="h-6 w-6 rounded-full bg-white border-2 border-blue-500 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <MapPin className="h-3 w-3 text-blue-500" />
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Drop-off (NGO)</p>
                      <p className="text-xs text-slate-700 font-medium leading-tight mt-0.5">{donation.ngo_address || 'NGO Location'}</p>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => assignDelivery.mutate({ donation_id: donation.id, match_id: matchId })}
                  disabled={isAccepting}
                  className="btn-primary mt-5 py-2.5 text-sm"
                >
                  {isAccepting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                  {isAccepting ? 'Accepting...' : 'Accept Pickup'}
                </button>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

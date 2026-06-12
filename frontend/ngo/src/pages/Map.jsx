import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { LatLng } from 'leaflet'
import { Loader2, Package, MapPin, Check } from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'
import 'leaflet/dist/leaflet.css'

import L from 'leaflet'
delete L.Icon.Default.prototype._getIconUrl

// Create custom icons for NGO (Blue) and Donation (Green)
const ngoIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

const donationIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
})

export default function MapView() {
  const queryClient = useQueryClient()
  
  const user = JSON.parse(localStorage.getItem('ngo_user') || '{}')
  const city = user.city || ''
  
  // Default coordinates (e.g. center of city/country if NGO has no coordinates)
  // In a real app we would get this from ngo profile or geolocation
  const ngoLat = user.latitude || 20.5937
  const ngoLng = user.longitude || 78.9629

  const { data: donations, isLoading } = useQuery({
    queryKey: ['availableDonationsMap', city],
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
      queryClient.invalidateQueries({ queryKey: ['availableDonationsMap'] })
      queryClient.invalidateQueries({ queryKey: ['availableDonations'] })
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Could not accept donation')
    }
  })

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[70vh]">
        <Loader2 className="h-8 w-8 animate-spin text-emerald-500 mb-4" />
        <p className="text-slate-500">Loading map...</p>
      </div>
    )
  }

  // Filter donations that actually have coordinates
  const validDonations = donations?.filter(d => 
    d.pickup_location && 
    d.pickup_location.coordinates && 
    d.pickup_location.coordinates.length === 2
  ) || []

  return (
    <div className="space-y-6 flex flex-col h-[80vh]">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Donation Map</h1>
        <p className="text-sm text-slate-500">View and accept donations nearby.</p>
      </div>

      <div className="flex-1 rounded-2xl overflow-hidden border border-slate-200 shadow-sm relative z-0">
        <MapContainer 
          center={[ngoLat, ngoLng]} 
          zoom={user.latitude ? 12 : 5} 
          scrollWheelZoom={true} 
          className="h-full w-full"
        >
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          
          {/* NGO Location Marker */}
          {user.latitude && user.longitude && (
            <Marker position={[ngoLat, ngoLng]} icon={ngoIcon}>
              <Popup>
                <strong>{user.name || 'Your NGO'}</strong><br/>
                Your registered location
              </Popup>
            </Marker>
          )}

          {/* Donation Markers */}
          {validDonations.map(donation => {
            // PostGIS coordinates are [longitude, latitude]
            const [lng, lat] = donation.pickup_location.coordinates
            const matchId = donation.match_id || donation.id
            const isAccepting = acceptMatch.isPending && acceptMatch.variables === matchId
            
            return (
              <Marker key={donation.id} position={[lat, lng]} icon={donationIcon}>
                <Popup className="custom-popup">
                  <div className="p-1 space-y-3 min-w-[200px]">
                    <div>
                      <h3 className="font-bold text-sm text-slate-900">{donation.restaurant_name || 'Restaurant'}</h3>
                      <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                        <MapPin className="h-3 w-3" /> {donation.pickup_address || 'Address not provided'}
                      </p>
                    </div>
                    
                    <div className="bg-slate-50 p-2 rounded flex items-center gap-2 border border-slate-100">
                      <Package className="h-4 w-4 text-emerald-600" />
                      <div className="text-xs">
                        <span className="block font-semibold text-slate-700 capitalize">{donation.food_type}</span>
                        <span className="text-slate-500">{donation.quantity} packs</span>
                      </div>
                    </div>

                    <button
                      onClick={() => acceptMatch.mutate(matchId)}
                      disabled={isAccepting}
                      className="w-full btn-primary py-1.5 px-3 text-xs flex justify-center"
                    >
                      {isAccepting ? <Loader2 className="h-3 w-3 animate-spin mr-1" /> : <Check className="h-3 w-3 mr-1" />}
                      {isAccepting ? 'Accepting...' : 'Accept Donation'}
                    </button>
                  </div>
                </Popup>
              </Marker>
            )
          })}
        </MapContainer>
      </div>
    </div>
  )
}

import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { MapContainer, TileLayer, Marker, Polyline, Popup } from 'react-leaflet'
import { LatLng } from 'leaflet'
import { Navigation, MapPin, Camera, Check, Loader2, Truck } from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'
import 'leaflet/dist/leaflet.css'

import L from 'leaflet'
delete L.Icon.Default.prototype._getIconUrl

const restIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

const ngoIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})

export default function ActiveDelivery() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef(null)
  
  const [photoBase64, setPhotoBase64] = useState(null)

  const { data: delivery, isLoading } = useQuery({
    queryKey: ['activeDelivery'],
    queryFn: async () => {
      // Assuming a dedicated endpoint, or fallback to filtering deliveries
      try {
        const res = await api.get('/deliveries/active')
        const items = res.data?.items ?? res.data ?? []
        // Return first active delivery assigned to this volunteer
        return items[0] || null
      } catch (e) {
        return null
      }
    },
    refetchInterval: 15_000,
  })

  const updateStatus = useMutation({
    mutationFn: (status) => api.patch(`/deliveries/${delivery?.id}/status`, { status }),
    onSuccess: (data, variables) => {
      toast.success(variables === 'picked_up' ? 'Marked as picked up!' : 'Marked as delivered!')
      queryClient.invalidateQueries({ queryKey: ['activeDelivery'] })
    },
    onError: () => toast.error('Failed to update status')
  })

  const confirmDelivery = useMutation({
    mutationFn: (payload) => api.post(`/deliveries/${delivery?.id}/confirm`, payload),
    onSuccess: () => {
      toast.success('Delivery confirmed and completed!')
      setPhotoBase64(null)
      queryClient.invalidateQueries({ queryKey: ['activeDelivery'] })
      queryClient.invalidateQueries({ queryKey: ['deliveryHistory'] })
    },
    onError: () => toast.error('Failed to confirm delivery')
  })

  const handlePhotoCapture = (e) => {
    const file = e.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onloadend = () => {
      setPhotoBase64(reader.result) // includes data:image/jpeg;base64,...
    }
    reader.readAsDataURL(file)
  }

  const handleConfirm = () => {
    if (!photoBase64) return toast.error('Please capture a photo first')
    confirmDelivery.mutate({ photo: photoBase64 })
  }

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-500">
        <Loader2 className="h-8 w-8 animate-spin text-[#1D9E75] mb-4" />
        <p>Loading active route...</p>
      </div>
    )
  }

  if (!delivery) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <div className="h-16 w-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
          <Truck className="h-8 w-8 text-slate-400" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">No active delivery</h2>
        <p className="text-slate-500 mt-2 text-sm">You are not currently assigned to any deliveries. Check the Pickups tab.</p>
      </div>
    )
  }

  // Parse coordinates [lng, lat]
  const pickupCoords = delivery.pickup_location?.coordinates || [78.9629, 20.5937]
  const dropoffCoords = delivery.dropoff_location?.coordinates || [78.9629, 20.5937]
  
  const restPos = [pickupCoords[1], pickupCoords[0]]
  const ngoPos = [dropoffCoords[1], dropoffCoords[0]]

  const isPickedUp = delivery.status === 'picked_up'
  const isDelivered = delivery.status === 'delivered'

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] space-y-4">
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm flex-shrink-0">
        <h2 className="font-bold text-slate-900 capitalize text-lg">{delivery.food_type} <span className="text-slate-500 text-sm font-normal">({delivery.quantity} packs)</span></h2>
        
        <div className="mt-3 space-y-2 relative before:absolute before:inset-y-3 before:left-[9px] before:w-0.5 before:bg-slate-100">
          <div className="flex items-start gap-3 relative z-10">
            <div className={`h-5 w-5 rounded-full bg-white border-2 flex items-center justify-center flex-shrink-0 mt-0.5 ${isPickedUp ? 'border-slate-300' : 'border-[#1D9E75]'}`}>
              {!isPickedUp && <div className="h-1.5 w-1.5 rounded-full bg-[#1D9E75]"></div>}
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Restaurant</p>
              <p className={`text-xs font-medium leading-tight mt-0.5 ${isPickedUp ? 'text-slate-400 line-through' : 'text-slate-700'}`}>{delivery.pickup_address || delivery.restaurant_name}</p>
            </div>
          </div>
          <div className="flex items-start gap-3 relative z-10">
            <div className={`h-5 w-5 rounded-full bg-white border-2 flex items-center justify-center flex-shrink-0 mt-0.5 ${isDelivered ? 'border-slate-300' : isPickedUp ? 'border-blue-500' : 'border-slate-300'}`}>
              {!isDelivered && isPickedUp && <div className="h-1.5 w-1.5 rounded-full bg-blue-500"></div>}
            </div>
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">NGO</p>
              <p className="text-xs text-slate-700 font-medium leading-tight mt-0.5">{delivery.ngo_address || delivery.ngo_name}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 rounded-2xl overflow-hidden border border-slate-200 shadow-sm relative z-0 min-h-[200px]">
        <MapContainer bounds={[restPos, ngoPos]} zoomPadding={[50, 50]} scrollWheelZoom={false} className="h-full w-full">
          <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <Marker position={restPos} icon={restIcon}>
            <Popup>Pickup: {delivery.restaurant_name}</Popup>
          </Marker>
          <Marker position={ngoPos} icon={ngoIcon}>
            <Popup>Dropoff: {delivery.ngo_name}</Popup>
          </Marker>
          <Polyline positions={[restPos, ngoPos]} color="#1D9E75" weight={4} dashArray="5, 10" />
        </MapContainer>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm flex-shrink-0">
        {!isPickedUp ? (
          <button 
            onClick={() => updateStatus.mutate('picked_up')} 
            disabled={updateStatus.isPending}
            className="btn-primary w-full py-3.5 text-base"
          >
            {updateStatus.isPending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Package className="h-5 w-5" />}
            Mark as Picked Up
          </button>
        ) : !isDelivered ? (
          <button 
            onClick={() => updateStatus.mutate('delivered')} 
            disabled={updateStatus.isPending}
            className="btn-primary w-full py-3.5 text-base bg-blue-600 hover:bg-blue-700 focus:ring-blue-500 shadow-blue-200"
          >
            {updateStatus.isPending ? <Loader2 className="h-5 w-5 animate-spin" /> : <MapPin className="h-5 w-5" />}
            Mark as Delivered
          </button>
        ) : (
          <div className="space-y-3">
            <input 
              type="file" 
              accept="image/*" 
              capture="environment" 
              ref={fileInputRef}
              onChange={handlePhotoCapture}
              className="hidden" 
            />
            
            {photoBase64 ? (
              <div className="relative rounded-xl overflow-hidden border border-slate-200 bg-slate-100 aspect-[4/3]">
                <img src={photoBase64} alt="Delivery Proof" className="w-full h-full object-cover" />
                <button 
                  onClick={() => fileInputRef.current?.click()}
                  className="absolute bottom-2 right-2 bg-black/50 text-white text-xs px-3 py-1.5 rounded-lg backdrop-blur"
                >
                  Retake
                </button>
              </div>
            ) : (
              <button 
                onClick={() => fileInputRef.current?.click()}
                className="w-full py-8 border-2 border-dashed border-[#1D9E75]/30 bg-emerald-50 text-[#1D9E75] rounded-xl flex flex-col items-center justify-center gap-2 hover:bg-emerald-100 transition-colors"
              >
                <Camera className="h-8 w-8 opacity-80" />
                <span className="font-semibold">Take Proof Photo</span>
              </button>
            )}

            <button 
              onClick={handleConfirm}
              disabled={confirmDelivery.isPending || !photoBase64}
              className="btn-primary w-full py-3.5 text-base"
            >
              {confirmDelivery.isPending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Check className="h-5 w-5" />}
              Confirm Delivery
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

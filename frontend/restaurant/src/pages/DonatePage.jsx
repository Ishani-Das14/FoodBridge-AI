import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import { LatLng } from 'leaflet'
import { PlusCircle, Loader2 } from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'
import 'leaflet/dist/leaflet.css'

import L from 'leaflet'
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
})

function LocationPicker({ onSelect }) {
  useMapEvents({
    click(e) {
      onSelect(e.latlng)
    },
  })
  return null
}

export default function DonatePage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  
  const [location, setLocation] = useState(null)
  const [form, setForm] = useState({
    food_type: 'Rice',
    quantity: '',
    prepared_at: '',
    expiry_time: '',
    pickup_address: '',
  })

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const createDonation = useMutation({
    mutationFn: (payload) => api.post('/donations', payload),
    onSuccess: () => {
      toast.success('Donation created successfully!')
      queryClient.invalidateQueries({ queryKey: ['activeDonations'] })
      navigate('/dashboard')
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Failed to create donation')
    }
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!location) {
      toast.error('Please pick a pickup location on the map')
      return
    }

    // Convert expiry_time from minutes to an ISO string
    const expiryDate = new Date()
    expiryDate.setMinutes(expiryDate.getMinutes() + Number(form.expiry_time))

    const payload = {
      food_type: form.food_type,
      quantity: Number(form.quantity),
      prepared_at: new Date(form.prepared_at).toISOString(),
      expiry_time: expiryDate.toISOString(),
      pickup_address: form.pickup_address,
      pickup_location: {
        type: 'Point',
        coordinates: [location.lng, location.lat],
      },
    }
    createDonation.mutate(payload)
  }

  const foodOptions = ['Rice', 'Biryani', 'Roti', 'Dal', 'Mixed', 'Other']

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-900">Donate Food</h1>
      <form onSubmit={handleSubmit} className="space-y-6 max-w-4xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Food Type</label>
            <select name="food_type" value={form.food_type} onChange={handleChange} className="input">
              {foodOptions.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
            </select>
          </div>
          <div>
            <label className="label">Quantity (kg)</label>
            <input type="number" name="quantity" min="0" step="0.1" required value={form.quantity} onChange={handleChange} placeholder="e.g., 12.5" className="input" />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Prepared At</label>
            <input type="datetime-local" name="prepared_at" required value={form.prepared_at} onChange={handleChange} className="input" />
          </div>
          <div>
            <label className="label">Expiry in (minutes)</label>
            <input type="number" name="expiry_time" min="30" required value={form.expiry_time} onChange={handleChange} placeholder="e.g., 120" className="input" />
          </div>
        </div>
        
        <div>
          <label className="label">Pickup Address (Text)</label>
          <input type="text" name="pickup_address" required value={form.pickup_address} onChange={handleChange} placeholder="123 Main St..." className="input" />
        </div>

        <div>
          <label className="label">Pickup Location (Map)</label>
          <p className="text-sm text-slate-500 mb-2">Click on the map to set the exact pickup coordinates.</p>
          <div className="border rounded-xl overflow-hidden h-96">
            <MapContainer center={[20.5937, 78.9629]} zoom={5} scrollWheelZoom={true} className="leaflet-container h-full">
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <LocationPicker onSelect={setLocation} />
              {location && <Marker position={new LatLng(location.lat, location.lng)} />}
            </MapContainer>
          </div>
        </div>

        <button type="submit" disabled={createDonation.isPending} className="btn-primary flex items-center gap-2">
          {createDonation.isPending ? <Loader2 className="h-5 w-5 animate-spin" /> : <PlusCircle className="h-5 w-5" />}
          {createDonation.isPending ? 'Creating...' : 'Create Donation'}
        </button>
      </form>
    </div>
  )
}

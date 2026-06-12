import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet'
import { LatLng } from 'leaflet'
import { Utensils, Clock, Calendar, FileText, Loader2, PlusCircle } from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'
import 'leaflet/dist/leaflet.css'

// Fix default marker icons (leaflet's images are not bundled by Vite by default)
import L from 'leaflet'
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: new URL('leaflet/dist/images/marker-icon-2x.png', import.meta.url).href,
  iconUrl: new URL('leaflet/dist/images/marker-icon.png', import.meta.url).href,
  shadowUrl: new URL('leaflet/dist/images/marker-shadow.png', import.meta.url).href,
})

function LocationPicker({ onSelect }) {
  const map = useMapEvents({
    click(e) {
      onSelect(e.latlng)
    },
  })
  return null
}

export default function DonatePage() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [location, setLocation] = useState(null)
  const [form, setForm] = useState({
    food_type: 'Rice',
    quantity: '',
    prepared_at: '',
    expiry_time: '',
  })

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!location) {
      toast.error('Please pick a pickup location on the map')
      return
    }
    setLoading(true)
    try {
      const payload = {
        ...form,
        quantity: Number(form.quantity),
        pickup_location: {
          type: 'Point',
          coordinates: [location.lng, location.lat],
        },
      }
      await api.post('/donations', payload)
      toast.success('Donation created!')
      navigate('/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create donation')
    } finally {
      setLoading(false)
    }
  }

  const foodOptions = ['Rice', 'Biryani', 'Roti', 'Dal', 'Mixed', 'Other']

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-slate-900">Donate Food</h1>
      <form onSubmit={handleSubmit} className="space-y-6 max-w-3xl">
        {/* Food type & quantity */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Food Type</label>
            <select
              name="food_type"
              value={form.food_type}
              onChange={handleChange}
              className="input"
            >
              {foodOptions.map((opt) => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Quantity (kg)</label>
            <input
              type="number"
              name="quantity"
              min="0"
              step="0.1"
              required
              value={form.quantity}
              onChange={handleChange}
              placeholder="e.g., 12.5"
              className="input"
            />
          </div>
        </div>

        {/* Prepared & expiry */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Prepared At</label>
            <input
              type="datetime-local"
              name="prepared_at"
              required
              value={form.prepared_at}
              onChange={handleChange}
              className="input"
            />
          </div>
          <div>
            <label className="label">Expiry</label>
            <input
              type="datetime-local"
              name="expiry_time"
              required
              value={form.expiry_time}
              onChange={handleChange}
              className="input"
            />
          </div>
        </div>

        {/* Map picker */}
        <div className="border rounded-xl overflow-hidden h-96">
          <MapContainer
            center={[20.5937, 78.9629]}
            zoom={5}
            scrollWheelZoom={true}
            className="leaflet-container"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <LocationPicker onSelect={setLocation} />
            {location && <Marker position={new LatLng(location.lat, location.lng)} />}
          </MapContainer>
        </div>
        <p className="text-sm text-slate-500">Click on the map to set the pickup location.</p>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="btn-primary flex items-center gap-2"
        >
          {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <PlusCircle className="h-5 w-5" />}
          {loading ? 'Creating...' : 'Create Donation'}
        </button>
      </form>
    </div>
  )
}

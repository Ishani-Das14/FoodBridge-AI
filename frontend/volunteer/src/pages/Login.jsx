import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Mail, Lock, ArrowRight, Loader2, Package, MapPin } from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'

export default function Login() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const requestGeolocation = () => {
    return new Promise((resolve) => {
      if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
          (pos) => resolve(pos),
          (err) => {
            console.warn('Geolocation denied or failed', err)
            toast.error('Location access denied. Some features may not work.')
            resolve(null)
          },
          { enableHighAccuracy: true, timeout: 5000 }
        )
      } else {
        resolve(null)
      }
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', {
        email: form.email,
        password: form.password,
      })
      
      localStorage.setItem('volunteer_access_token', data.access_token)
      localStorage.setItem('volunteer_user', JSON.stringify(data.user ?? {}))
      
      toast.success('Login successful! Requesting location...')
      
      // Request location after login as per requirements
      await requestGeolocation()
      
      navigate('/pickups')
    } catch (err) {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        toast.error(detail[0]?.msg || 'Validation error')
      } else {
        toast.error(detail || 'Invalid credentials')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-2">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1D9E75] shadow-md shadow-emerald-200 mb-6">
            <Package className="h-7 w-7 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-slate-900 tracking-tight">Volunteer</h2>
          <p className="mt-2 text-sm text-slate-500">Sign in to start delivering food.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="email" className="label text-xs">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input id="email" type="email" name="email" required value={form.email} onChange={handleChange} className="input pl-10" />
            </div>
          </div>
          <div>
            <label htmlFor="password" className="label text-xs">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input id="password" type="password" name="password" required value={form.password} onChange={handleChange} className="input pl-10" />
            </div>
          </div>
          
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 flex items-start gap-3 mt-4">
            <MapPin className="h-5 w-5 text-[#1D9E75] flex-shrink-0 mt-0.5" />
            <p className="text-[11px] text-slate-500 leading-tight">
              We will request your location after login to show you the closest pickups.
            </p>
          </div>

          <button type="submit" disabled={loading} className="btn-primary mt-2">
            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <>Sign in <ArrowRight className="h-4 w-4" /></>}
          </button>
        </form>

        <p className="text-center text-sm text-slate-500">
          New volunteer?{' '}
          <Link to="/register" className="font-semibold text-[#1D9E75] hover:underline">Register here</Link>
        </p>
      </div>
    </div>
  )
}

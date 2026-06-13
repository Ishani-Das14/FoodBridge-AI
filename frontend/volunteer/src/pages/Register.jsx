import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Mail, Lock, User, MapPin, ArrowRight, Loader2, Package } from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    phone_number: '',
  })
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/auth/register/volunteer', form)
      toast.success('Registration successful! Please log in.')
      navigate('/login')
    } catch (err) {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        toast.error(detail[0]?.msg || 'Validation error')
      } else {
        toast.error(detail || 'Registration failed')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-2 py-8">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#1D9E75] shadow-md shadow-emerald-200 mb-6">
            <Package className="h-7 w-7 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-slate-900 tracking-tight">Join Us</h2>
          <p className="mt-2 text-sm text-slate-500">Become a FoodBridge volunteer.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="name" className="label text-xs">Full Name</label>
            <div className="relative">
              <User className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input id="name" type="text" name="name" required value={form.name} onChange={handleChange} className="input pl-10" />
            </div>
          </div>
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
          <div>
            <label htmlFor="phone_number" className="label text-xs">Phone Number</label>
            <div className="relative">
              <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input id="phone_number" type="text" name="phone_number" required value={form.phone_number} onChange={handleChange} className="input pl-10" />
            </div>
          </div>

          <button type="submit" disabled={loading} className="btn-primary mt-4">
            {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <>Create Account <ArrowRight className="h-4 w-4" /></>}
          </button>
        </form>

        <p className="text-center text-sm text-slate-500">
          Already registered?{' '}
          <Link to="/login" className="font-semibold text-[#1D9E75] hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  )
}

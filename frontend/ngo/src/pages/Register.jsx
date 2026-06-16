import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { HeartHandshake, Mail, Lock, Building2, MapPin, Navigation, Users, ArrowRight, Loader2 } from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    registration_number: '',
    address: '',
    capacity: '',
  })
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const payload = {
        ...form,
        capacity: Number(form.capacity),
      }
      await api.post('/auth/register/ngo', payload)
      toast.success('Account created! Please sign in.')
      navigate('/login')
    } catch (err) {
      const detail = err.response?.data?.detail
      if (Array.isArray(detail)) {
        toast.error(detail.map(d => d.msg || String(d)).join(', '))
      } else if (typeof detail === 'string') {
        toast.error(detail)
      } else {
        toast.error('Registration failed. Please check your inputs.')
      }
    } finally {
      setLoading(false)
    }
  }

  const fields = [
    { id: 'name', label: 'NGO Name', type: 'text', icon: Building2 },
    { id: 'email', label: 'Email address', type: 'email', icon: Mail },
    { id: 'password', label: 'Password', type: 'password', icon: Lock },
    { id: 'registration_number', label: 'Registration No.', type: 'text', icon: MapPin },
    { id: 'address', label: 'Full Address', type: 'text', icon: Navigation },
    { id: 'capacity', label: 'Capacity (max meals/day)', type: 'number', icon: Users },
  ]

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-2/5 flex-col justify-between p-12 bg-gradient-to-br from-emerald-500 via-teal-600 to-cyan-700 relative overflow-hidden">
        <div className="relative flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/20 backdrop-blur">
            <HeartHandshake className="h-6 w-6 text-white" />
          </div>
          <span className="text-xl font-bold text-white">FoodBridge AI</span>
        </div>
        <div className="relative space-y-4">
          <h1 className="text-4xl font-bold text-white leading-tight">
            Partner with us.
          </h1>
          <p className="text-emerald-100 text-lg leading-relaxed max-w-xs">
            Register your NGO to start receiving food donations matching your capacity.
          </p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 bg-white overflow-y-auto">
        <div className="w-full max-w-md space-y-7 py-8">
          <div>
            <h2 className="text-3xl font-bold text-slate-900">Create account</h2>
            <p className="mt-2 text-slate-500">
              Already registered?{' '}
              <Link to="/login" className="text-emerald-600 font-semibold hover:underline">Sign in</Link>
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {fields.map(({ id, label, type, icon: Icon }) => (
              <div key={id}>
                <label htmlFor={id} className="label">{label}</label>
                <div className="relative">
                  <Icon className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                  <input id={id} name={id} type={type} required min={type === 'number' ? '1' : undefined} value={form[id]} onChange={handleChange} className="input pl-10" />
                </div>
              </div>
            ))}
            <button type="submit" disabled={loading} className="btn-primary w-full text-base py-3 mt-2">
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <>Create account <ArrowRight className="h-4 w-4" /></>}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

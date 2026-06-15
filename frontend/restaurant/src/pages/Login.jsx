import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Utensils, Mail, Lock, ArrowRight, Loader2 } from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'

export default function Login() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await api.post('/auth/login', {
        email: form.email,
        password: form.password,
      })
      localStorage.setItem('fb_access_token', data.access_token)
      localStorage.setItem('fb_user', JSON.stringify(data.user ?? {}))
      toast.success('Welcome back!')
      navigate('/dashboard')
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
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-12 bg-gradient-to-br from-blue-600 via-indigo-600 to-violet-700 relative overflow-hidden">
        <div className="relative flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/20 backdrop-blur">
            <Utensils className="h-6 w-6 text-white" />
          </div>
          <span className="text-xl font-bold text-white">FoodBridge AI</span>
        </div>
        <div className="relative space-y-4">
          <h1 className="text-4xl font-bold text-white leading-tight">
            Turning surplus<br />into sustenance.
          </h1>
          <p className="text-blue-100 text-lg leading-relaxed max-w-sm">
            Connect your restaurant with local NGOs and make every meal count. Reduce waste, build impact.
          </p>
        </div>
        <div className="relative flex items-center gap-6">
          {[
            { value: '12K+', label: 'Meals donated' },
            { value: '80+', label: 'NGO partners' },
            { value: '4.8T', label: 'Food saved (kg)' },
          ].map(({ value, label }) => (
            <div key={label}>
              <div className="text-2xl font-bold text-white">{value}</div>
              <div className="text-xs text-blue-200 mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 bg-white">
        <div className="w-full max-w-md space-y-8">
          <div>
            <h2 className="text-3xl font-bold text-slate-900">Sign in</h2>
            <p className="mt-2 text-slate-500">Don&rsquo;t have an account?{' '}
              <Link to="/register" className="text-blue-600 font-semibold hover:underline">Register</Link>
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label htmlFor="email" className="label">Email address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                <input id="email" type="email" name="email" required value={form.email} onChange={handleChange} placeholder="you@restaurant.com" className="input pl-10" />
              </div>
            </div>
            <div>
              <label htmlFor="password" className="label">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                <input id="password" type="password" name="password" required value={form.password} onChange={handleChange} placeholder="••••••••" className="input pl-10" />
              </div>
            </div>
            <button type="submit" disabled={loading} className="btn-primary w-full text-base py-3">
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <>Sign in <ArrowRight className="h-4 w-4" /></>}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

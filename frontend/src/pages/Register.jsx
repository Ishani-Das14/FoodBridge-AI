import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Utensils, Mail, Lock, Building2, FileText, MapPin, ArrowRight, Loader2 } from 'lucide-react'
import api from '../lib/api.js'
import toast from 'react-hot-toast'

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    fssai_license: '',
    city: '',
  })
  const [loading, setLoading] = useState(false)

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/auth/register/restaurant', form)
      toast.success('Account created! Please sign in.')
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

  const fields = [
    { id: 'name',          label: 'Restaurant name',    type: 'text',     icon: Building2, placeholder: 'Spice Garden' },
    { id: 'email',         label: 'Email address',      type: 'email',    icon: Mail,      placeholder: 'you@restaurant.com', autoComplete: 'email' },
    { id: 'password',      label: 'Password',           type: 'password', icon: Lock,      placeholder: '••••••••', autoComplete: 'new-password' },
    { id: 'fssai_license', label: 'FSSAI license no.',  type: 'text',     icon: FileText,  placeholder: '10012345678901' },
    { id: 'city',          label: 'City',               type: 'text',     icon: MapPin,    placeholder: 'Mumbai' },
  ]

  return (
    <div className="min-h-screen flex">
      {/* Left panel */}
      <div className="hidden lg:flex lg:w-2/5 flex-col justify-between p-12 bg-gradient-to-br from-emerald-500 via-teal-600 to-cyan-700 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className="absolute rounded-full bg-white"
              style={{
                width: `${100 + i * 70}px`,
                height: `${100 + i * 70}px`,
                bottom: `${5 + i * 12}%`,
                right: `${-15 + i * 10}%`,
              }}
            />
          ))}
        </div>
        <div className="relative flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/20 backdrop-blur">
            <Utensils className="h-6 w-6 text-white" />
          </div>
          <span className="text-xl font-bold text-white">FoodBridge AI</span>
        </div>
        <div className="relative space-y-4">
          <h1 className="text-4xl font-bold text-white leading-tight">
            Join the<br />movement.
          </h1>
          <p className="text-emerald-100 text-lg leading-relaxed max-w-xs">
            Register your restaurant and start donating surplus food to those who need it most.
          </p>
        </div>
        <div className="relative">
          <div className="rounded-2xl bg-white/10 backdrop-blur p-4 border border-white/20">
            <p className="text-sm text-white/80">
              &ldquo;We've donated over 2,000 meals through FoodBridge. It's incredibly easy.&rdquo;
            </p>
            <p className="text-xs text-white/60 mt-2">— Rahul Sharma, Chef & Owner, Spice Route</p>
          </div>
        </div>
      </div>

      {/* Right form */}
      <div className="flex-1 flex items-center justify-center p-6 bg-white overflow-y-auto">
        <div className="w-full max-w-md space-y-7 py-8">
          <div className="flex items-center gap-2.5 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600">
              <Utensils className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold text-slate-900">FoodBridge AI</span>
          </div>

          <div>
            <h2 className="text-3xl font-bold text-slate-900">Create account</h2>
            <p className="mt-2 text-slate-500">
              Already registered?{' '}
              <Link to="/login" className="text-blue-600 font-semibold hover:underline">Sign in</Link>
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {fields.map(({ id, label, type, icon: Icon, placeholder, autoComplete }) => (
              <div key={id}>
                <label htmlFor={id} className="label">{label}</label>
                <div className="relative">
                  <Icon className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
                  <input
                    id={id}
                    name={id}
                    type={type}
                    required
                    autoComplete={autoComplete}
                    value={form[id]}
                    onChange={handleChange}
                    placeholder={placeholder}
                    className="input pl-10"
                  />
                </div>
              </div>
            ))}

            <button
              type="submit"
              id="register-submit"
              disabled={loading}
              className="btn-primary w-full text-base py-3 mt-2"
            >
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : (
                <>Create account <ArrowRight className="h-4 w-4" /></>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

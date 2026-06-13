import { NavLink, useNavigate } from 'react-router-dom'
import { MapPin, Navigation, History, LogOut, Package } from 'lucide-react'

const NAV_LINKS = [
  { to: '/pickups', label: 'Pickups', icon: MapPin },
  { to: '/active', label: 'Active Route', icon: Navigation },
  { to: '/history', label: 'History', icon: History },
]

export default function Navbar() {
  const navigate = useNavigate()

  const handleLogout = () => {
    localStorage.removeItem('volunteer_access_token')
    localStorage.removeItem('volunteer_user')
    navigate('/login')
  }

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-slate-100 bg-white shadow-sm">
        <div className="mx-auto max-w-lg px-4 flex h-14 items-center justify-between">
          <div className="flex items-center gap-2 text-[#1D9E75]">
            <Package className="h-6 w-6" />
            <span className="font-bold tracking-tight text-slate-900">Volunteer</span>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-500 hover:text-red-600 hover:bg-red-50 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </header>

      {/* Mobile Bottom Navigation (typical for PWAs) */}
      <nav className="fixed bottom-0 z-50 w-full border-t border-slate-200 bg-white pb-safe">
        <div className="mx-auto max-w-lg flex justify-around">
          {NAV_LINKS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex-1 flex flex-col items-center gap-1 py-3 px-2 text-[11px] font-semibold transition-colors ${
                  isActive ? 'text-[#1D9E75]' : 'text-slate-500 hover:text-slate-700'
                }`
              }
            >
              <Icon className="h-6 w-6" />
              {label}
            </NavLink>
          ))}
        </div>
      </nav>
    </>
  )
}

import { Link, NavLink, useNavigate } from 'react-router-dom'
import { Rss, Map as MapIcon, Truck, History, LogOut, HeartHandshake } from 'lucide-react'

const NAV_LINKS = [
  { to: '/feed', label: 'Live Feed', icon: Rss },
  { to: '/map', label: 'Map View', icon: MapIcon },
  { to: '/active', label: 'Active Deliveries', icon: Truck },
  { to: '/history', label: 'History', icon: History },
]

export default function Navbar() {
  const navigate = useNavigate()

  const handleLogout = () => {
    localStorage.removeItem('ngo_access_token')
    localStorage.removeItem('ngo_user')
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-100 bg-white/80 backdrop-blur-lg shadow-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link to="/feed" className="flex items-center gap-2.5 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 shadow-md shadow-emerald-200 group-hover:shadow-emerald-300 transition-shadow">
              <HeartHandshake className="h-5 w-5 text-white" />
            </div>
            <div className="leading-tight">
              <span className="block text-[15px] font-bold text-slate-900 tracking-tight">FoodBridge</span>
              <span className="block text-[10px] font-semibold text-emerald-600 uppercase tracking-widest -mt-0.5">NGO Portal</span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`
                }
              >
                <Icon className="h-4 w-4" />
                {label}
              </NavLink>
            ))}
          </nav>

          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-slate-600 hover:text-red-600 hover:bg-red-50 transition-all duration-150"
          >
            <LogOut className="h-4 w-4" />
            <span className="hidden sm:block">Sign Out</span>
          </button>
        </div>
      </div>

      {/* Mobile nav */}
      <nav className="md:hidden flex border-t border-slate-100 bg-white overflow-x-auto">
        {NAV_LINKS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex-1 flex flex-col items-center gap-0.5 py-2.5 px-2 min-w-[80px] text-[10px] font-semibold transition-colors ${
                isActive ? 'text-emerald-600' : 'text-slate-500'
              }`
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>
    </header>
  )
}

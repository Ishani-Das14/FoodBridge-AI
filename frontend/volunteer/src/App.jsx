import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'

import Login from './pages/Login.jsx'
import Register from './pages/Register.jsx'
import Pickups from './pages/Pickups.jsx'
import ActiveDelivery from './pages/ActiveDelivery.jsx'
import History from './pages/History.jsx'
import Navbar from './components/Navbar.jsx'

import { setupPushNotifications } from './lib/push.js'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
})

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('volunteer_access_token')
  if (!token) return <Navigate to="/login" replace />
  return children
}

function AppLayout({ children }) {
  // Try setting up push notifications automatically for logged in users
  useEffect(() => {
    setupPushNotifications()
  }, [])

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />
      {/* Add pb-20 to account for fixed bottom navigation */}
      <main className="flex-1 mx-auto w-full max-w-lg px-4 py-6 pb-24">
        {children}
      </main>
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          <Route path="/pickups" element={<ProtectedRoute><AppLayout><Pickups /></AppLayout></ProtectedRoute>} />
          <Route path="/active" element={<ProtectedRoute><AppLayout><ActiveDelivery /></AppLayout></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><AppLayout><History /></AppLayout></ProtectedRoute>} />
          
          <Route path="*" element={<Navigate to="/pickups" replace />} />
        </Routes>
      </BrowserRouter>

      <Toaster position="top-center" toastOptions={{ duration: 3000 }} />
    </QueryClientProvider>
  )
}

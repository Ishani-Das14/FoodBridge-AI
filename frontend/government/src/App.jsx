import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Analytics from './pages/Analytics';
import Forecast from './pages/Forecast';
import EmergencyMode from './pages/EmergencyMode';
import { LayoutDashboard, Map, AlertOctagon } from 'lucide-react';

const queryClient = new QueryClient();

function Layout({ children }) {
  return (
    <div className="flex h-screen bg-slate-100">
      <aside className="w-64 bg-white border-r border-slate-200">
        <div className="p-6 border-b border-slate-200">
          <h1 className="text-xl font-bold text-slate-800 tracking-tight">FoodBridge Gov</h1>
          <p className="text-xs text-slate-500 mt-1">Analytics Portal</p>
        </div>
        <nav className="p-4 space-y-2">
          <Link to="/" className="flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-600 hover:bg-slate-50 hover:text-blue-600 transition-colors font-medium">
            <LayoutDashboard size={20} />
            <span>Dashboard</span>
          </Link>
          <Link to="/forecast" className="flex items-center space-x-3 px-4 py-3 rounded-xl text-slate-600 hover:bg-slate-50 hover:text-blue-600 transition-colors font-medium">
            <Map size={20} />
            <span>ML Forecast</span>
          </Link>
          <Link to="/emergency" className="flex items-center space-x-3 px-4 py-3 rounded-xl text-red-600 hover:bg-red-50 transition-colors font-bold">
            <AlertOctagon size={20} />
            <span>Emergency Mode</span>
          </Link>
        </nav>
      </aside>
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Analytics />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/emergency" element={<EmergencyMode />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

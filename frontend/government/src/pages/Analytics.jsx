import React from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  BarChart, Bar
} from 'recharts';
import { TrendingUp, Package, Leaf, AlertCircle } from 'lucide-react';

const fetchOverview = async () => (await axios.get('http://127.0.0.1:8000/api/v1/analytics/overview')).data;
const fetchWasteTrend = async () => (await axios.get('http://127.0.0.1:8000/api/v1/analytics/waste-trend?days=30')).data;
const fetchFunnel = async () => (await axios.get('http://127.0.0.1:8000/api/v1/analytics/donation-funnel')).data;
const fetchTopRestaurants = async () => (await axios.get('http://127.0.0.1:8000/api/v1/analytics/top-restaurants?limit=10')).data;

export default function Analytics() {
  const { data: overview, isLoading: loadingOverview } = useQuery({ queryKey: ['overview'], queryFn: fetchOverview, staleTime: 60000, refetchInterval: 60000 });
  const { data: trend, isLoading: loadingTrend } = useQuery({ queryKey: ['wasteTrend'], queryFn: fetchWasteTrend, staleTime: 60000 });
  const { data: funnel, isLoading: loadingFunnel } = useQuery({ queryKey: ['funnel'], queryFn: fetchFunnel, staleTime: 60000 });
  const { data: topRestaurants, isLoading: loadingRest } = useQuery({ queryKey: ['topRestaurants'], queryFn: fetchTopRestaurants, staleTime: 60000 });

  const funnelData = funnel ? [
    { name: 'Available', value: funnel.available, fill: '#3b82f6' },
    { name: 'Matched', value: funnel.matched, fill: '#8b5cf6' },
    { name: 'Picked Up', value: funnel.picked_up, fill: '#f59e0b' },
    { name: 'Delivered', value: funnel.delivered, fill: '#10b981' },
    { name: 'Expired', value: funnel.expired, fill: '#ef4444' }
  ] : [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 bg-slate-50 min-h-screen">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-slate-800">Government Analytics Dashboard</h1>
        <div className="text-sm text-slate-500">Live Impact Tracking</div>
      </div>

      {/* Section 1 - Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard title="Total Donations Today" value={overview?.total_donations_today || 0} icon={<Package />} color="bg-blue-100 text-blue-600" />
        <StatCard title="Meals Saved Today" value={overview?.total_meals_saved_today || 0} icon={<TrendingUp />} color="bg-green-100 text-green-600" />
        <StatCard title="Kg Food Saved" value={overview?.total_kg_saved_today || 0} icon={<Leaf />} color="bg-emerald-100 text-emerald-600" />
        <StatCard title="Active Now" value={overview?.active_donations_now || 0} icon={<AlertCircle />} color="bg-purple-100 text-purple-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Section 2 - Waste Trend Line Chart */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h2 className="text-xl font-semibold mb-6 text-slate-700">30-Day Food Recovery Trend</h2>
          <div className="h-80">
            {loadingTrend ? <p>Loading...</p> : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="date" tick={{fontSize: 12}} stroke="#94a3b8" />
                  <YAxis yAxisId="left" tick={{fontSize: 12}} stroke="#94a3b8" />
                  <YAxis yAxisId="right" orientation="right" tick={{fontSize: 12}} stroke="#94a3b8" />
                  <Tooltip contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="meals_saved" stroke="#10b981" strokeWidth={3} dot={false} activeDot={{ r: 8 }} />
                  <Line yAxisId="right" type="monotone" dataKey="kg_saved" stroke="#3b82f6" strokeWidth={3} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Section 3 - Donation Funnel */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h2 className="text-xl font-semibold mb-6 text-slate-700">Today's Donation Funnel</h2>
          <div className="h-80">
            {loadingFunnel ? <p>Loading...</p> : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart layout="vertical" data={funnelData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                  <XAxis type="number" stroke="#94a3b8" />
                  <YAxis dataKey="name" type="category" width={80} stroke="#94a3b8" />
                  <Tooltip cursor={{fill: '#f1f5f9'}} contentStyle={{borderRadius: '8px'}} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={32} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>

      {/* Section 4 - Top Restaurants */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <h2 className="text-xl font-semibold mb-6 text-slate-700">Top Contributing Restaurants (All-Time)</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 text-sm uppercase tracking-wider">
                <th className="p-4 font-medium">Rank</th>
                <th className="p-4 font-medium">Restaurant</th>
                <th className="p-4 font-medium">City</th>
                <th className="p-4 font-medium">Total Meals</th>
                <th className="p-4 font-medium">Badge</th>
              </tr>
            </thead>
            <tbody className="text-slate-700">
              {loadingRest ? <tr><td colSpan="5" className="p-4">Loading...</td></tr> : topRestaurants?.map((rest) => (
                <tr key={rest.rank} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                  <td className="p-4 font-semibold text-slate-500">#{rest.rank}</td>
                  <td className="p-4 font-medium">{rest.restaurant_name}</td>
                  <td className="p-4">{rest.city}</td>
                  <td className="p-4">{rest.total_meals}</td>
                  <td className="p-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      rest.badge === 'Gold' ? 'bg-yellow-100 text-yellow-700' :
                      rest.badge === 'Silver' ? 'bg-slate-200 text-slate-700' :
                      rest.badge === 'Bronze' ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {rest.badge}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color }) {
  return (
    <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex items-center space-x-4">
      <div className={`p-4 rounded-xl ${color}`}>
        {icon}
      </div>
      <div>
        <p className="text-sm font-medium text-slate-500">{title}</p>
        <p className="text-2xl font-bold text-slate-800">{value}</p>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { AlertTriangle, ShieldAlert, Activity } from 'lucide-react';

const fetchEmergencyStatus = async () => {
  return (await axios.get('http://127.0.0.1:8000/api/v1/admin/emergency-mode/status')).data;
};

const fetchEmergencyDonations = async () => {
  return (await axios.get('http://127.0.0.1:8000/api/v1/donations?emergency_only=true')).data;
};

export default function EmergencyMode() {
  const queryClient = useQueryClient();
  const [reason, setReason] = useState('');
  const [districtsInput, setDistrictsInput] = useState('');

  const { data: statusData, isLoading: loadingStatus } = useQuery({ 
    queryKey: ['emergencyStatus'], 
    queryFn: fetchEmergencyStatus,
    refetchInterval: 15000 
  });

  const { data: donations } = useQuery({
    queryKey: ['emergencyDonations'],
    queryFn: fetchEmergencyDonations,
    refetchInterval: 15000,
    enabled: !!statusData?.active
  });

  const activateMutation = useMutation({
    mutationFn: async (payload) => {
      // In a real app, attach bearer token
      return axios.post('http://127.0.0.1:8000/api/v1/admin/emergency-mode/activate', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['emergencyStatus']);
      setReason('');
      setDistrictsInput('');
    }
  });

  const deactivateMutation = useMutation({
    mutationFn: async () => {
      return axios.post('http://127.0.0.1:8000/api/v1/admin/emergency-mode/deactivate');
    },
    onSuccess: () => {
      queryClient.invalidateQueries(['emergencyStatus']);
    }
  });

  const handleActivate = (e) => {
    e.preventDefault();
    if (!reason) return alert('Reason is required.');
    const districts = districtsInput.split(',').map(d => d.trim()).filter(d => d);
    
    if (window.confirm("WARNING: This will override all standard matching radii and trigger alerts to all volunteers. Proceed?")) {
      activateMutation.mutate({ reason, affected_districts: districts });
    }
  };

  const handleDeactivate = () => {
    if (window.confirm("Are you sure you want to deactivate Emergency Mode?")) {
      deactivateMutation.mutate();
    }
  };

  if (loadingStatus) return <div className="p-8">Loading Emergency Protocol Status...</div>;

  const isActive = statusData?.active;
  const meta = statusData?.metadata || {};

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 min-h-screen bg-slate-50">
      
      <div className="flex items-center space-x-4">
        <ShieldAlert size={36} className={isActive ? "text-red-600" : "text-slate-400"} />
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Crisis & Emergency Protocol</h1>
          <p className="text-sm text-slate-500">Manage disaster relief distribution</p>
        </div>
      </div>

      {isActive ? (
        <div className="bg-red-50 border-2 border-red-600 rounded-2xl p-8 shadow-lg relative overflow-hidden">
          <div className="absolute top-0 right-0 bg-red-600 text-white px-4 py-1 font-bold text-sm rounded-bl-lg animate-pulse">
            LIVE CRISIS MODE
          </div>
          <h2 className="text-2xl font-black text-red-700 mb-4 flex items-center">
            <AlertTriangle className="mr-3" /> EMERGENCY MODE ACTIVE
          </h2>
          <div className="space-y-2 text-red-900 font-medium">
            <p><span className="font-bold opacity-75">Reason:</span> {meta.reason}</p>
            <p><span className="font-bold opacity-75">Affected Districts:</span> {meta.affected_districts?.join(', ')}</p>
            <p><span className="font-bold opacity-75">Activated At:</span> {new Date(meta.activated_at).toLocaleString()}</p>
            <p><span className="font-bold opacity-75">Activated By:</span> {meta.activated_by}</p>
          </div>
          <button 
            onClick={handleDeactivate}
            disabled={deactivateMutation.isLoading}
            className="mt-8 px-8 py-3 bg-red-700 hover:bg-red-800 text-white font-bold rounded-xl shadow-md transition-colors"
          >
            {deactivateMutation.isLoading ? 'Deactivating...' : 'DEACTIVATE EMERGENCY MODE'}
          </button>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">
          <h2 className="text-xl font-bold text-slate-800 mb-6">Activate New Emergency Protocol</h2>
          <form onSubmit={handleActivate} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Crisis Reason / Description</label>
              <textarea 
                value={reason}
                onChange={e => setReason(e.target.value)}
                className="w-full p-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-none"
                rows="3"
                placeholder="e.g. Severe flooding in north sector causing displacement..."
                required
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-slate-700 mb-2">Affected Districts (comma separated)</label>
              <input 
                type="text"
                value={districtsInput}
                onChange={e => setDistrictsInput(e.target.value)}
                className="w-full p-3 border border-slate-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-none"
                placeholder="District A, District B"
              />
            </div>
            <button 
              type="submit"
              disabled={activateMutation.isLoading}
              className="w-full py-4 bg-red-600 hover:bg-red-700 text-white font-black text-lg rounded-xl shadow-lg transition-transform hover:-translate-y-1"
            >
              {activateMutation.isLoading ? 'ACTIVATING...' : 'ACTIVATE EMERGENCY MODE'}
            </button>
          </form>
        </div>
      )}

      {isActive && (
        <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">
          <h2 className="text-xl font-bold text-slate-800 mb-6 flex items-center">
            <Activity className="mr-2 text-red-600" /> Live Emergency Distribution Feed
          </h2>
          <div className="space-y-4">
            {donations?.length === 0 ? (
              <p className="text-slate-500 italic">No donations matched yet during this emergency...</p>
            ) : (
              donations?.map(d => (
                <div key={d.id} className="p-4 bg-slate-50 rounded-xl border border-slate-100 flex justify-between items-center">
                  <div>
                    <span className="font-bold text-slate-800">{d.food_type}</span>
                    <span className="text-slate-500 ml-2">({d.quantity} units)</span>
                  </div>
                  <div className="px-3 py-1 bg-green-100 text-green-800 text-xs font-bold rounded-full">
                    {d.status.toUpperCase()}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

    </div>
  );
}

import React from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix Leaflet default marker icons issue in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom colored markers using simple SVG data URIs
const createIcon = (color) => new L.Icon({
  iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const redIcon = createIcon('red');
const yellowIcon = createIcon('gold');
const greenIcon = createIcon('green');

const fetchNgoGap = async () => {
  // Using the new /analytics/ngo-gap endpoint which combines forecast with actuals today
  return (await axios.get('http://127.0.0.1:8000/api/v1/analytics/ngo-gap')).data;
};

// Hardcoded NGO locations since they aren't provided by the API in this specific task setup
const NGO_LOCATIONS = {
  "1": { lat: 18.5204, lng: 73.8567 }, // Pune center
  "2": { lat: 18.5304, lng: 73.8467 }, 
  "3": { lat: 18.5104, lng: 73.8667 },
  "4": { lat: 18.5404, lng: 73.8767 },
  "5": { lat: 18.5004, lng: 73.8367 }
};

export default function Forecast() {
  const { data: gaps, isLoading } = useQuery({ queryKey: ['ngoGap'], queryFn: fetchNgoGap, staleTime: 60000 });

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 bg-slate-50 min-h-screen">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-slate-800">NGO Demand Forecast</h1>
        <div className="text-sm text-slate-500">ML Predictions vs Actual Intake</div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Section 1 - Table */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col h-[600px]">
          <h2 className="text-xl font-semibold mb-6 text-slate-700">NGO Gap Analysis (Today)</h2>
          <div className="overflow-y-auto flex-1">
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b border-slate-200 text-slate-500 text-sm uppercase tracking-wider">
                  <th className="p-3 font-medium">NGO Name</th>
                  <th className="p-3 font-medium">Predicted Need</th>
                  <th className="p-3 font-medium">Bounds</th>
                  <th className="p-3 font-medium">Received Today</th>
                  <th className="p-3 font-medium">Gap</th>
                </tr>
              </thead>
              <tbody className="text-slate-700">
                {isLoading ? <tr><td colSpan="5" className="p-4 text-center">Loading AI models...</td></tr> : 
                  gaps?.map((ngo) => {
                    const isCritical = ngo.gap > 20;
                    return (
                      <tr key={ngo.ngo_id} className={`border-b border-slate-50 hover:bg-slate-50 transition-colors ${isCritical ? 'bg-red-50 hover:bg-red-100' : ''}`}>
                        <td className="p-3 font-medium">{ngo.ngo_name}</td>
                        <td className="p-3 font-bold text-slate-800">{ngo.predicted_need}</td>
                        <td className="p-3 text-sm text-slate-500">[{ngo.lower_bound} - {ngo.upper_bound}]</td>
                        <td className="p-3 text-emerald-600 font-medium">{ngo.actual_received}</td>
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded-md text-sm font-bold ${isCritical ? 'text-red-700 bg-red-100' : 'text-slate-600'}`}>
                            {ngo.gap > 0 ? `-${ngo.gap}` : 'Met'}
                          </span>
                        </td>
                      </tr>
                    );
                  })
                }
                {gaps?.length === 0 && <tr><td colSpan="5" className="p-4 text-center text-slate-500">No ML forecasts generated for today.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>

        {/* Section 2 - Map */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 h-[600px] flex flex-col">
          <h2 className="text-xl font-semibold mb-6 text-slate-700">Live City Heatmap</h2>
          <div className="flex-1 rounded-xl overflow-hidden border border-slate-200">
            <MapContainer center={[18.5204, 73.8567]} zoom={13} style={{ height: '100%', width: '100%' }}>
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              />
              {!isLoading && gaps?.map(ngo => {
                const loc = NGO_LOCATIONS[ngo.ngo_id] || NGO_LOCATIONS["1"];
                let icon = greenIcon;
                if (ngo.gap > 20) icon = redIcon;
                else if (ngo.gap > 0) icon = yellowIcon;

                return (
                  <Marker key={ngo.ngo_id} position={[loc.lat, loc.lng]} icon={icon}>
                    <Popup>
                      <div className="font-sans">
                        <h3 className="font-bold text-base mb-1">{ngo.ngo_name}</h3>
                        <p className="m-0 text-sm"><span className="text-slate-500">Predicted Need:</span> <strong>{ngo.predicted_need}</strong></p>
                        <p className="m-0 text-sm"><span className="text-slate-500">Received Today:</span> <strong>{ngo.actual_received}</strong></p>
                        <p className="m-0 text-sm mt-1">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${ngo.gap > 20 ? 'bg-red-100 text-red-700' : ngo.gap > 0 ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-700'}`}>
                            Gap: {ngo.gap}
                          </span>
                        </p>
                      </div>
                    </Popup>
                  </Marker>
                )
              })}
            </MapContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

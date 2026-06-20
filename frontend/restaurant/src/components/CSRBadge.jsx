import React from 'react';

const CSRBadge = ({ score, badge, totalMeals, kgSaved, co2Saved, onDownloadCert }) => {
  let gradientClass = 'bg-gradient-to-r from-orange-400 to-amber-600';
  let badgeIcon = '🥉';

  if (badge === 'Platinum') {
    gradientClass = 'bg-gradient-to-r from-slate-400 to-slate-200 text-slate-800';
    badgeIcon = '💎';
  } else if (badge === 'Gold') {
    gradientClass = 'bg-gradient-to-r from-amber-300 to-yellow-500 text-slate-900';
    badgeIcon = '🥇';
  } else if (badge === 'Silver') {
    gradientClass = 'bg-gradient-to-r from-gray-300 to-gray-400 text-slate-800';
    badgeIcon = '🥈';
  }

  return (
    <div className={`p-6 rounded-2xl shadow-lg ${gradientClass} text-white flex flex-col md:flex-row justify-between items-center transition-transform hover:scale-105`}>
      <div className="flex items-center space-x-6 mb-4 md:mb-0">
        <div className="text-6xl drop-shadow-md">
          {badgeIcon}
        </div>
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{badge} Tier Member</h2>
          <p className="text-sm opacity-90 mt-1">CSR Impact Score: <span className="font-bold text-lg">{score}</span></p>
        </div>
      </div>

      <div className="flex flex-col md:flex-row space-y-3 md:space-y-0 md:space-x-8 text-center md:text-left">
        <div className="bg-white/20 p-3 rounded-xl backdrop-blur-sm">
          <p className="text-xs uppercase font-semibold tracking-wider opacity-90">Meals Donated</p>
          <p className="text-2xl font-bold">{totalMeals}</p>
        </div>
        <div className="bg-white/20 p-3 rounded-xl backdrop-blur-sm">
          <p className="text-xs uppercase font-semibold tracking-wider opacity-90">Food Saved (kg)</p>
          <p className="text-2xl font-bold">{kgSaved}</p>
        </div>
        <div className="bg-white/20 p-3 rounded-xl backdrop-blur-sm">
          <p className="text-xs uppercase font-semibold tracking-wider opacity-90">CO₂ Saved (kg)</p>
          <p className="text-2xl font-bold">{co2Saved}</p>
        </div>
      </div>

      <div className="mt-6 md:mt-0 ml-0 md:ml-6">
        <button 
          onClick={onDownloadCert}
          className="px-6 py-3 bg-slate-900 text-white rounded-xl shadow-md hover:bg-slate-800 hover:shadow-lg transition-all font-semibold text-sm"
        >
          Download Tax Certificate
        </button>
      </div>
    </div>
  );
};

export default CSRBadge;

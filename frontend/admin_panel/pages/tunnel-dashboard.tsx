import React from 'react';
import useSWR from 'swr';
import axios from 'axios';

// Fonction fetcher utilisée par SWR pour obtenir les données depuis l'API.
const fetcher = (url: string) => axios.get(url).then((res) => res.data);

const TunnelDashboard: React.FC = () => {
  // Appel de l'API pour récupérer l'overview dynamique du tunnel.
  // Ici, on interroge l'endpoint /api/analysis/dynamic-tunnel avec des paramètres par défaut.
  const { data, error } = useSWR(
    '/api/analysis/dynamic-tunnel?days=30&granularity=daily',
    fetcher
  );

  if (error) return <div>Erreur lors du chargement des données.</div>;
  if (!data) return <div>Chargement...</div>;

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">
        Tableau de Bord - Tunnel de Vente Dynamique
      </h1>
      <table className="min-w-full border-collapse border border-gray-300">
        <thead>
          <tr>
            <th className="border px-4 py-2">Date</th>
            <th className="border px-4 py-2">Étape du Tunnel</th>
            <th className="border px-4 py-2">Nombre de Posts</th>
            <th className="border px-4 py-2">Conversions</th>
            <th className="border px-4 py-2">Taux de Conversion (%)</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item: any, index: number) => (
            <tr key={index}>
              <td className="border px-4 py-2">{item.date}</td>
              <td className="border px-4 py-2">{item.funnel_stage}</td>
              <td className="border px-4 py-2">{item.posts}</td>
              <td className="border px-4 py-2">{item.conversions}</td>
              <td className="border px-4 py-2">
                {parseFloat(item.conversion_rate).toFixed(2)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TunnelDashboard;

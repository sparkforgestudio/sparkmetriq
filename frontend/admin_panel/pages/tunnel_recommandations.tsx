import React from 'react';
import useSWR from 'swr';
import axios from 'axios';

// Fonction fetcher utilisée par SWR pour récupérer les données de l'API
const fetcher = (url: string) => axios.get(url).then((res) => res.data);

const TunnelRecommendations: React.FC = () => {
  // Supposons que l'endpoint d'analyse avec recommandations soit /api/analysis/tunnel
  const { data, error } = useSWR('/api/analysis/tunnel?days=30&granularity=daily', fetcher);

  if (error) return <div>Erreur lors du chargement des recommandations.</div>;
  if (!data) return <div>Chargement...</div>;

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-4">
        Recommandations d'Optimisation du Tunnel de Vente
      </h1>
      {data.map((item: any, index: number) => (
        <div key={index} className="mb-6 border p-4 rounded shadow">
          <h2 className="text-xl font-semibold">Muse : {item.muse_id}</h2>
          <div className="mt-2">
            <h3 className="font-medium">Analyse du Tunnel :</h3>
            <ul className="list-disc ml-6">
              {item.funnel.map((stage: any, idx: number) => (
                <li key={idx}>
                  {stage.stage} : {stage.posts} posts, {stage.conversions} conversions, taux de conversion: {parseFloat(stage.conversion_rate).toFixed(2)}%
                </li>
              ))}
            </ul>
          </div>
          <div className="mt-2">
            <h3 className="font-medium">Recommandations :</h3>
            <ul className="list-disc ml-6">
              {item.recommendations.map((rec: string, recIdx: number) => (
                <li key={recIdx}>{rec}</li>
              ))}
            </ul>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TunnelRecommendations;

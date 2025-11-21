// pages/analysis/tunnel.tsx
import React, { useState, useMemo } from "react";
import useSWR from "swr";
import axios from "axios";
import { Select, SelectOption } from "@/components/ui/select";
import { DatePicker } from "@/components/ui/date-picker";

interface FunnelStage {
  stage: string;
  posts: number;
  conversions: number;
  conversion_rate: number | string;
}

interface TunnelDataItem {
  muse_id: string;
  funnel: FunnelStage[];
  recommendations: string[];
}

interface MetadataResponse {
  agencies: string[];
  muses: string[];
  platforms: string[];
}

const fetcher = (url: string) => axios.get(url).then((res) => res.data);

const TunnelAnalysisPage: React.FC = () => {
  // États pour les filtres
    const [agency, setAgency]   = useState<string>("");
    const [muse, setMuse]       = useState<string>("");
    const [platform, setPlatform] = useState<string>("");
    // on passe à Date | undefined et on initialise à undefined
    const [startDate, setStartDate] = useState<Date | undefined>(undefined);
    const [endDate, setEndDate]     = useState<Date | undefined>(undefined);

  // Récupère les métadonnées pour les options de filtre
  const { data: meta } = useSWR<MetadataResponse>(
    "/api/analysis/tunnel/meta",
    fetcher
  );

  // S’assurer qu’on a toujours un tableau même si meta est undefined
  const agencies   = meta?.agencies   ?? [];
  const muses      = meta?.muses      ?? [];
  const platforms  = meta?.platforms  ?? [];

  // Construire les options pour le Select
  const agencyOptions: SelectOption[]  = agencies .map((a) => ({ value: a, label: a }));
  const museOptions:  SelectOption[]  = muses    .map((m) => ({ value: m, label: m }));
  const platformOptions: SelectOption[] = platforms.map((p) => ({ value: p, label: p }));

  // Construire l’URL de requête en memo pour éviter les reconstructions à chaque render
  const queryKey = useMemo(() => {
    const params = new URLSearchParams();
    if (agency)    params.append("agency_id", agency);
    if (muse)      params.append("muse_id", muse);
    if (platform)  params.append("platform", platform);
    if (startDate) params.append("start_date", startDate.toISOString());
    if (endDate)   params.append("end_date", endDate.toISOString());

    const qs = params.toString();
    return `/api/analysis/tunnel${qs ? `?${qs}` : ""}`;
  }, [agency, muse, platform, startDate, endDate]);

  const { data, error } = useSWR<TunnelDataItem[]>(queryKey, fetcher, {
    revalidateOnFocus: false,
  });

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">
        Analyse & Recommandations du Tunnel de Vente
      </h1>

      {/* Barre de filtres */}
      <div className="flex flex-wrap gap-4 mb-6">
        <Select
          options={agencyOptions}
          value={agency}
          onValueChange={setAgency}
          placeholder="Agence"
        />
        <Select
          options={museOptions}
          value={muse}
          onValueChange={setMuse}
          placeholder="Muse"
        />
        <Select
          options={platformOptions}
          value={platform}
          onValueChange={setPlatform}
          placeholder="Plateforme"
        />
        <DatePicker
          selected={startDate}
          onSelect={setStartDate}
          placeholder="Date début"
        />
        <DatePicker
          selected={endDate}
          onSelect={setEndDate}
          placeholder="Date fin"
        />
      </div>

      {/* Résultats */}
      {error && (
        <div className="text-red-600">
          Erreur lors du chargement : {error.message}
        </div>
      )}
      {!data && !error && <div>Chargement…</div>}
      {data &&
        data.map((item, idx) => (
          <div key={idx} className="mb-6 border p-4 rounded shadow">
            <h2 className="text-xl font-semibold">Muse : {item.muse_id}</h2>

            <div className="mt-2">
              <h3 className="font-medium">Analyse du Tunnel :</h3>
              <ul className="list-disc ml-6">
                {item.funnel.map((stage, sidx) => (
                  <li key={sidx}>
                    {stage.stage} : {stage.posts} posts, {stage.conversions} conversions, taux :{" "}
                    {typeof stage.conversion_rate === "string"
                      ? parseFloat(stage.conversion_rate).toFixed(2)
                      : stage.conversion_rate.toFixed(2)}
                    %
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-2">
              <h3 className="font-medium">Recommandations :</h3>
              <ul className="list-disc ml-6">
                {item.recommendations.map((rec, ridx) => (
                  <li key={ridx}>{rec}</li>
                ))}
              </ul>
            </div>
          </div>
        ))}
    </div>
  );
};

export default TunnelAnalysisPage;

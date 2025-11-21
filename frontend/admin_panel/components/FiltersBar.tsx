// frontend/admin_panel/components/TunnelFilterBar.tsx
import React from "react";
import useSWR from "swr";

export interface FilterParams {
  agency_id?: string;
  muse_id?: string;
  platform?: string;
  funnel_stage?: string;
  content_type?: string;
  start_date?: string;
  end_date?: string;
}

interface TunnelFilters {
  agencies: string[];
  muses: string[];
  platforms: string[];
  stages: string[];
  types: string[];
}

interface TunnelFilterBarProps {
  onChange: (filters: FilterParams) => void;
}

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export function TunnelFilterBar({ onChange }: TunnelFilterBarProps) {
  const { data, error } = useSWR<TunnelFilters>(
    "/api/analysis/filters/tunnel",
    fetcher
  );

  if (error) return <div>Impossible de charger les filtres</div>;
  if (!data) return <div>Chargement des filtres…</div>;

  return (
    <div className="flex flex-wrap gap-4 mb-4">
      {/* Agence */}
      <div>
        <label className="block mb-1">Agence</label>
        <select
          className="border rounded p-2"
          onChange={(e) =>
            onChange({ agency_id: e.target.value || undefined })
          }
        >
          <option value="">Toutes</option>
          {data.agencies.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
      </div>

      {/* Muse */}
      <div>
        <label className="block mb-1">Muse</label>
        <select
          className="border rounded p-2"
          onChange={(e) =>
            onChange({ muse_id: e.target.value || undefined })
          }
        >
          <option value="">Toutes</option>
          {data.muses.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </div>

      {/* Plateforme */}
      <div>
        <label className="block mb-1">Plateforme</label>
        <select
          className="border rounded p-2"
          onChange={(e) =>
            onChange({ platform: e.target.value || undefined })
          }
        >
          <option value="">Toutes</option>
          {data.platforms.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>

      {/* Étape du funnel */}
      <div>
        <label className="block mb-1">Étape</label>
        <select
          className="border rounded p-2"
          onChange={(e) =>
            onChange({ funnel_stage: e.target.value || undefined })
          }
        >
          <option value="">Toutes</option>
          {data.stages.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {/* Type de contenu */}
      <div>
        <label className="block mb-1">Type de contenu</label>
        <select
          className="border rounded p-2"
          onChange={(e) =>
            onChange({ content_type: e.target.value || undefined })
          }
        >
          <option value="">Tous</option>
          {data.types.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>

      {/* Date de début */}
      <div>
        <label className="block mb-1">Depuis</label>
        <input
          type="date"
          className="border rounded p-2"
          onChange={(e) =>
            onChange({ start_date: e.target.value || undefined })
          }
        />
      </div>

      {/* Date de fin */}
      <div>
        <label className="block mb-1">Jusqu’à</label>
        <input
          type="date"
          className="border rounded p-2"
          onChange={(e) =>
            onChange({ end_date: e.target.value || undefined })
          }
        />
      </div>
    </div>
  );
}

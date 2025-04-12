import useSWR from "swr"
import axios from "@/lib/axios"

export const useStatsOverview = (query?: string) =>
  useSWR(`/api/stats/overview${query ? "?" + query : ""}`, (url) =>
    axios.get(url).then((res) => res.data.stats)
  )

export const useStatsTimeline = (query?: string) =>
  useSWR(`/api/stats/timeline${query ? "?" + query : ""}`, (url) =>
    axios.get(url).then((res) => res.data.timeline)
  )

export const useAgencies = () =>
  useSWR("/api/stats/agencies", (url) => axios.get(url).then((res) => res.data))

export const useMuses = () =>
  useSWR("/api/stats/muses", (url) => axios.get(url).then((res) => res.data))

import type { JobItem, SkillRank } from '~/types'

export interface SearchResponse {
  query: string
  count: number
  results: JobItem[]
}

export const useApi = () => {
  const config = useRuntimeConfig()
  const baseUrl = config.public.apiBaseUrl

  return {
    search: (params: Record<string, unknown>) =>
      $fetch<SearchResponse>(`${baseUrl}/api/search`, { params, timeout: 30000 }),

    topSkills: (params: Record<string, unknown>) =>
      $fetch<{ skills: SkillRank[]; n_postings: number }>(`${baseUrl}/api/skills/top`, { params, timeout: 30000 })
  }
}

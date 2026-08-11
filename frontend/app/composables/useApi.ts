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

    jobDetail: (id: number) =>
      $fetch<JobItem>(`${baseUrl}/api/jobs/${id}`, { timeout: 30000 }),

    bookmarks: () =>
      $fetch<{ count: number; results: JobItem[] }>(`${baseUrl}/api/bookmarks`, { timeout: 30000 }),

    addBookmark: (postingId: number) =>
      $fetch<{ status: string }>(`${baseUrl}/api/bookmarks`, {
        method: 'POST',
        params: { posting_id: postingId },
        timeout: 30000
      }),

    removeBookmark: (postingId: number) =>
      $fetch<{ status: string }>(`${baseUrl}/api/bookmarks/${postingId}`, {
        method: 'DELETE',
        timeout: 30000
      }),

    topSkills: (params: Record<string, unknown>) =>
      $fetch<{ skills: SkillRank[]; n_postings: number }>(`${baseUrl}/api/skills/top`, { params, timeout: 30000 })
  }
}

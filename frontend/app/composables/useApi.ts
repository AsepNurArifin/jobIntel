export const useApi = () => {
  const config = useRuntimeConfig()
  const baseUrl = config.public.apiBaseUrl

  return {
    search: (params: Record<string, unknown>) =>
      $fetch(`${baseUrl}/api/search`, { params, timeout: 30000 }),

    topSkills: (params: Record<string, unknown>) =>
      $fetch(`${baseUrl}/api/skills/top`, { params, timeout: 30000 })
  }
}

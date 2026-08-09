<script setup lang="ts">
export interface JobItem {
  id: number
  title: string
  company: string | null
  source: string
  source_url: string
  posted_date: string | null
  location: string | null
  similarity: number
  top_skills: string[]
}

defineProps<{
  job: JobItem
}>()

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'tanggal tidak diketahui'
  const d = new Date(dateStr)
  const days = Math.floor((Date.now() - d.getTime()) / 86400000)
  if (days <= 0) return 'hari ini'
  if (days === 1) return 'kemarin'
  return `${days} hari lalu`
}
</script>

<template>
  <article
    class="flex flex-col gap-3 rounded-xl border border-gray-200 bg-white p-4 shadow-sm dark:border-gray-800 dark:bg-gray-900"
  >
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0">
        <h3 class="truncate font-semibold text-gray-900 dark:text-white">{{ job.title }}</h3>
        <p class="mt-0.5 text-sm text-gray-500 dark:text-gray-400">
          {{ job.company ?? 'Perusahaan tidak disebutkan' }}
          <span v-if="job.location"> · {{ job.location }}</span>
        </p>
      </div>
      <span class="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-300">
        {{ job.source }}
      </span>
    </div>

    <div v-if="job.top_skills.length" class="flex flex-wrap gap-1.5">
      <span
        v-for="skill in job.top_skills"
        :key="skill"
        class="rounded-md bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary"
      >
        {{ skill }}
      </span>
    </div>

    <div class="flex items-center justify-between text-xs text-gray-400 dark:text-gray-500">
      <span>{{ timeAgo(job.posted_date) }}</span>
      <span>relevansi {{ Math.round(job.similarity * 100) }}%</span>
    </div>

    <UButton
      :to="job.source_url"
      target="_blank"
      rel="noopener"
      size="sm"
      variant="outline"
      class="self-start"
      color="primary"
    >
      Lihat di {{ job.source === 'remoteok' ? 'RemoteOK' : 'WeWorkRemotely' }}
    </UButton>
  </article>
</template>

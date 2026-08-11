<script setup lang="ts">
import type { JobItem } from '~/types'

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

function matchBadgeColor(score: number): string {
  if (score >= 0.8) return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800'
  if (score >= 0.6) return 'bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border-blue-200 dark:border-blue-800'
  return 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300 border-amber-200 dark:border-amber-800'
}
</script>

<template>
  <article
    class="group flex flex-col justify-between gap-4 rounded-2xl border border-gray-200/80 bg-white p-5 shadow-sm hover:shadow-xl hover:shadow-blue-500/5 hover:border-blue-500/30 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-blue-500/40 transition-all duration-300"
  >
    <div class="flex flex-col gap-3">
      <!-- Header with Title & Source Badge -->
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0 flex-1">
          <NuxtLink
            :to="job.source_url"
            target="_blank"
            rel="noopener"
            class="line-clamp-2 font-bold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors text-base leading-snug"
          >
            {{ job.title }}
          </NuxtLink>
          
          <div class="mt-1.5 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-gray-500 dark:text-gray-400 font-medium">
            <span class="flex items-center gap-1 font-semibold text-gray-700 dark:text-gray-300">
              <UIcon name="i-lucide-building-2" class="h-3.5 w-3.5 text-gray-400" />
              {{ job.company ?? 'Perusahaan Rahasia' }}
            </span>
            <span v-if="job.location" class="flex items-center gap-1">
              <span>·</span>
              <UIcon name="i-lucide-map-pin" class="h-3.5 w-3.5 text-gray-400" />
              <span>{{ job.location }}</span>
            </span>
          </div>
        </div>

        <span
          class="shrink-0 rounded-full px-2.5 py-1 text-[11px] font-bold tracking-wide uppercase shadow-xs border"
          :class="job.source === 'remoteok'
            ? 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/50 dark:text-rose-300 dark:border-rose-800'
            : 'bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950/50 dark:text-indigo-300 dark:border-indigo-800'"
        >
          {{ job.source === 'remoteok' ? 'RemoteOK' : 'WeWorkRemotely' }}
        </span>
      </div>

      <!-- Match Score & Posted Time -->
      <div class="flex items-center gap-2">
        <span
          class="inline-flex items-center gap-1 rounded-lg px-2 py-0.5 text-xs font-bold border shadow-2xs"
          :class="matchBadgeColor(job.similarity)"
        >
          <UIcon name="i-lucide-sparkles" class="h-3 w-3" />
          <span>{{ Math.round(job.similarity * 100) }}% Relevan</span>
        </span>

        <span class="flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500 font-medium">
          <UIcon name="i-lucide-clock" class="h-3.5 w-3.5" />
          <span>{{ timeAgo(job.posted_date) }}</span>
        </span>
      </div>

      <!-- Skill Pills -->
      <div v-if="job.top_skills.length" class="flex flex-wrap gap-1.5 pt-1">
        <NuxtLink
          v-for="skill in job.top_skills"
          :key="skill"
          :to="`/?q=${encodeURIComponent(skill)}`"
          class="rounded-lg bg-blue-50/80 px-2.5 py-1 text-xs font-semibold text-blue-700 hover:bg-blue-100 dark:bg-blue-950/40 dark:text-blue-300 dark:hover:bg-blue-900/60 border border-blue-200/50 dark:border-blue-800/40 transition-colors"
        >
          #{{ skill }}
        </NuxtLink>
      </div>
    </div>

    <!-- Action Button -->
    <div class="pt-2 border-t border-gray-100 dark:border-gray-800/60 flex items-center justify-between">
      <span class="text-[11px] font-medium text-gray-400 dark:text-gray-500">Klik untuk melamar</span>
      <UButton
        :to="job.source_url"
        target="_blank"
        rel="noopener"
        size="xs"
        color="primary"
        variant="soft"
        class="rounded-lg font-semibold group-hover:translate-x-0.5 transition-transform"
      >
        <span>Buka Loker</span>
        <UIcon name="i-lucide-external-link" class="h-3.5 w-3.5 ml-1" />
      </UButton>
    </div>
  </article>
</template>

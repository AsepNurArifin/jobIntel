<script setup lang="ts">
import type { SkillRank } from '~/types'

const props = defineProps<{
  skills: SkillRank[]
}>()

const maxFreq = computed(() => Math.max(1, ...props.skills.map((s) => s.freq)))

function barWidth(freq: number): string {
  return `${Math.max(6, Math.round((freq / maxFreq.value) * 100))}%`
}

function categoryBadge(category: string): { label: string; color: string } {
  switch (category?.toLowerCase()) {
    case 'hard':
      return { label: 'Hard Skill', color: 'bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 border-blue-200/60 dark:border-blue-800/60' }
    case 'soft':
      return { label: 'Soft Skill', color: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border-emerald-200/60 dark:border-emerald-800/60' }
    case 'tool':
      return { label: 'Tool', color: 'bg-purple-50 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border-purple-200/60 dark:border-purple-800/60' }
    default:
      return { label: category ?? 'General', color: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300 border-gray-200 dark:border-gray-700' }
  }
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <div
      v-for="(skill, index) in skills"
      :key="skill.name"
      class="group flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 rounded-xl p-2.5 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors border border-transparent hover:border-gray-200/60 dark:hover:border-gray-700/60"
    >
      <!-- Rank Number & Skill Name -->
      <div class="flex items-center gap-2.5 w-full sm:w-56 shrink-0 justify-between sm:justify-start">
        <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-gray-100 dark:bg-gray-800 text-xs font-bold text-gray-500 dark:text-gray-400 font-mono">
          #{{ index + 1 }}
        </span>

        <NuxtLink
          :to="`/?q=${encodeURIComponent(skill.name)}`"
          class="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors text-sm truncate flex-1"
          title="Klik untuk cari loker dengan skill ini"
        >
          {{ skill.name }}
        </NuxtLink>

        <span
          class="inline-block shrink-0 rounded-md px-2 py-0.5 text-[10px] font-bold border"
          :class="categoryBadge(skill.category).color"
        >
          {{ categoryBadge(skill.category).label }}
        </span>
      </div>

      <!-- Animated Gradient Bar -->
      <div class="relative h-6 flex-1 overflow-hidden rounded-lg bg-gray-100 dark:bg-gray-800 p-0.5">
        <div
          class="h-full rounded-md bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 transition-all duration-700 ease-out shadow-xs"
          :style="{ width: barWidth(skill.freq) }"
        />
      </div>

      <!-- Frequency Counter Badge -->
      <div class="flex items-center justify-end sm:w-20 shrink-0 font-mono text-xs font-bold text-gray-700 dark:text-gray-300">
        <span class="rounded-lg bg-gray-100 dark:bg-gray-800 px-2 py-1 border border-gray-200/60 dark:border-gray-700/60">
          {{ skill.freq }} loker
        </span>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="!skills.length" class="flex flex-col items-center justify-center py-12 text-center">
      <UIcon name="i-lucide-bar-chart-2" class="h-10 w-10 text-gray-300 dark:text-gray-600 mb-2" />
      <p class="text-sm font-medium text-gray-500 dark:text-gray-400">
        Belum ada data insight untuk kombinasi filter ini.
      </p>
    </div>
  </div>
</template>

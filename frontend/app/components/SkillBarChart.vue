<script setup lang="ts">
export interface SkillRank {
  name: string
  category: string
  freq: number
}

const props = defineProps<{
  skills: SkillRank[]
}>()

const maxFreq = computed(() => Math.max(1, ...props.skills.map((s) => s.freq)))

function barWidth(freq: number): string {
  return `${Math.max(4, Math.round((freq / maxFreq.value) * 100))}%`
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <div
      v-for="skill in skills"
      :key="skill.name"
      class="flex items-center gap-3 text-sm"
    >
      <span class="w-44 shrink-0 truncate text-right font-medium text-gray-700 dark:text-gray-200">
        {{ skill.name }}
      </span>
      <div class="h-5 flex-1 overflow-hidden rounded-md bg-gray-100 dark:bg-gray-800">
        <div
          class="h-full rounded-md bg-primary"
          :style="{ width: barWidth(skill.freq) }"
        />
      </div>
      <span class="w-10 shrink-0 text-right font-mono text-gray-500 dark:text-gray-400">
        {{ skill.freq }}
      </span>
    </div>

    <p v-if="!skills.length" class="py-6 text-center text-sm text-gray-400">
      Belum ada data untuk filter ini.
    </p>
  </div>
</template>

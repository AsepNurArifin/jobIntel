<script setup lang="ts">
const days = defineModel<number>('days')
const source = defineModel<string>('source')
const role = defineModel<string>('role')
const category = defineModel<string | null>('category')
const level = defineModel<string>('level')
const employmentType = defineModel<string>('employmentType')

const DAY_OPTIONS = [
  { label: '7 hari terakhir', value: 7 },
  { label: '30 hari terakhir', value: 30 },
  { label: '90 hari terakhir', value: 90 }
]

const CATEGORY_OPTIONS = [
  { label: 'Semua Kategori', value: '' },
  { label: 'Hard Skill', value: 'hard' },
  { label: 'Soft Skill', value: 'soft' },
  { label: 'Tools & Tech', value: 'tool' }
]

const LEVEL_OPTIONS = [
  { label: 'Semua Level', value: '' },
  { label: 'Junior', value: 'junior' },
  { label: 'Mid-Level', value: 'mid' },
  { label: 'Senior', value: 'senior' }
]

const EMPLOYMENT_OPTIONS = [
  { label: 'Semua Tipe', value: '' },
  { label: 'Remote', value: 'remote' },
  { label: 'Hybrid', value: 'hybrid' },
  { label: 'Onsite', value: 'onsite' }
]

const SOURCE_OPTIONS = [
  { label: 'Semua Sumber', value: 'all' },
  { label: 'RemoteOK', value: 'remoteok' },
  { label: 'WeWorkRemotely', value: 'wwr' },
  { label: 'Adzuna', value: 'adzuna' }
]
</script>

<template>
  <div class="flex flex-wrap items-center gap-3.5 rounded-2xl border border-gray-200/80 bg-white/90 p-4 shadow-sm backdrop-blur-md dark:border-gray-800 dark:bg-gray-900/90">
    <div v-if="days !== undefined" class="flex flex-col gap-1 min-w-[150px]">
      <label class="flex items-center gap-1 text-xs font-semibold text-gray-500 dark:text-gray-400">
        <span>Rentang Waktu</span>
      </label>
      <USelect v-model="days" :options="DAY_OPTIONS" class="w-full" size="md" />
    </div>

    <div v-if="source !== undefined" class="flex flex-col gap-1 min-w-[160px]">
      <label class="flex items-center gap-1 text-xs font-semibold text-gray-500 dark:text-gray-400">
        <span>Sumber Job</span>
      </label>
      <USelect v-model="source" size="md" :options="SOURCE_OPTIONS" />
    </div>

    <div v-if="level !== undefined" class="flex flex-col gap-1 min-w-[140px]">
      <label class="flex items-center gap-1 text-xs font-semibold text-gray-500 dark:text-gray-400">
        <span>Level Pengalaman</span>
      </label>
      <USelect v-model="level" size="md" :options="LEVEL_OPTIONS" />
    </div>

    <div v-if="employmentType !== undefined" class="flex flex-col gap-1 min-w-[140px]">
      <label class="flex items-center gap-1 text-xs font-semibold text-gray-500 dark:text-gray-400">
        <span>Tipe Pekerjaan</span>
      </label>
      <USelect v-model="employmentType" size="md" :options="EMPLOYMENT_OPTIONS" />
    </div>

    <div v-if="category !== undefined" class="flex flex-col gap-1 min-w-[160px]">
      <label class="flex items-center gap-1 text-xs font-semibold text-gray-500 dark:text-gray-400">
        <UIcon name="i-lucide-layers" class="h-3.5 w-3.5 text-purple-500" />
        <span>Kategori Skill</span>
      </label>
      <USelect :model-value="category ?? ''" size="md" :options="CATEGORY_OPTIONS" @update:model-value="(val: any) => category = val ? String(val) : null" />
    </div>

    <div v-if="role !== undefined" class="flex flex-col gap-1 min-w-[200px] flex-1">
      <label class="flex items-center gap-1 text-xs font-semibold text-gray-500 dark:text-gray-400">
        <UIcon name="i-lucide-user-check" class="h-3.5 w-3.5 text-emerald-500" />
        <span>Role Target (opsional)</span>
      </label>
      <UInput v-model="role" size="md" placeholder='mis. "data scientist"' />
    </div>
  </div>
</template>

<script setup lang="ts">
const model = defineModel<{
  days: number
  source: string
  role: string
  category: string | null
}>()

const DAY_OPTIONS = [
  { label: '7 hari', value: 7 },
  { label: '30 hari', value: 30 },
  { label: '90 hari', value: 90 }
]

const CATEGORY_OPTIONS = [
  { label: 'Semua', value: '' },
  { label: 'Hard skill', value: 'hard' },
  { label: 'Soft skill', value: 'soft' },
  { label: 'Tools', value: 'tool' }
]
</script>

<template>
  <div class="flex flex-wrap items-end gap-3 rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
    <div v-if="model.days !== undefined">
      <label class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Rentang waktu</label>
      <USelect :model-value="model.days" :options="DAY_OPTIONS" @update:model-value="model.days = $event" />
    </div>

    <div v-if="model.source !== undefined">
      <label class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Sumber</label>
      <USelect
        :model-value="model.source"
        :options="[
          { label: 'Semua', value: 'all' },
          { label: 'RemoteOK', value: 'remoteok' },
          { label: 'WeWorkRemotely', value: 'wwr' }
        ]"
        @update:model-value="model.source = $event"
      />
    </div>

    <div v-if="model.category !== undefined">
      <label class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Kategori</label>
      <USelect :model-value="model.category ?? ''" :options="CATEGORY_OPTIONS" @update:model-value="model.category = $event || null" />
    </div>

    <div v-if="model.role !== undefined" class="min-w-48 flex-1">
      <label class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Role (opsional)</label>
      <UInput v-model="model.role" placeholder='mis. "data scientist"' />
    </div>
  </div>
</template>

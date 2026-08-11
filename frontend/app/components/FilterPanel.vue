<script setup lang="ts">
const days = defineModel<number>('days')
const source = defineModel<string>('source')
const role = defineModel<string>('role')
const category = defineModel<string | null>('category')

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
    <div v-if="days !== undefined">
      <label class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Rentang waktu</label>
      <USelect v-model="days" :options="DAY_OPTIONS" />
    </div>

    <div v-if="source !== undefined">
      <label class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Sumber</label>
      <USelect
        v-model="source"
        :options="[
          { label: 'Semua', value: 'all' },
          { label: 'RemoteOK', value: 'remoteok' },
          { label: 'WeWorkRemotely', value: 'wwr' }
        ]"
      />
    </div>

    <div v-if="category !== undefined">
      <label class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Kategori</label>
      <USelect :model-value="category ?? ''" :options="CATEGORY_OPTIONS" @update:model-value="(val: any) => category = val ? String(val) : null" />
    </div>

    <div v-if="role !== undefined" class="min-w-48 flex-1">
      <label class="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Role (opsional)</label>
      <UInput v-model="role" placeholder='mis. "data scientist"' />
    </div>
  </div>
</template>

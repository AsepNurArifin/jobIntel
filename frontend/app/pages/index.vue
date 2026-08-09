<script setup lang="ts">
import type { JobItem } from '~/components/JobCard.vue'

const api = useApi()

const query = ref('')
const days = ref(30)
const source = ref('all')
const loading = ref(false)
const error = ref<string | null>(null)
const results = ref<JobItem[]>([])

async function doSearch() {
  if (!query.value.trim()) return
  loading.value = true
  error.value = null
  try {
    results.value = await api.search({
      q: query.value,
      days: days.value,
      source: source.value,
      limit: 30
    })
  } catch (e: any) {
    error.value = e?.data?.detail ?? e?.message ?? 'Gagal mengambil data. Pastikan backend berjalan di port 8000.'
    results.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // Support ?q=... dari URL (berguna saat kembali dari insight)
  const urlQ = useRoute().query.q
  if (typeof urlQ === 'string' && urlQ) {
    query.value = urlQ
    doSearch()
  }
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <section class="flex flex-col gap-3">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        Cari Loker IT
      </h1>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Search semantik lintas RemoteOK &amp; WeWorkRemotely. Klik hasil untuk menuju sumber asli.
      </p>
      <SearchBar :initial-query="query" @search="doSearch" />
      <FilterPanel v-model="days" v-model:source="source" />
    </section>

    <p v-if="error" class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
      {{ error }}
    </p>

    <p v-if="loading" class="text-sm text-gray-500 dark:text-gray-400">
      Mencari…
    </p>

    <div v-else-if="results.length" class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <JobCard v-for="job in results" :key="job.id" :job="job" />
    </div>

    <div v-else-if="!loading && query && !error" class="rounded-lg border border-dashed border-gray-300 p-8 text-center text-sm text-gray-500 dark:border-gray-700 dark:text-gray-400">
      Tidak ada hasil untuk "{{ query }}". Coba kata kunci lain atau perlebar rentang waktu.
    </div>

    <div v-else-if="!loading && !query" class="rounded-lg border border-dashed border-gray-300 p-8 text-center text-sm text-gray-400 dark:border-gray-700">
      Mulai ketik keyword untuk mencari loker.
    </div>
  </div>
</template>

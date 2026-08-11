<script setup lang="ts">
import type { JobItem } from '~/types'

const api = useApi()

const query = ref('')
const days = ref(30)
const source = ref('all')
const loading = ref(false)
const error = ref<string | null>(null)
const results = ref<JobItem[]>([])
const hasSearched = ref(false)

async function doSearch() {
  if (!query.value.trim()) return
  loading.value = true
  error.value = null
  hasSearched.value = true
  try {
    results.value = await api.search({
      q: query.value,
      days: days.value,
      source: source.value,
      limit: 30
    })
  } catch (e: any) {
    error.value = e?.data?.detail ?? e?.message ?? 'Gagal mengambil data. Pastikan backend server berjalan di port 8000.'
    results.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  // Support ?q=... dari URL (berguna saat kembali dari insight atau tag click)
  const urlQ = useRoute().query.q
  if (typeof urlQ === 'string' && urlQ) {
    query.value = urlQ
    doSearch()
  }
})

// Re-search when filter options change if query exists
watch([days, source], () => {
  if (query.value.trim() && hasSearched.value) {
    doSearch()
  }
})
</script>

<template>
  <div class="flex flex-col gap-8">
    <!-- Hero Header -->
    <section class="flex flex-col items-center text-center gap-4 py-4">
      <div class="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-3.5 py-1 text-xs font-semibold text-blue-600 dark:bg-blue-400/10 dark:text-blue-400">
        <span class="relative flex h-2 w-2">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
          <span class="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
        </span>
        <span>Pencarian Semantik &amp; AI Vector Search</span>
      </div>

      <h1 class="text-3xl sm:text-5xl font-black tracking-tight text-gray-900 dark:text-white max-w-2xl leading-tight">
        Temukan Loker Remote IT <br>
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600">
          Sesuai Skill Impianmu
        </span>
      </h1>

      <p class="text-sm sm:text-base text-gray-500 dark:text-gray-400 max-w-xl">
        JobIntel melakukan penjelajahan pintar lintas RemoteOK &amp; WeWorkRemotely dengan analisis relevansi kecerdasan buatan.
      </p>

      <!-- Main Search Box & Filters -->
      <div class="w-full max-w-3xl mt-2 flex flex-col gap-4 text-left">
        <SearchBar :initial-query="query" @search="(q) => { query = q; doSearch() }" />
        <FilterPanel v-model:days="days" v-model:source="source" />
      </div>
    </section>

    <!-- Error Alert -->
    <div
      v-if="error"
      class="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/50 dark:text-rose-300 backdrop-blur-md"
    >
      <UIcon name="i-lucide-alert-circle" class="h-5 w-5 shrink-0 text-rose-500 mt-0.5" />
      <div class="flex-1 font-medium">
        {{ error }}
      </div>
    </div>

    <!-- Results Section -->
    <section v-if="loading" class="flex flex-col gap-4">
      <div class="flex items-center justify-between text-sm font-semibold text-gray-500">
        <span class="flex items-center gap-2">
          <UIcon name="i-lucide-loader-2" class="h-4 w-4 animate-spin text-blue-500" />
          Mencari loker semantik...
        </span>
      </div>
      <!-- Skeleton Loaders -->
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div v-for="n in 4" :key="n" class="h-44 rounded-2xl bg-gray-200/60 dark:bg-gray-800/60 animate-pulse border border-gray-200/50 dark:border-gray-800/50" />
      </div>
    </section>

    <section v-else-if="results.length" class="flex flex-col gap-4">
      <!-- Result Stats Header -->
      <div class="flex items-center justify-between rounded-xl bg-white/70 dark:bg-gray-900/70 border border-gray-200/60 dark:border-gray-800/60 px-4 py-3 text-sm">
        <div class="flex items-center gap-2 font-semibold text-gray-700 dark:text-gray-200">
          <UIcon name="i-lucide-check-circle-2" class="h-4 w-4 text-emerald-500" />
          <span>Ditemukan <strong class="text-blue-600 dark:text-blue-400 font-extrabold">{{ results.length }}</strong> loker relevan</span>
        </div>
        <span class="text-xs text-gray-400 dark:text-gray-500 font-medium">
          Query: "{{ query }}"
        </span>
      </div>

      <!-- Job Cards Grid -->
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
        <JobCard v-for="job in results" :key="job.id" :job="job" />
      </div>
    </section>

    <!-- No Results State -->
    <div
      v-else-if="!loading && query && hasSearched && !error"
      class="flex flex-col items-center justify-center rounded-3xl border border-dashed border-gray-300 dark:border-gray-800 bg-white/50 dark:bg-gray-900/50 p-12 text-center backdrop-blur-md"
    >
      <div class="flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-50 dark:bg-amber-950/50 text-amber-500 mb-4 border border-amber-200/60 dark:border-amber-800/60">
        <UIcon name="i-lucide-search-x" class="h-8 w-8" />
      </div>
      <h3 class="text-lg font-bold text-gray-900 dark:text-white">Tidak ada loker ditemukan</h3>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400 max-w-md">
        Tidak ada hasil untuk kata kunci "{{ query }}". Coba ubah kata kunci atau perlebar rentang waktu di panel filter.
      </p>
    </div>

    <!-- Empty Initial State -->
    <div
      v-else-if="!loading && !hasSearched"
      class="flex flex-col items-center justify-center rounded-3xl border border-dashed border-gray-300/80 dark:border-gray-800/80 bg-white/40 dark:bg-gray-900/40 p-12 text-center backdrop-blur-md"
    >
      <div class="flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-50 dark:bg-blue-950/50 text-blue-500 mb-4 border border-blue-200/60 dark:border-blue-800/60">
        <UIcon name="i-lucide-sparkles" class="h-8 w-8" />
      </div>
      <h3 class="text-lg font-bold text-gray-900 dark:text-white">Mulai Pencarian Loker</h3>
      <p class="mt-1 text-sm text-gray-500 dark:text-gray-400 max-w-md">
        Ketik posisi atau skill di kolom pencarian di atas untuk menemukan lowongan kerja remote terbaik.
      </p>
    </div>
  </div>
</template>

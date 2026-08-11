<script setup lang="ts">
import type { SkillRank } from '~/types'

const api = useApi()

const days = ref(30)
const role = ref('')
const category = ref<string | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const skills = ref<SkillRank[]>([])
const nPostings = ref(0)

async function load() {
  loading.value = true
  error.value = null
  try {
    const data = await api.topSkills({
      days: days.value,
      role: role.value.trim() || undefined,
      category: category.value ?? undefined,
      limit: 20
    })
    skills.value = data.skills ?? []
    nPostings.value = data.n_postings ?? 0
  } catch (e: any) {
    error.value = e?.data?.detail ?? e?.message ?? 'Gagal mengambil data insight skill.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col gap-8">
    <!-- Hero Header -->
    <section class="flex flex-col items-center text-center gap-3 py-2">
      <div class="inline-flex items-center gap-2 rounded-full border border-indigo-500/20 bg-indigo-500/10 px-3.5 py-1 text-xs font-semibold text-indigo-600 dark:bg-indigo-400/10 dark:text-indigo-400">
        <UIcon name="i-lucide-trending-up" class="h-3.5 w-3.5" />
        <span>Market Intelligence &amp; Skill Demand Ranking</span>
      </div>

      <h1 class="text-3xl sm:text-4xl font-black tracking-tight text-gray-900 dark:text-white max-w-2xl leading-tight">
        Insight Skill Loker Remote IT
      </h1>

      <p class="text-sm sm:text-base text-gray-500 dark:text-gray-400 max-w-xl">
        Analisis ranking keahlian yang paling diminati perusahaan remote global berdasarkan data loker terkini.
      </p>

      <!-- Filter Controls -->
      <div class="w-full max-w-3xl mt-4 flex flex-col gap-3">
        <FilterPanel v-model:days="days" v-model:role="role" v-model:category="category" />
        <div class="flex justify-end">
          <UButton
            color="primary"
            size="lg"
            :loading="loading"
            class="rounded-xl px-6 font-semibold shadow-md shadow-blue-500/20 hover:scale-[1.02] active:scale-95 transition-all"
            @click="load"
          >
            <UIcon name="i-lucide-filter" class="h-4 w-4 mr-1.5" />
            <span>Terapkan Filter</span>
          </UButton>
        </div>
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

    <!-- Overview Stat Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div class="flex items-center gap-4 rounded-2xl border border-gray-200/80 bg-white/80 p-4 shadow-sm backdrop-blur-md dark:border-gray-800 dark:bg-gray-900/80">
        <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400 border border-blue-200/60 dark:border-blue-800/60">
          <UIcon name="i-lucide-briefcase" class="h-6 w-6" />
        </div>
        <div>
          <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">Total Loker Diinklusi</p>
          <p class="text-2xl font-black text-gray-900 dark:text-white font-mono">{{ nPostings }}</p>
        </div>
      </div>

      <div class="flex items-center gap-4 rounded-2xl border border-gray-200/80 bg-white/80 p-4 shadow-sm backdrop-blur-md dark:border-gray-800 dark:bg-gray-900/80">
        <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-400 border border-indigo-200/60 dark:border-indigo-800/60">
          <UIcon name="i-lucide-award" class="h-6 w-6" />
        </div>
        <div>
          <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">Skill #1 Paling Dicari</p>
          <p class="text-lg font-black text-gray-900 dark:text-white truncate max-w-[150px]">
            {{ skills[0]?.name ?? '-' }}
          </p>
        </div>
      </div>

      <div class="flex items-center gap-4 rounded-2xl border border-gray-200/80 bg-white/80 p-4 shadow-sm backdrop-blur-md dark:border-gray-800 dark:bg-gray-900/80">
        <div class="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-50 text-purple-600 dark:bg-purple-950/50 dark:text-purple-400 border border-purple-200/60 dark:border-purple-800/60">
          <UIcon name="i-lucide-clock" class="h-6 w-6" />
        </div>
        <div>
          <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">Rentang Waktu</p>
          <p class="text-lg font-black text-gray-900 dark:text-white font-mono">{{ days }} Hari Terakhir</p>
        </div>
      </div>
    </div>

    <!-- Chart Container -->
    <section class="rounded-3xl border border-gray-200/80 bg-white/90 p-6 shadow-sm backdrop-blur-md dark:border-gray-800 dark:bg-gray-900/90">
      <div class="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-gray-100 dark:border-gray-800 pb-4">
        <div>
          <h2 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <UIcon name="i-lucide-bar-chart-3" class="h-5 w-5 text-blue-500" />
            <span>Ranking Skill Terpopuler</span>
          </h2>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            Frekuensi kemunculan skill pada postingan loker remote
            <span v-if="role.trim()">, khusus untuk role <strong>"{{ role.trim() }}"</strong></span>.
          </p>
        </div>

        <div class="text-xs text-gray-400 dark:text-gray-500 font-medium">
          Klik nama skill untuk mencari loker terkait
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex flex-col gap-3 py-6">
        <div v-for="n in 6" :key="n" class="h-10 w-full rounded-xl bg-gray-100 dark:bg-gray-800/60 animate-pulse" />
      </div>

      <!-- Chart Content -->
      <SkillBarChart v-else :skills="skills" />
    </section>

    <!-- Context Note -->
    <div class="flex items-center gap-2.5 rounded-xl border border-blue-200/60 bg-blue-50/50 p-4 text-xs text-blue-700 dark:border-blue-900/40 dark:bg-blue-950/30 dark:text-blue-300">
      <UIcon name="i-lucide-info" class="h-4 w-4 shrink-0 text-blue-500" />
      <span>
        Catatan: Insight ini merepresentasikan demand remote-global (RemoteOK &amp; WeWorkRemotely), yang sangat berguna untuk acuan belajar skill remote berstandar internasional.
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { JobItem } from '~/types'

const route = useRoute()
const api = useApi()

const loading = ref(true)
const error = ref<string | null>(null)
const job = ref<JobItem | null>(null)
const bookmarked = ref(false)
const bookmarkBusy = ref(false)

async function load() {
  loading.value = true
  error.value = null
  try {
    job.value = await api.jobDetail(Number(route.params.id))
    const bm = await api.bookmarks()
    bookmarked.value = (bm.results ?? []).some((r: any) => r.id === Number(route.params.id))
  } catch (e: any) {
    error.value = e?.data?.detail ?? e?.message ?? 'Gagal memuat detail loker.'
  } finally {
    loading.value = false
  }
}

async function toggleBookmark() {
  if (!job.value || bookmarkBusy.value) return
  bookmarkBusy.value = true
  try {
    if (bookmarked.value) {
      await api.removeBookmark(job.value.id)
      bookmarked.value = false
    } else {
      await api.addBookmark(job.value.id)
      bookmarked.value = true
    }
  } catch (e: any) {
    error.value = e?.data?.detail ?? e?.message ?? 'Gagal menyimpan loker.'
  } finally {
    bookmarkBusy.value = false
  }
}

onMounted(load)

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'tanggal tidak diketahui'
  const d = new Date(dateStr)
  const days = Math.floor((Date.now() - d.getTime()) / 86400000)
  if (days <= 0) return 'hari ini'
  if (days === 1) return 'kemarin'
  return `${days} hari lalu`
}

function levelLabel(level?: string): string {
  switch (level) {
    case 'junior': return 'Junior'
    case 'mid': return 'Mid-Level'
    case 'senior': return 'Senior'
    default: return 'Tidak disebutkan'
  }
}

function empTypeLabel(type?: string): string {
  switch (type) {
    case 'remote': return 'Remote'
    case 'onsite': return 'Onsite'
    case 'hybrid': return 'Hybrid'
    default: return 'Tidak disebutkan'
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <!-- Back link -->
    <NuxtLink to="/" class="flex items-center gap-1 text-sm font-medium text-gray-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors w-fit">
      <UIcon name="i-lucide-arrow-left" class="h-4 w-4" />
      Kembali ke hasil pencarian
    </NuxtLink>

    <div v-if="loading" class="flex flex-col gap-4">
      <div class="h-8 w-2/3 rounded-xl bg-gray-200/60 dark:bg-gray-800/60 animate-pulse" />
      <div class="h-5 w-1/3 rounded-xl bg-gray-200/60 dark:bg-gray-800/60 animate-pulse" />
      <div class="h-64 w-full rounded-2xl bg-gray-200/60 dark:bg-gray-800/60 animate-pulse" />
    </div>

    <div v-else-if="error" class="rounded-2xl border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/50 dark:text-rose-300">
      {{ error }}
    </div>

    <template v-else-if="job">
      <!-- Header Card -->
      <section class="rounded-3xl border border-gray-200/80 bg-white/90 p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900/90">
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <h1 class="text-2xl font-black tracking-tight text-gray-900 dark:text-white">
              {{ job.title }}
            </h1>
            <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-gray-500 dark:text-gray-400">
              <span class="font-semibold text-gray-700 dark:text-gray-300">{{ job.company ?? 'Perusahaan Rahasia' }}</span>
              <span v-if="job.location" class="flex items-center gap-1">
                <UIcon name="i-lucide-map-pin" class="h-3.5 w-3.5" />{{ job.location }}
              </span>
              <span>{{ timeAgo(job.posted_date) }}</span>
              <span
                class="rounded-full px-2.5 py-0.5 text-[11px] font-bold uppercase border"
                :class="job.source === 'remoteok'
                  ? 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/50 dark:text-rose-300 dark:border-rose-800'
                  : 'bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950/50 dark:text-indigo-300 dark:border-indigo-800'"
              >
                {{ job.source === 'remoteok' ? 'RemoteOK' : 'WeWorkRemotely' }}
              </span>
            </div>

            <div class="mt-3 flex flex-wrap gap-2 text-xs">
              <span v-if="levelLabel(job.experience_level)" class="rounded-lg bg-blue-50 px-2.5 py-1 font-semibold text-blue-700 dark:bg-blue-950/50 dark:text-blue-300 border border-blue-200/60 dark:border-blue-800/60">
                {{ levelLabel(job.experience_level) }}
              </span>
              <span v-if="empTypeLabel(job.employment_type)" class="rounded-lg bg-emerald-50 px-2.5 py-1 font-semibold text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800/60">
                {{ empTypeLabel(job.employment_type) }}
              </span>
              <span v-if="job.min_years_experience" class="rounded-lg bg-purple-50 px-2.5 py-1 font-semibold text-purple-700 dark:bg-purple-950/50 dark:text-purple-300 border border-purple-200/60 dark:border-purple-800/60">
                {{ job.min_years_experience }}+ tahun pengalaman
              </span>
            </div>
          </div>

          <div class="flex gap-2">
            <UButton
              :color="bookmarked ? 'amber' : 'neutral'"
              variant="outline"
              size="lg"
              class="shrink-0 rounded-xl px-5 font-semibold"
              :loading="bookmarkBusy"
              @click="toggleBookmark"
            >
              <UIcon :name="bookmarked ? 'i-lucide-bookmark' : 'i-lucide-bookmark-plus'" class="h-4 w-4 mr-1" />
              <span>{{ bookmarked ? 'Tersimpan' : 'Simpan' }}</span>
            </UButton>
            <UButton
              :to="job.source_url"
              target="_blank"
              rel="noopener"
              color="primary"
              size="lg"
              class="shrink-0 rounded-xl px-6 font-semibold shadow-md shadow-blue-500/20"
            >
              <span>Lamar Sekarang</span>
              <UIcon name="i-lucide-external-link" class="h-4 w-4 ml-1" />
            </UButton>
          </div>
        </div>
      </section>

      <!-- Requirements Grid -->
      <section v-if="job.tools?.length || job.hard_skills?.length || job.soft_skills?.length" class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="rounded-2xl border border-gray-200/80 bg-white/80 p-4 dark:border-gray-800 dark:bg-gray-900/80">
          <h3 class="text-xs font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">Tools & Teknologi</h3>
          <div class="flex flex-wrap gap-1.5">
            <span v-for="s in job.tools" :key="s" class="rounded-lg bg-blue-50/80 px-2.5 py-1 text-xs font-semibold text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 border border-blue-200/50 dark:border-blue-800/40">
              {{ s }}
            </span>
          </div>
        </div>

        <div class="rounded-2xl border border-gray-200/80 bg-white/80 p-4 dark:border-gray-800 dark:bg-gray-900/80">
          <h3 class="text-xs font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">Hard Skills</h3>
          <div class="flex flex-wrap gap-1.5">
            <span v-for="s in job.hard_skills" :key="s" class="rounded-lg bg-indigo-50/80 px-2.5 py-1 text-xs font-semibold text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300 border border-indigo-200/50 dark:border-indigo-800/40">
              {{ s }}
            </span>
          </div>
        </div>

        <div class="rounded-2xl border border-gray-200/80 bg-white/80 p-4 dark:border-gray-800 dark:bg-gray-900/80">
          <h3 class="text-xs font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">Soft Skills</h3>
          <div class="flex flex-wrap gap-1.5">
            <span v-for="s in job.soft_skills" :key="s" class="rounded-lg bg-emerald-50/80 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300 border border-emerald-200/50 dark:border-emerald-800/40">
              {{ s }}
            </span>
          </div>
        </div>
      </section>

      <!-- Full Description -->
      <section class="rounded-3xl border border-gray-200/80 bg-white/90 p-6 shadow-sm dark:border-gray-800 dark:bg-gray-900/90">
        <h2 class="mb-4 text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <UIcon name="i-lucide-file-text" class="h-4 w-4 text-blue-500" />
          Deskripsi Pekerjaan
        </h2>
        <div v-if="job.description" class="prose prose-sm max-w-none text-sm leading-relaxed text-gray-600 dark:text-gray-300 prose-headings:text-gray-900 dark:prose-headings:text-white prose-strong:text-gray-900 dark:prose-strong:text-white prose-li:my-0.5">
          <p class="whitespace-pre-wrap">{{ job.description }}</p>
        </div>
        <p v-else class="text-sm text-gray-400">Deskripsi tidak tersedia untuk loker ini.</p>
      </section>
    </template>
  </div>
</template>

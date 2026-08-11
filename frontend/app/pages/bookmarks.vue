<script setup lang="ts">
import type { JobItem } from '~/types'

const api = useApi()

const loading = ref(true)
const error = ref<string | null>(null)
const bookmarks = ref<JobItem[]>([])

async function load() {
  loading.value = true
  error.value = null
  try {
    const data = await api.bookmarks()
    bookmarks.value = data.results ?? []
  } catch (e: any) {
    error.value = e?.data?.detail ?? e?.message ?? 'Gagal memuat bookmark.'
  } finally {
    loading.value = false
  }
}

async function removeJob(id: number) {
  await api.removeBookmark(id)
  bookmarks.value = bookmarks.value.filter((j) => j.id !== id)
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
</script>

<template>
  <div class="flex flex-col gap-6">
    <section class="flex flex-col gap-2">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
        <UIcon name="i-lucide-bookmark" class="h-5 w-5 text-amber-500" />
        Loker Tersimpan
      </h1>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Daftar loker yang Anda simpan untuk dilamar nanti.
      </p>
    </section>

    <p v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50/80 p-4 text-sm text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/50 dark:text-rose-300">
      {{ error }}
    </p>

    <section v-if="loading" class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div v-for="n in 4" :key="n" class="h-40 rounded-2xl bg-gray-200/60 dark:bg-gray-800/60 animate-pulse" />
    </section>

    <section v-else-if="bookmarks.length" class="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div
        v-for="job in bookmarks"
        :key="job.id"
        class="group flex flex-col gap-3 rounded-2xl border border-gray-200/80 bg-white p-5 shadow-sm hover:shadow-xl hover:border-blue-500/30 dark:border-gray-800 dark:bg-gray-900 dark:hover:border-blue-500/40 transition-all duration-300"
      >
        <div>
          <NuxtLink
            :to="`/jobs/${job.id}`"
            class="line-clamp-2 font-bold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors"
          >
            {{ job.title }}
          </NuxtLink>
          <p class="mt-1 text-xs text-gray-500 dark:text-gray-400 font-medium">
            {{ job.company ?? 'Perusahaan Rahasia' }}
            <span v-if="job.location"> · {{ job.location }}</span>
            <span> · {{ timeAgo(job.posted_date) }}</span>
          </p>
        </div>

        <p v-if="job.description" class="line-clamp-2 text-xs text-gray-500 dark:text-gray-400">
          {{ job.description.replace(/\s+/g, ' ').slice(0, 180) }}…
        </p>

        <div class="pt-2 border-t border-gray-100 dark:border-gray-800/60 flex items-center justify-between">
          <span
            class="rounded-full px-2.5 py-1 text-[11px] font-bold uppercase border"
            :class="job.source === 'remoteok'
              ? 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/50 dark:text-rose-300 dark:border-rose-800'
              : job.source === 'adzuna'
                ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:border-amber-800'
                : 'bg-indigo-50 text-indigo-700 border-indigo-200 dark:bg-indigo-950/50 dark:text-indigo-300 dark:border-indigo-800'"
          >
            {{ job.source }}
          </span>
          <div class="flex gap-2">
            <UButton :to="`/jobs/${job.id}`" size="xs" color="primary" variant="soft" class="rounded-lg">
              Detail
            </UButton>
            <UButton size="xs" color="red" variant="ghost" class="rounded-lg" @click="removeJob(job.id)">
              Hapus
            </UButton>
          </div>
        </div>
      </div>
    </section>

    <section v-else class="rounded-3xl border border-dashed border-gray-300 dark:border-gray-800 bg-white/40 dark:bg-gray-900/40 p-12 text-center">
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Belum ada loker tersimpan. Buka detail loker lalu klik "Simpan".
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import type { SkillRank } from '~/components/SkillBarChart.vue'

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
    error.value = e?.data?.detail ?? e?.message ?? 'Gagal mengambil data insight.'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col gap-6">
    <section class="flex flex-col gap-3">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
        Insight Skill
      </h1>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Ranking skill yang paling sering diminta di loker-loker terkini.
      </p>
      <FilterPanel v-model="days" v-model:role="role" v-model:category="category" />
      <UButton color="primary" :loading="loading" @click="load">
        Terapkan Filter
      </UButton>
    </section>

    <p v-if="error" class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600 dark:border-red-800 dark:bg-red-950 dark:text-red-300">
      {{ error }}
    </p>

    <section v-if="!loading" class="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-900">
      <p class="mb-4 text-xs font-medium text-gray-500 dark:text-gray-400">
        Berdasarkan <strong>{{ nPostings }}</strong> loker, {{ days }} hari terakhir
        <span v-if="role.trim()">, role "{{ role.trim() }}"</span>
      </p>
      <SkillBarChart :skills="skills" />
    </section>

    <p class="text-xs text-gray-400 dark:text-gray-500">
      Catatan: Insight ini merepresentasikan demand remote-global (RemoteOK, WeWorkRemotely), bukan pasar lokal Indonesia.
    </p>
  </div>
</template>

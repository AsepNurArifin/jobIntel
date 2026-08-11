<script setup lang="ts">
const props = defineProps<{
  initialQuery?: string
}>()

const emit = defineEmits<{
  search: [query: string]
}>()

const query = ref(props.initialQuery ?? '')

const QUICK_TAGS = [
  'Data Scientist',
  'Backend Python',
  'Fullstack React',
  'DevOps',
  'Machine Learning',
  'Golang'
]

watch(() => props.initialQuery, (newVal) => {
  if (newVal !== undefined) {
    query.value = newVal
  }
})

function onSubmit() {
  if (query.value.trim()) {
    emit('search', query.value.trim())
  }
}

function selectTag(tag: string) {
  query.value = tag
  emit('search', tag)
}

function clearQuery() {
  query.value = ''
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <form class="group relative flex items-center gap-2 rounded-2xl bg-white p-2 shadow-lg shadow-gray-200/50 dark:bg-gray-900 dark:shadow-none border border-gray-200/80 dark:border-gray-800 transition-all focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/10" @submit.prevent="onSubmit">
      <div class="pl-3 text-gray-400 dark:text-gray-500 flex items-center">
        <UIcon name="i-lucide-search" class="h-5 w-5" />
      </div>
      <input
        v-model="query"
        type="text"
        name="query"
        placeholder='Cari loker (mis. "data scientist", "backend python", "fullstack")'
        class="w-full bg-transparent py-2.5 px-2 text-sm sm:text-base text-gray-900 placeholder-gray-400 focus:outline-none dark:text-white dark:placeholder-gray-500 font-medium"
        @keyup.enter="onSubmit"
      >
      
      <button
        v-if="query"
        type="button"
        class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors rounded-lg"
        title="Bersihkan"
        @click="clearQuery"
      >
        <UIcon name="i-lucide-x" class="h-4 w-4" />
      </button>

      <UButton
        size="lg"
        type="submit"
        color="primary"
        class="shrink-0 rounded-xl px-5 font-semibold shadow-md shadow-blue-500/20 hover:scale-[1.02] active:scale-95 transition-all"
      >
        <span>Cari Loker</span>
      </UButton>
    </form>

    <!-- Quick Search Suggestions -->
    <div class="flex flex-wrap items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 px-1">
      <span class="font-medium text-gray-400 dark:text-gray-500 flex items-center gap-1">
        Pencarian Populer:
      </span>
      <button
        v-for="tag in QUICK_TAGS"
        :key="tag"
        type="button"
        class="rounded-lg bg-gray-100 dark:bg-gray-800/80 px-2.5 py-1 font-medium text-gray-600 dark:text-gray-300 hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-blue-950/50 dark:hover:text-blue-400 border border-gray-200/50 dark:border-gray-700/50 transition-all cursor-pointer"
        @click="selectTag(tag)"
      >
        {{ tag }}
      </button>
    </div>
  </div>
</template>

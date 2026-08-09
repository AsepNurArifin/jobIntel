<script setup lang="ts">
const props = defineProps<{
  initialQuery?: string
}>()

const emit = defineEmits<{
  search: [query: string]
}>()

const query = ref(props.initialQuery ?? '')

function onSubmit() {
  if (query.value.trim()) {
    emit('search', query.value.trim())
  }
}
</script>

<template>
  <form class="flex gap-2" @submit.prevent="onSubmit">
    <UInput
      v-model="query"
      name="query"
      size="xl"
      placeholder='Contoh: "data scientist", "backend python", "ml engineer"'
      class="flex-1"
      @keyup.enter="onSubmit"
    />
    <UButton size="xl" type="submit" color="primary">
      Cari
    </UButton>
  </form>
</template>

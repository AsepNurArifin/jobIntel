<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-950">
    <header class="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
      <nav class="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <NuxtLink to="/" class="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-white">
          <span class="text-primary">⌘</span> JobIntel
        </NuxtLink>
        <div class="flex items-center gap-1">
          <NuxtLink
            to="/"
            class="rounded-md px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            Cari Loker
          </NuxtLink>
          <NuxtLink
            to="/insight"
            class="rounded-md px-3 py-1.5 text-sm font-medium text-gray-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            Insight Skill
          </NuxtLink>
        </div>
      </nav>
    </header>

    <main class="mx-auto max-w-5xl px-4 py-6">
      <NuxtPage />
    </main>
  </div>
</template>

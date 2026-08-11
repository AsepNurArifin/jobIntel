<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 dark:bg-gray-950 dark:text-gray-100 antialiased selection:bg-blue-500 selection:text-white">
    <header class="sticky top-0 z-50 border-b border-gray-200/80 dark:border-gray-800/80 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md">
      <nav class="mx-auto flex max-w-5xl items-center justify-between px-4 py-3.5">
        <NuxtLink to="/" class="flex items-center gap-2 text-lg font-bold tracking-tight text-gray-900 dark:text-white hover:opacity-90 transition-opacity">
          <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white font-mono text-sm font-black shadow-sm">
            ⌘
          </div>
          <span>JobIntel</span>
        </NuxtLink>
        <div class="flex items-center gap-1.5 bg-gray-100/80 dark:bg-gray-800/80 p-1 rounded-xl border border-gray-200/50 dark:border-gray-700/50">
          <NuxtLink
            to="/"
            exact-active-class="bg-white dark:bg-gray-900 text-blue-600 dark:text-blue-400 shadow-xs font-semibold"
            class="rounded-lg px-3.5 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-all"
          >
            Cari Loker
          </NuxtLink>
          <NuxtLink
            to="/insight"
            exact-active-class="bg-white dark:bg-gray-900 text-blue-600 dark:text-blue-400 shadow-xs font-semibold"
            class="rounded-lg px-3.5 py-1.5 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-all"
          >
            Insight Skill
          </NuxtLink>
        </div>
      </nav>
    </header>

    <main class="mx-auto max-w-5xl px-4 py-8">
      <NuxtPage />
    </main>
  </div>
</template>


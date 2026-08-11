<template>
  <div class="relative min-h-screen bg-gray-50/50 text-gray-900 dark:bg-gray-950 dark:text-gray-100 antialiased selection:bg-blue-500 selection:text-white transition-colors duration-300">
    <!-- Ambient Background Glow Accents -->
    <div class="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      <div class="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-blue-500/10 blur-3xl dark:bg-blue-600/15" />
      <div class="absolute top-1/3 -right-40 h-96 w-96 rounded-full bg-indigo-500/10 blur-3xl dark:bg-indigo-600/15" />
      <div class="absolute bottom-10 left-1/4 h-96 w-96 rounded-full bg-sky-500/10 blur-3xl dark:bg-sky-600/10" />
    </div>

    <!-- Header Navigation -->
    <header class="sticky top-0 z-50 border-b border-gray-200/60 dark:border-gray-800/60 bg-white/75 dark:bg-gray-900/75 backdrop-blur-xl transition-all">
      <nav class="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <NuxtLink to="/" class="group flex items-center gap-2.5 text-lg font-extrabold tracking-tight text-gray-900 dark:text-white transition-all">
          <div class="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white font-mono text-sm font-black shadow-md shadow-blue-500/25 group-hover:scale-105 transition-transform">
            ⌘
          </div>
          <div class="flex flex-col">
            <span class="flex items-center gap-1.5 leading-tight font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-gray-900 via-blue-900 to-indigo-900 dark:from-white dark:via-blue-100 dark:to-indigo-200">
              JobIntel
              <span class="rounded-full bg-blue-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-blue-600 dark:bg-blue-400/10 dark:text-blue-400 border border-blue-500/20">AI</span>
            </span>
            <span class="text-[10px] font-medium text-gray-400 dark:text-gray-500 leading-none">Remote Career Engine</span>
          </div>
        </NuxtLink>

        <!-- Right Side Nav Items -->
        <div class="flex items-center gap-3">
          <div class="flex items-center gap-1 bg-gray-100/90 dark:bg-gray-800/80 p-1 rounded-xl border border-gray-200/60 dark:border-gray-700/60 backdrop-blur-sm">
            <NuxtLink
              to="/"
              exact-active-class="bg-white dark:bg-gray-900 text-blue-600 dark:text-blue-400 shadow-sm font-semibold"
              class="flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs sm:text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-all"
            >
              <UIcon name="i-lucide-search" class="h-4 w-4" />
              <span>Cari Loker</span>
            </NuxtLink>
            <NuxtLink
              to="/insight"
              exact-active-class="bg-white dark:bg-gray-900 text-blue-600 dark:text-blue-400 shadow-sm font-semibold"
              class="flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs sm:text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-white transition-all"
            >
              <span>Insight Skill</span>
            </NuxtLink>
          </div>
        </div>
      </nav>
    </header>

    <!-- Main Content -->
    <main class="relative z-10 mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <NuxtPage />
    </main>

    <!-- Footer -->
    <footer class="relative z-10 border-t border-gray-200/60 dark:border-gray-800/60 bg-white/40 dark:bg-gray-900/40 backdrop-blur-md py-6 mt-16">
      <div class="mx-auto max-w-6xl px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gray-500 dark:text-gray-400">
        <div class="flex items-center gap-2">
          <span class="font-semibold text-gray-700 dark:text-gray-300">JobIntel AI</span>
          <span>·</span>
          <span>Engine Pencari Loker Semantik RemoteOK &amp; WeWorkRemotely</span>
        </div>
        <div class="flex items-center gap-2">
          <span class="flex items-center gap-1">
            <span class="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            Backend Online
          </span>
        </div>
      </div>
    </footer>
  </div>
</template>


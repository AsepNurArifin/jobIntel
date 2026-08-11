export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  css: ['~/assets/css/main.css'],

  modules: [
    '@nuxt/ui'
  ],

  runtimeConfig: {
    public: {
      apiBaseUrl: 'http://localhost:8000'
    }
  }
})


export default defineNuxtConfig({
  compatibilityDate: '2025-05-06',
  modules: ['@pinia/nuxt', '@nuxthub/core'],
  css: ['~/assets/style.css'],
  debug: true,
  app: {
    head: {
      title: 'Laptop Recommendation Chatbot',
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' }
      ],
      script: [
        { src: 'https://unpkg.com/ionicons@7.1.0/dist/ionicons/ionicons.esm.js', type: 'module' },
        { src: 'https://unpkg.com/ionicons@7.1.0/dist/ionicons/ionicons.js', nomodule: true }
      ]
    }
  }
})
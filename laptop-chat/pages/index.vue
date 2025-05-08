<template>
  <div>
    <ThemeToggle />
    <Sidebar />

    <div class="splash-container" v-if="showSplash">
      <div class="splash-content">
        <h1>Welcome to LaptopAdvisor</h1>
        <div class="laptop-icon">💻</div>
        <p>Your AI-powered assistant for finding the perfect laptop.</p>
        <p class="splash-description">I can help you discover the best laptop options based on your specific needs, budget, and preferences. Whether you're a gamer, student, professional, or casual user, I've got recommendations just for you.</p>
        <button @click="$router.push('/chat')" class="start-chat-btn">Start Chat</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import ThemeToggle from '~/components/ThemeToggle.vue';
import Sidebar from '~/components/Sidebar.vue';
const showSplash = ref(true);
</script>
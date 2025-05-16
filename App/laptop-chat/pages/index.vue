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
        <button @click="startChat" class="start-chat-btn">Start Chat</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import ThemeToggle from '~/components/ThemeToggle.vue';
import Sidebar from '~/components/Sidebar.vue';
import { useUserStore } from '~/store/user';

const showSplash = ref(true);
const userStore = useUserStore();

// Check for authentication when app loads
onMounted(async () => {
  await userStore.checkAuth();
});

// Verify login status before starting chat
function startChat() {
  if (userStore.isLoggedIn) {
    navigateTo('/chat');
  } else {
    navigateTo('/profile');
  }
}
</script>
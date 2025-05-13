<template>
  <div>
    <button class="sidebar-toggle" @click="openSidebar">☰</button>
    <div class="overlay" :class="{ active: isOpen }" @click="closeSidebar"></div>
    <div class="sidebar" :class="{ open: isOpen }">
      <div class="sidebar-header">
        LaptopAdvisor Menu
        <button class="sidebar-close" @click="closeSidebar">×</button>
      </div>
      <div class="sidebar-content">
        <ul class="sidebar-nav">
          <li @click="$router.push('/')">Home</li>
          <li @click="$router.push('/profile')">Profile </li>
          <li @click="$router.push('/pastrecs')">Past Recommendations</li>
          <li @click="$router.push('/search')">Laptop Search</li>
          <li @click="$router.push('/about')">About</li>        </ul>
        <div style="margin-top: 30px;">
          <p>Need help finding your perfect laptop?</p>
          <p style="margin-top: 10px; color: var(--text-color-light);">Use our AI-powered chat assistant to get personalized recommendations based on your needs.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const isOpen = ref(false);

function openSidebar() {
  isOpen.value = true;
}

function closeSidebar() {
  isOpen.value = false;
}
</script>
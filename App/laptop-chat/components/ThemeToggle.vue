<template>
  <div class="fixed-theme-toggle">
    <div class="theme-toggle">
      <input type="checkbox" id="theme-toggle-checkbox" v-model="isDarkMode" class="theme-toggle-checkbox">
      <label for="theme-toggle-checkbox" class="theme-toggle-label">
        <span class="theme-toggle-icons">
          <span class="sun">☀️</span>
          <span class="moon">🌙</span>
        </span>
      </label>
    </div>
  </div>
</template>

<script setup>
const isDarkMode = ref(false);

watch(isDarkMode, (newValue) => {
  document.body.classList.toggle('dark-theme', newValue);
});
</script>
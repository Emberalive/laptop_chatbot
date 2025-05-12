<script setup lang="ts">
import { ref } from 'vue';

// Search state
const searchTerm = ref('');
const isSearching = ref(false);
const searchResults = ref([]);
const selectedLaptop = ref(null);
const errorMessage = ref('');

// Search for laptops by name
async function searchLaptops() {
  if (!searchTerm.value.trim()) {
    errorMessage.value = 'Please enter a laptop name';
    return;
  }

  try {
    isSearching.value = true;
    errorMessage.value = '';
    searchResults.value = [];
    selectedLaptop.value = null;

    const response = await $fetch('/api/search-laptops', {
      method: 'POST',
      body: JSON.stringify({ searchTerm: searchTerm.value }),
      headers: { 'Content-Type': 'application/json' }
    });

    if (response.results && response.results.length > 0) {
      searchResults.value = response.results;
    } else {
      errorMessage.value = 'No laptops found matching your search';
    }
  } catch (error) {
    console.error('Error searching laptops:', error);
    errorMessage.value = 'An error occurred while searching';
  } finally {
    isSearching.value = false;
  }
}

// Fetch laptop details using model_id
async function getLaptopDetails(modelId) {
  try {
    isSearching.value = true;

    const response = await $fetch('/api/laptop-details', {
      method: 'POST',
      body: JSON.stringify({ modelId }),
      headers: { 'Content-Type': 'application/json' }
    });

    if (response.details) {
      selectedLaptop.value = response.details;
    } else {
      errorMessage.value = 'Could not retrieve laptop details';
    }
  } catch (error) {
    console.error('Error fetching laptop details:', error);
    errorMessage.value = 'An error occurred while fetching laptop details';
  } finally {
    isSearching.value = false;
  }
}
</script>
<template>
  <div>
    <ThemeToggle />
    <Sidebar />

    <div class="search-container">
      <div class="search-header">
        <h1>Laptop Search</h1>
        <p>Find detailed information about specific laptop models</p>
      </div>

      <div class="search-form">
        <div class="search-input-container">
          <input
              type="text"
              v-model="searchTerm"
              placeholder="Enter laptop name or model"
              @keyup.enter="searchLaptops"
              class="search-input"
          />
          <button
              @click="searchLaptops"
              class="search-button"
              :disabled="isSearching"
          >
            {{ isSearching ? 'Searching...' : 'Search' }}
          </button>
        </div>

        <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
      </div>

      <div class="search-results-layout">
        <div class="search-results-column" :class="{ 'with-details': selectedLaptop }">
          <div v-if="searchResults.length >= 6">
            <h2>{{ searchResults.length }} Results Found</h2>
            <h2> Please be more specfic </h2>
          </div>
          <div v-if="searchResults.length > 0" class="search-results">
            <h2>Search Results</h2>
            <div class="results-list">
              <div
                  v-for="laptop in searchResults"
                  :key="laptop.model_id"
                  class="laptop-result-item"
                  @click="getLaptopDetails(laptop.model_id)"
              >
                <h3>{{ laptop.model_name }}</h3>
                <p>{{ laptop.brand }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-if="selectedLaptop" class="laptop-details-column">
          <div class="laptop-details">
            <h2>{{ selectedLaptop.model_name }}</h2>
            <img :src="selectedLaptop.image_url" alt="Laptop Image" class="laptop-image" />
            <div class="details-container">
              <div class="detail-section">
                <h3>Specifications</h3>
                <ul class="spec-list">
                  <li><strong>Brand:</strong> {{ selectedLaptop.brand }}</li>
                  <li><strong>Processor:</strong> {{ selectedLaptop.processor }}</li>
                  <li><strong>RAM:</strong> {{ selectedLaptop.ram }}</li>
                  <li><strong>Storage:</strong> {{ selectedLaptop.storage }}</li>
                  <li><strong>Display:</strong> {{ selectedLaptop.display_size }} {{ selectedLaptop.display_resolution }}</li>
                  <li><strong>Graphics:</strong> {{ selectedLaptop.graphics }}</li>
                </ul>
              </div>

              <div class="detail-section">
                <h3>Additional Information</h3>
                <ul class="spec-list">
                  <li><strong>Weight:</strong> {{ selectedLaptop.weight }} kg</li>
                  <li><strong>Battery Life:</strong> {{ selectedLaptop.battery_life }} hours</li>
                  <li v-if="selectedLaptop.price"><strong>Price:</strong> ${{ selectedLaptop.price }}</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
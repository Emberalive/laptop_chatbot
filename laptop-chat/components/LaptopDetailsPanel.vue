<!-- components/LaptopDetailsPanel.vue -->
<template>
  <div class="laptop-details-panel" :class="{ 'open': isOpen, 'comparison-mode': isComparisonMode }">
    <div class="laptop-details-header">
      <button class="laptop-details-close" @click="close">×</button>
      <h2>{{ title }}</h2>
    </div>
    <div class="laptop-details-content">
      <div v-if="isComparisonMode" class="comparison-container">
        <div v-for="(laptop, index) in comparisonLaptops" :key="index" class="laptop-column">
          <h3>{{ laptop.brand }} {{ laptop.name }}</h3>
          <div class="laptop-image-container">
            <div class="placeholder-image">{{ laptop.brand }}</div>
          </div>
          <!-- Ordered specs for comparison view -->
          <div class="laptop-spec">
            <div class="laptop-spec-label">CPU</div>
            <div class="laptop-spec-value">{{ getOrderedSpecs(laptop).cpu }}</div>
          </div>
          <div class="laptop-spec">
            <div class="laptop-spec-label">RAM</div>
            <div class="laptop-spec-value">{{ getOrderedSpecs(laptop).ram }}</div>
          </div>
          <div class="laptop-spec">
            <div class="laptop-spec-label">Storage</div>
            <div class="laptop-spec-value">{{ getOrderedSpecs(laptop).storage }}</div>
          </div>
          <div class="laptop-spec">
            <div class="laptop-spec-label">Screen</div>
            <div class="laptop-spec-value">{{ getOrderedSpecs(laptop).screen }}</div>
          </div>
          <div class="laptop-spec">
            <div class="laptop-spec-label">GPU</div>
            <div class="laptop-spec-value">{{ getOrderedSpecs(laptop).gpu }}</div>
          </div>
          <!-- Additional specs if available -->
          <div v-if="laptop.price" class="laptop-spec">
            <div class="laptop-spec-label">Price</div>
            <div class="laptop-spec-value">{{ laptop.price }}</div>
          </div>
          <div v-if="laptop.features" class="laptop-spec">
            <div class="laptop-spec-label">Features</div>
            <div class="laptop-spec-value">{{ laptop.features }}</div>
          </div>
        </div>
      </div>
      <div v-else>
        <div class="laptop-image-container">
          <div class="placeholder-image">{{ selectedLaptop?.brand || 'Laptop' }}</div>
        </div>
        <!-- Ordered specs for single laptop view -->
        <div class="laptop-spec">
          <div class="laptop-spec-label">CPU</div>
          <div class="laptop-spec-value">{{ getOrderedSpecs(selectedLaptop).cpu }}</div>
        </div>
        <div class="laptop-spec">
          <div class="laptop-spec-label">RAM</div>
          <div class="laptop-spec-value">{{ getOrderedSpecs(selectedLaptop).ram }}</div>
        </div>
        <div class="laptop-spec">
          <div class="laptop-spec-label">Storage</div>
          <div class="laptop-spec-value">{{ getOrderedSpecs(selectedLaptop).storage }}</div>
        </div>
        <div class="laptop-spec">
          <div class="laptop-spec-label">Screen</div>
          <div class="laptop-spec-value">{{ getOrderedSpecs(selectedLaptop).screen }}</div>
        </div>
        <div class="laptop-spec">
          <div class="laptop-spec-label">GPU</div>
          <div class="laptop-spec-value">{{ getOrderedSpecs(selectedLaptop).gpu }}</div>
        </div>
        <!-- Additional specs if available -->
        <div v-if="selectedLaptop?.price" class="laptop-spec">
          <div class="laptop-spec-label">Price</div>
          <div class="laptop-spec-value">{{ selectedLaptop.price }}</div>
        </div>
        <div v-if="selectedLaptop?.features" class="laptop-spec">
          <div class="laptop-spec-label">Features</div>
          <div class="laptop-spec-value">{{ selectedLaptop.features }}</div>
        </div>
        <button class="compare-btn" @click="toggleComparisonSelection">Compare with another laptop</button>
      </div>
      <button v-if="isComparisonMode" class="exit-comparison-btn" @click="exitComparisonMode">
        Exit Comparison
      </button>
    </div>
  </div>
  <div v-if="showComparisonModal" class="comparison-modal">
    <div class="comparison-modal-content">
      <div class="comparison-modal-header">
        <h3>Select a laptop to compare</h3>
        <button class="close-modal-btn" @click="showComparisonModal = false">×</button>
      </div>
      <div class="comparison-modal-body">
        <div v-if="availableLaptops.length === 0" class="no-laptops-message">
          No recommended laptops available for comparison.
        </div>
        <div v-else class="laptop-selection-list">
          <div
              v-for="(laptop, index) in availableLaptops"
              :key="index"
              class="laptop-selection-item"
              @click="selectLaptopForComparison(laptop)"
          >
            <h4>{{ laptop.brand }} {{ laptop.name }}</h4>
            <div class="laptop-specs-preview">
              <span v-if="laptop.price">{{ laptop.price }}</span>
              <span v-if="laptop.processor">{{ laptop.processor.substring(0, 20) }}...</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useChatStore } from '~/store/chat';

const props = defineProps({
  isOpen: Boolean,
});

const emit = defineEmits(['close', 'comparison-mode-change']);

const chatStore = useChatStore();
const selectedLaptop = ref(null);
const isComparisonMode = ref(false);
const comparisonLaptops = ref([]);
const showComparisonModal = ref(false);
const availableLaptops = ref([]);

const title = computed(() => {
  if (isComparisonMode.value) {
    return 'Laptop Comparison';
  }
  return selectedLaptop.value ? `${selectedLaptop.value.brand} ${selectedLaptop.value.name}` : 'Laptop Details';
});

function showLaptopDetails(laptop, addToComparison = false) {
  if (addToComparison) {
    if (!comparisonLaptops.value.length) {
      comparisonLaptops.value.push(selectedLaptop.value);
    }
    comparisonLaptops.value.push(laptop);
    isComparisonMode.value = true;
    emit('comparison-mode-change', true);
  } else {
    selectedLaptop.value = laptop;
    comparisonLaptops.value = [laptop];
    isComparisonMode.value = false;
    emit('comparison-mode-change', false);
  }
}

function close() {
  emit('close');
}

function exitComparisonMode() {
  // Save the current laptop before clearing comparison mode
  const currentLaptop = comparisonLaptops.value.length > 0 ? comparisonLaptops.value[0] : null;

  // Clear comparison mode
  isComparisonMode.value = false;

  // Reset comparison laptops array
  comparisonLaptops.value = [];

  // Keep only the first laptop as the selected one
  if (currentLaptop) {
    selectedLaptop.value = currentLaptop;
    comparisonLaptops.value = [currentLaptop];
  }

  // Notify parent component
  emit('comparison-mode-change', false);
}

function toggleComparisonSelection() {
  // Get all recommended laptops from the chat store
  const allLaptops = chatStore.allRecommendations || [];

  const uniqueLaptops = [];
  const seen = new Set();

  allLaptops.forEach(laptop => {
    const key = `${laptop.brand}-${laptop.name}`;
    if (!seen.has(key)) {
      seen.add(key);
      uniqueLaptops.push(laptop);
    }
  });

  // Filter out the currently selected laptop
  availableLaptops.value = uniqueLaptops.filter(laptop => {
    if (!selectedLaptop.value) return true;

    return !(laptop.brand === selectedLaptop.value.brand &&
        laptop.name === selectedLaptop.value.name);
  });

  showComparisonModal.value = true;
}

function selectLaptopForComparison(laptop) {
  showComparisonModal.value = false;
  showLaptopDetails(laptop, true);
}

function getSpecs(laptop) {
  if (!laptop) return {};

  const specs = {};
  for (const [key, value] of Object.entries(laptop)) {
    if (!['brand', 'name', 'image'].includes(key) && value) {
      specs[key] = value;
    }
  }
  return specs;
}

function formatSpecLabel(key) {
  return key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}
// Add this function to the script section
function getOrderedSpecs(laptop) {
  if (!laptop) {
    return {
      cpu: 'Not specified',
      ram: 'Not specified',
      storage: 'Not specified',
      screen: 'Not specified',
      gpu: 'Not specified'
    };
  }

  // Check if laptop has a specs string that needs to be parsed
  if (laptop.specs && typeof laptop.specs === 'string') {
    const specsList = laptop.specs.split(',').map(spec => spec.trim());
    return {
      cpu: specsList[0] || laptop.processor || 'Not specified',
      ram: specsList[1] || laptop.memory || 'Not specified',
      storage: specsList[2] || laptop.storage || 'Not specified',
      screen: specsList[3] || laptop.display || 'Not specified',
      gpu: specsList[4] || laptop.graphics || 'Not specified'
    };
  }

  // Handle case where specs are separate properties
  return {
    cpu: laptop.processor || laptop.cpu || 'Not specified',
    ram: laptop.memory || laptop.ram || 'Not specified',
    storage: laptop.storage || 'Not specified',
    screen: laptop.display || laptop.screen || 'Not specified',
    gpu: laptop.graphics || laptop.gpu || 'Not specified'
  };
}
// Expose methods to parent component
defineExpose({
  showLaptopDetails
});
</script>
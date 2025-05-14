<template>
  <div class="laptop-details-panel" :class="{ 'open': isOpen, 'comparison-mode': isComparisonMode }">
    <div class="laptop-details-header">
      <button class="laptop-details-close" @click="closeLaptopDetails">
        <i class="fas fa-arrow-right"></i>
      </button>
      <h2 v-if="!isComparisonMode">Laptop Details</h2>
      <h2 v-else>Laptop Comparison</h2>
    </div>

    <div class="laptop-details-content">
      <!-- Single laptop view -->
      <div v-if="!isComparisonMode && selectedLaptop">
        <div class="laptop-image-container">
          <img v-if="selectedLaptop.image" :src="selectedLaptop.image" :alt="selectedLaptop.name" class="laptop-image">
          <div v-else class="placeholder-image">
            <i class="fas fa-laptop"></i>
          </div>
          <h3>{{ selectedLaptop.brand }} {{ selectedLaptop.name }}</h3>
        </div>

        <div class="laptop-spec">
          <div class="laptop-spec-label">Price</div>
          <div class="laptop-spec-value">{{ formatPrice(selectedLaptop.price) }}</div>
        </div>

        <div class="laptop-spec">
          <div class="laptop-spec-label">Processor</div>
          <div class="laptop-spec-value">{{ formatSpecValue(selectedLaptop.cpu) }}</div>
        </div>

        <div class="laptop-spec">
          <div class="laptop-spec-label">RAM</div>
          <div class="laptop-spec-value">
            {{ formatSpecValue(selectedLaptop.key_specs?.RAM || findFeatureValue(selectedLaptop, 'RAM')) }}
          </div>
        </div>

        <div class="laptop-spec">
          <div class="laptop-spec-label">Storage</div>
          <div class="laptop-spec-value">{{ formatSpecValue(selectedLaptop.storage) }}</div>
        </div>

        <div class="laptop-spec">
          <div class="laptop-spec-label">Graphics</div>
          <div class="laptop-spec-value">{{ formatSpecValue(selectedLaptop.graphics) }}</div>
        </div>

        <div class="laptop-spec">
          <div class="laptop-spec-label">Display</div>
          <div class="laptop-spec-value">
            {{ formatSpecValue(selectedLaptop.screen_size) }}
            {{ selectedLaptop.screen_resolution ? `(${selectedLaptop.screen_resolution})` : '' }}
            {{ selectedLaptop.refresh_rate ? `@ ${selectedLaptop.refresh_rate}` : '' }}
          </div>
        </div>

        <div class="laptop-spec">
          <div class="laptop-spec-label">Operating System</div>
          <div class="laptop-spec-value">{{ formatSpecValue(selectedLaptop.operating_system) }}</div>
        </div>

        <div class="laptop-spec">
          <div class="laptop-spec-label">Battery Life</div>
          <div class="laptop-spec-value">{{ formatSpecValue(selectedLaptop.battery_life) }}</div>
        </div>

        <div class="laptop-spec">
          <div class="laptop-spec-label">Weight</div>
          <div class="laptop-spec-value">{{ formatSpecValue(selectedLaptop.weight) }}</div>
        </div>

        <div class="laptop-spec">
          <div class="laptop-spec-label">Features</div>
          <div class="laptop-spec-value">
            <ul>
              <li v-if="selectedLaptop.has_touchscreen">Touchscreen</li>
              <li v-if="selectedLaptop.has_backlit_keyboard">Backlit Keyboard</li>
              <li v-if="selectedLaptop.has_numeric_keyboard">Numeric Keypad</li>
              <li v-if="selectedLaptop.has_bluetooth">Bluetooth</li>
            </ul>
          </div>
        </div>

        <div class="laptop-spec">
          <div class="laptop-spec-label">Ports</div>
          <div class="laptop-spec-value">
            <ul>
              <li v-if="selectedLaptop.has_usb_c">USB-C</li>
              <li v-if="selectedLaptop.has_hdmi">HDMI</li>
              <li v-if="selectedLaptop.has_ethernet">Ethernet</li>
              <li v-if="selectedLaptop.has_thunderbolt">Thunderbolt</li>
              <li v-if="selectedLaptop.has_display_port">DisplayPort</li>
            </ul>
          </div>
        </div>

        <button class="compare-btn" @click="startComparison">
          Compare with another laptop
        </button>
      </div>

      <!-- Comparison View -->
      <!-- Comparison View -->
      <div v-else-if="isComparisonMode && selectedLaptop && comparisonLaptop" class="comparison-container">
        <!-- First Laptop -->
        <div class="laptop-column">
          <h3>{{ selectedLaptop.brand }} {{ selectedLaptop.name }}</h3>
          <div class="laptop-image-container">
            <img v-if="selectedLaptop.image" :src="selectedLaptop.image" :alt="selectedLaptop.name" class="laptop-image">
            <div v-else class="placeholder-image">
              <i class="fas fa-laptop"></i>
            </div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Price</div>
            <div class="laptop-spec-value">{{ formatPrice(selectedLaptop.price) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Processor</div>
            <div class="laptop-spec-value">{{ formatSpecValue(selectedLaptop.cpu) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">RAM</div>
            <div class="laptop-spec-value">
              {{ formatSpecValue(selectedLaptop.key_specs?.RAM || findFeatureValue(selectedLaptop, 'RAM')) }}
            </div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Storage</div>
            <div class="laptop-spec-value">{{ formatSpecValue(selectedLaptop.storage) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Graphics</div>
            <div class="laptop-spec-value">{{ formatSpecValue(selectedLaptop.graphics) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Display</div>
            <div class="laptop-spec-value">
              {{ formatSpecValue(selectedLaptop.screen_size) }}
              {{ selectedLaptop.screen_resolution ? `(${selectedLaptop.screen_resolution})` : '' }}
              {{ selectedLaptop.refresh_rate ? `@ ${selectedLaptop.refresh_rate}` : '' }}
            </div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Operating System</div>
            <div class="laptop-spec-value">{{ formatSpecValue(selectedLaptop.operating_system) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Battery Life</div>
            <div class="laptop-spec-value">{{ formatSpecValue(selectedLaptop.battery_life) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Weight</div>
            <div class="laptop-spec-value">{{ formatSpecValue(selectedLaptop.weight) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Features</div>
            <div class="laptop-spec-value">
              <ul>
                <li v-if="selectedLaptop.has_touchscreen">Touchscreen</li>
                <li v-if="selectedLaptop.has_backlit_keyboard">Backlit Keyboard</li>
                <li v-if="selectedLaptop.has_numeric_keyboard">Numeric Keypad</li>
                <li v-if="selectedLaptop.has_bluetooth">Bluetooth</li>
              </ul>
            </div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Ports</div>
            <div class="laptop-spec-value">
              <ul>
                <li v-if="selectedLaptop.has_usb_c">USB-C</li>
                <li v-if="selectedLaptop.has_hdmi">HDMI</li>
                <li v-if="selectedLaptop.has_ethernet">Ethernet</li>
                <li v-if="selectedLaptop.has_thunderbolt">Thunderbolt</li>
                <li v-if="selectedLaptop.has_display_port">DisplayPort</li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Second Laptop -->
        <div class="laptop-column">
          <h3>{{ comparisonLaptop.brand }} {{ comparisonLaptop.name }}</h3>
          <div class="laptop-image-container">
            <img v-if="comparisonLaptop.image" :src="comparisonLaptop.image" :alt="comparisonLaptop.name" class="laptop-image">
            <div v-else class="placeholder-image">
              <i class="fas fa-laptop"></i>
            </div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Price</div>
            <div class="laptop-spec-value">{{ formatPrice(comparisonLaptop.price) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Processor</div>
            <div class="laptop-spec-value">{{ formatSpecValue(comparisonLaptop.cpu) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">RAM</div>
            <div class="laptop-spec-value">
              {{ formatSpecValue(selectedLaptop.key_specs?.RAM || findFeatureValue(selectedLaptop, 'RAM')) }}
            </div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Storage</div>
            <div class="laptop-spec-value">{{ formatSpecValue(comparisonLaptop.storage) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Graphics</div>
            <div class="laptop-spec-value">{{ formatSpecValue(comparisonLaptop.graphics) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Display</div>
            <div class="laptop-spec-value">
              {{ formatSpecValue(comparisonLaptop.screen_size) }}
              {{ comparisonLaptop.screen_resolution ? `(${comparisonLaptop.screen_resolution})` : '' }}
              {{ comparisonLaptop.refresh_rate ? `@ ${comparisonLaptop.refresh_rate}` : '' }}
            </div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Operating System</div>
            <div class="laptop-spec-value">{{ formatSpecValue(comparisonLaptop.operating_system) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Battery Life</div>
            <div class="laptop-spec-value">{{ formatSpecValue(comparisonLaptop.battery_life) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Weight</div>
            <div class="laptop-spec-value">{{ formatSpecValue(comparisonLaptop.weight) }}</div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Features</div>
            <div class="laptop-spec-value">
              <ul>
                <li v-if="comparisonLaptop.has_touchscreen">Touchscreen</li>
                <li v-if="comparisonLaptop.has_backlit_keyboard">Backlit Keyboard</li>
                <li v-if="comparisonLaptop.has_numeric_keyboard">Numeric Keypad</li>
                <li v-if="comparisonLaptop.has_bluetooth">Bluetooth</li>
              </ul>
            </div>
          </div>

          <div class="laptop-spec">
            <div class="laptop-spec-label">Ports</div>
            <div class="laptop-spec-value">
              <ul>
                <li v-if="comparisonLaptop.has_usb_c">USB-C</li>
                <li v-if="comparisonLaptop.has_hdmi">HDMI</li>
                <li v-if="comparisonLaptop.has_ethernet">Ethernet</li>
                <li v-if="comparisonLaptop.has_thunderbolt">Thunderbolt</li>
                <li v-if="comparisonLaptop.has_display_port">DisplayPort</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
        <button v-if="isComparisonMode" class="exit-comparison-btn" @click="exitComparison">
          Exit Comparison
        </button>

    </div>

    <!-- Comparison Selection Modal -->
    <div v-if="showComparisonModal" class="comparison-modal">
      <div class="comparison-modal-content">
        <div class="comparison-modal-header">
          <h3>Select a laptop to compare</h3>
          <button class="close-modal-btn" @click="showComparisonModal = false">×</button>
        </div>
        <div class="comparison-modal-body">
          <div v-if="availableLaptops.length > 0" class="laptop-selection-list">
            <div
                v-for="laptop in availableLaptops"
                :key="`${laptop.brand}-${laptop.name}`"
                class="laptop-selection-item"
                @click="selectComparisonLaptop(laptop)"
            >
              <h4>{{ laptop.brand }} {{ laptop.name }}</h4>
              <div class="laptop-specs-preview">
                <span>{{ formatSpecValue(laptop.cpu) }}</span>
                <span>
              {{ formatSpecValue(selectedLaptop.key_specs?.RAM || findFeatureValue(selectedLaptop, 'RAM')) }}
                </span>
                <span>{{ formatPrice(laptop.price) }}</span>
              </div>
            </div>
          </div>
          <div v-else class="no-laptops-message">
            No other laptops available for comparison
          </div>
          <button class="cancel-comparison-btn" @click="showComparisonModal = false">
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { formatPrice, formatSpecValue } from '~/server/utils/formatters';
import { useChatStore } from '~/store/chat';

export default {
  props: {
    isOpen: {
      type: Boolean,
      default: false
    }
  },

  data() {
    return {
      selectedLaptop: null,
      comparisonLaptop: null,
      isComparisonMode: false,
      showComparisonModal: false
    };
  },

  computed: {
    chatStore() {
      return useChatStore();
    },

    availableLaptops() {
      if (!this.selectedLaptop) return [];

      // Filter out the currently selected laptop
      return this.chatStore.currentRecommendations.filter(laptop => {
        return laptop.name !== this.selectedLaptop.name || laptop.brand !== this.selectedLaptop.brand;
      });
    }
  },

  methods: {
    formatPrice,
    formatSpecValue,

    showLaptopDetails(laptop) {
      this.selectedLaptop = laptop;
      this.$emit('open');
    },

    closeLaptopDetails() {
      this.$emit('close');

      // Reset comparison mode when closing
      if (this.isComparisonMode) {
        this.exitComparison();
      }
    },

    selectLaptop(laptop) {
      this.selectedLaptop = laptop;
    },

    startComparison() {
      this.showComparisonModal = true;
    },

    selectComparisonLaptop(laptop) {
      this.comparisonLaptop = laptop;
      this.isComparisonMode = true;
      this.showComparisonModal = false;
      this.$emit('comparison-mode-change', true);
    },

    exitComparison() {
      this.isComparisonMode = false;
      this.comparisonLaptop = null;
      this.$emit('comparison-mode-change', false);
    }
  },

  watch: {
    // Update selected laptop when recommendations change
    'chatStore.currentRecommendations': {
      handler(newRecommendations) {
        if (newRecommendations.length > 0 && !this.selectedLaptop) {
          this.selectedLaptop = newRecommendations[0];
        }
      },
      immediate: true
    }
  }
};
</script>
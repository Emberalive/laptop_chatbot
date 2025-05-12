<template>
  <sidebar />
  <theme-toggle />
  <div class="chat-page">
    <div class="chat-container" :class="{ 'shifted': isDetailsPanelOpen, 'comparison-mode': isComparisonMode }">
      <div class="chat-header">
        <div class="header-left">
          <h1>Laptop Assistant</h1>
        </div>
        <button id="restart-chat-btn" class="restart-btn" @click="resetConversation">
          <i>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
              <path d="M3 3v5h5"></path>
            </svg>
          </i>
          Restart
        </button>
      </div>

      <div class="chat-messages" ref="chatMessagesRef">
        <div v-for="(message, index) in messages" :key="index"
             class="message" :class="message.type">
          <div v-if="message.type === 'recommendations'" class="recommendations">
            <h4>Recommended Laptops:</h4>
            <ul>
              <li v-for="(laptop, laptopIndex) in message.content" :key="laptopIndex"
                  class="recommendation-item"
                  :data-laptop-id="laptopIndex"
                  @click="showLaptopDetails(laptop)">
                <strong>{{ laptop.brand }} {{ laptop.name }}</strong><br>
                <span>Click for more details</span>
              </li>
            </ul>
          </div>
          <div v-else class="message-content" v-html="message.content"></div>
        </div>



        <div v-if="isTyping" class="message bot">
          <div class="typing-indicator">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
        </div>
    </div>


      <div class="chat-input-container">
        <input
            v-model="userInput"
            @keypress.enter="sendMessage"
            type="text"
            placeholder="Type your message..."
        />
        <button @click="sendMessage">Send</button>
      </div>
    </div>

    <LaptopDetailsPanel
        :is-open="isDetailsPanelOpen"
        @close="closeDetailsPanel"
        @comparison-mode-change="handleComparisonModeChange"
        ref="detailsPanelRef"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue';
import { useChatStore } from '~/store/chat';

const chatStore = useChatStore();
const API_URL = process.env.NUXT_PUBLIC_API_URL || 'http://86.19.219.159:8000';

const userInput = ref('');
const messages = ref([]);
const recommendations = ref([]);
const isTyping = ref(false);
const chatMessagesRef = ref(null);
const detailsPanelRef = ref(null);
const isDetailsPanelOpen = ref(false);
const isComparisonMode = ref(false);
const sessionId = ref('');

// Initial greeting
messages.value.push({
  type: 'bot',
  content: "Hello! I'm your laptop recommendation assistant. Tell me what type of laptop you're looking for and I'll find the best options for you."
});

function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  // Add user message to chat
  messages.value.push({
    type: 'user',
    content: message
  });

  // Clear input and scroll to bottom
  userInput.value = '';
  scrollToBottom();

  // Show typing indicator
  isTyping.value = true;

  // Send message to API
  fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message,
      session_id: sessionId.value
    })
  })
      .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
      })
      .then(data => {
        isTyping.value = false;

        if (data.session_id) {
          sessionId.value = data.session_id;
        }


        // Add bot message
        messages.value.push({
          type: 'bot',
          content: data.message
        });

        // Handle recommendations if present
        if (data.recommendations && data.recommendations.length > 0) {
          messages.value.push({
            type: 'recommendations',
            content: data.recommendations
          });
          chatStore.addRecommendations(data.recommendations);
        }

        // Handle follow-up question if present
        if (data.next_question) {
          messages.value.push({
            type: 'bot',
            content: data.next_question
          });
        }

        scrollToBottom();
      })
      .catch(error => {
        isTyping.value = false;
        messages.value.push({
          type: 'bot error',
          content: "Sorry, I encountered an error connecting to the service. Please try again later."
        });
        console.error('Error:', error);
        scrollToBottom();
      });
}

function resetConversation() {
  fetch(`${API_URL}/api/reset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId.value })
  })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          messages.value = [{
            type: 'bot',
            content: "Hello! I'm your laptop recommendation assistant. Tell me what type of laptop you're looking for and I'll find the best options for you."
          }];
          recommendations.value = [];

          // Close laptop details panel if open
          if (isDetailsPanelOpen.value) {
            isDetailsPanelOpen.value = false;
            isComparisonMode.value = false;
          }

          // Show reset confirmation
          const tempAlert = document.createElement('div');
          tempAlert.className = 'alert-popup';
          tempAlert.textContent = data.message;
          document.body.appendChild(tempAlert);
          setTimeout(() => { tempAlert.classList.add('fade-out'); }, 2000);
          setTimeout(() => { document.body.removeChild(tempAlert); }, 4000);
        }
      })
      .catch(error => console.error('Error resetting conversation:', error));
}

function scrollToBottom() {
  nextTick(() => {
    if (chatMessagesRef.value) {
      chatMessagesRef.value.scrollTop = chatMessagesRef.value.scrollHeight;
    }
  });
}

function showLaptopDetails(laptop) {
  if (detailsPanelRef.value) {
    detailsPanelRef.value.showLaptopDetails(laptop);
    isDetailsPanelOpen.value = true;
  }
}

function closeDetailsPanel() {
  isDetailsPanelOpen.value = false;
  isComparisonMode.value = false;
}

function handleComparisonModeChange(isComparison) {
  isComparisonMode.value = isComparison;
}

onMounted(() => {
  // Initialize chat interface
  resetConversation();
  scrollToBottom();
});
</script>

<style>
.chat-page {
  display: flex;
  width: 100%;
  max-width: 1150px;
  height: 80vh;
  position: relative;
}

.chat-container {
  flex: 1;
  border-radius: 10px 0 0 10px;
  transition: width 0.3s ease;
}

</style>
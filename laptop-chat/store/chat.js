// store/chat.js
import { defineStore } from 'pinia';

export const useChatStore = defineStore('chat', {
    state: () => ({
        messages: [],
        recommendedLaptops: [],
        currentRecommendations: [], // Add this for the latest recommendations
        sessionId: null
    }),

    actions: {
        addMessage(message) {
            this.messages.push(message);
        },

        async sendMessage(message) {
            // API call logic
            // Update messages and recommendations

            // After getting recommendations from API:
            // this.currentRecommendations = laptopsFromApi;
        },

        resetChat() {
            this.messages = [{
                text: "Hello! I'm your laptop recommendation assistant. Tell me what type of laptop you're looking for and I'll find the best options for you.",
                sender: 'bot'
            }];
            this.currentRecommendations = [];
        }
    }
});
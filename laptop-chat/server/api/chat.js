// store/chat.js
import { defineStore } from 'pinia';
import { useUserStore } from '~/store/user';

export const useChatStore = defineStore('chat', {
    state: () => ({
        messages: [],
        recommendedLaptops: [],
        currentRecommendations: [],
        allRecommendations: [],
        sessionId: null
    }),

    actions: {
        addMessage(message) {
            this.messages.push(message);
        },

        async sendMessage(message) {
            this.addMessage({ text: message, sender: 'user' });

            try {
                const response = await $fetch('/api/chat', {
                    method: 'POST',
                    body: JSON.stringify({
                        message,
                        session_id: this.sessionId
                    }),
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                // Handle the response properly
                this.messages.push(...response.messages.map(msg => ({ text: msg, sender: 'bot' })));

                if (response.recommendations && response.recommendations.length > 0) {
                    this.currentRecommendations = response.recommendations;
                    this.addRecommendations(response.recommendations);

                    // Save each recommendation to the database
                    response.recommendations.forEach(laptop => {
                        this.saveRecommendation(laptop);
                    });
                }

                this.sessionId = response.session_id || this.sessionId;

            } catch (error) {
                console.error('Error calling chatbot API:', error);
                this.addMessage({ text: "I'm having trouble connecting to my knowledge base. Please try again later.", sender: 'bot' });
            }
        },

        addRecommendations(recommendations) {
            this.recommendedLaptops = recommendations;
            this.currentRecommendations = recommendations;

            // Add each recommendation to allRecommendations with timestamp
            recommendations.forEach(recommendation => {
                this.allRecommendations.push({
                    ...recommendation,
                    timestamp: Date.now()
                });
            });
        },

        resetChat() {
            this.messages = [{
                text: "Hello! I'm your laptop recommendation assistant. Tell me what type of laptop you're looking for and I'll find the best options for you.",
                sender: 'bot'
            }];
            this.currentRecommendations = [];
            this.allRecommendations = [];
        },

        async saveRecommendation(laptop) {
            const userStore = useUserStore();
            if (!userStore.isLoggedIn) return;

            try {
                await useFetch('/api/db', {
                    method: 'POST',
                    body: {
                        action: 'saveRecommendation',
                        username: userStore.currentUser.username,
                        model_id: laptop.id || `${laptop.brand}-${laptop.name}`,
                        model_name: laptop.name,
                        model_brand: laptop.brand
                    }
                });
            } catch (error) {
                console.error('Error saving recommendation:', error);
            }
        }
    }
});
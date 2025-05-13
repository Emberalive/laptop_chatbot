<template>
  <div>
    <ThemeToggle />
    <Sidebar />

    <div class="past-recs-container">
      <h1>Your Past Recommendations</h1>

      <div v-if="!userStore.isLoggedIn" class="login-required">
        <p>Please log in to view your past recommendations.</p>
        <button @click="navigateTo('/profile')" class="login-btn">Log In</button>
      </div>

      <div v-else>
        <div v-if="isLoading" class="loading">Loading your recommendations...</div>

        <div v-else-if="recommendations.length === 0" class="no-recs">
          <p>You don't have any saved recommendations yet.</p>
          <p>Start a chat to get personalized laptop recommendations!</p>
          <button @click="navigateTo('/chat')" class="start-chat-btn">Start Chat</button>
        </div>

        <div v-else class="recommendations-list">
          <table>
            <thead>
            <tr>
              <th>Brand</th>
              <th>Model</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
            </thead>
            <tbody>
            <tr v-for="rec in recommendations" :key="rec.id">
              <td>{{ rec.model_brand }}</td>
              <td>{{ rec.model_name }}</td>
              <td>{{ formatDate(rec.rec_date) }}</td>
              <td>
                <button @click="deleteRecommendation(rec)" class="delete-btn">Delete</button>
              </td>
            </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import ThemeToggle from '~/components/ThemeToggle.vue';
import Sidebar from '~/components/Sidebar.vue';
import { useUserStore } from '~/store/user';

const userStore = useUserStore();
const recommendations = ref([]);
const isLoading = ref(true);

onMounted(async () => {
  // Check if user is authenticated
  await userStore.checkAuth();

  if (userStore.isLoggedIn) {
    await fetchRecommendations();
  } else {
    isLoading.value = false;
  }
});

async function fetchRecommendations() {
  isLoading.value = true;
  try {
    const { data } = await useFetch('/api/db', {
      method: 'POST',
      body: {
        action: 'getPastRecommendations',
        username: userStore.currentUser.username
      }
    });

    if (data.value?.success) {
      recommendations.value = data.value.recommendations;
    }
  } catch (error) {
    console.error('Error fetching recommendations:', error);
  } finally {
    isLoading.value = false;
  }
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString();
}

async function deleteRecommendation(rec) {
  try {
    const { data } = await useFetch('/api/db', {
      method: 'POST',
      body: {
        action: 'deleteRecommendation',
        username: userStore.currentUser.username,
        rec_id: rec.rec_id
      }
    });

    if (data.value?.success) {
      // Remove the deleted recommendation from the list
      recommendations.value = recommendations.value.filter(item => item.rec_id !== rec.rec_id);
    }
  } catch (error) {
    console.error('Error deleting recommendation:', error);
  }
}
</script>

<style scoped>
.past-recs-container {
  max-width: 1000px;
  margin: 40px auto;
  padding: 20px;
}

h1 {
  margin-bottom: 30px;
  text-align: center;
}

.login-required, .no-recs {
  text-align: center;
  margin: 40px 0;
}

.recommendations-list {
  margin-top: 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid var(--accent-color);
}

th {
  background-color: var(--secondary-bg-color);
}

.login-btn, .start-chat-btn, .view-btn {
  background-color: var(--background-color);
  color: var(--btn-text-color);
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

.delete-btn {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}

.delete-btn:hover {
  background-color: #c0392b;
}
</style>
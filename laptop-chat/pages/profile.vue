<template>
  <div>
    <ThemeToggle />
    <Sidebar />

      <div class="profile-content">
        <button class="close-profile-btn" @click="$router.push('/')">&times;</button>

        <!-- If not logged in show login form -->
        <div v-if="!userStore.isLoggedIn">
          <div class="profile-header">
            <div class="profile-avatar"><i><ion-icon name="person-outline"></ion-icon></i></div>
            <h1>Account Login</h1>
          </div>
          <div class="login-form" v-if="!showRegister">
            <div class="form-group">
              <label for="username">Username</label>
              <input type="text" id="username" v-model="loginForm.username" class="profile-input" placeholder="Enter your username">
            </div>
            <div class="form-group">
              <label for="password">Password</label>
              <input type="password" id="password" v-model="loginForm.password" class="profile-input" placeholder="Enter your password">
            </div>
            <div class="login-actions">
              <button @click="handleLogin" class="profile-save-btn">Login</button>
            </div>
            <div class="register-link">
              <p>Don't have an account? <a href="#" @click.prevent="showRegister = true">Register</a></p>
            </div>
          </div>

          <!-- Registration form -->
          <div class="login-form" v-else>
            <div class="form-group">
              <label for="reg-username">Username</label>
              <input type="text" id="reg-username" v-model="registerForm.username" class="profile-input" placeholder="Choose a username">
            </div>
            <div class="form-group">
              <label for="reg-email">Email</label>
              <input type="email" id="reg-email" v-model="registerForm.email" class="profile-input" placeholder="Enter your email">
            </div>
            <div class="form-group">
              <label for="reg-password">Password</label>
              <input type="password" id="reg-password" v-model="registerForm.password" class="profile-input" placeholder="Choose a password">
            </div>
            <div class="login-actions">
              <button @click="handleRegister" class="profile-save-btn">Register</button>
            </div>
            <div class="register-link">
              <p>Already have an account? <a href="#" @click.prevent="showRegister = false">Login</a></p>
            </div>
          </div>
        </div>

        <!-- If logged in show profile -->
        <div v-else>
          <div class="profile-header">
            <div class="profile-avatar"><i><ion-icon name="person-outline"></ion-icon></i></div>
            <h1>Welcome, {{ userStore.currentUser.username }}!</h1>
          </div>
          <div class="profile-details">
            <div class="profile-section">
              <h2>Personal Information</h2>
              <div class="profile-field">
                <label>Name</label>
                <input type="text" v-model="profileForm.name" class="profile-input">
              </div>
              <div class="profile-field">
                <label>Email</label>
                <input type="email" v-model="profileForm.email" class="profile-input">
              </div>
            </div>

            <div class="profile-section">
              <h2>Laptop Preferences</h2>
              <div class="profile-field">
                <label>Primary Use</label>
                <select v-model="profileForm.primaryUse" class="profile-input">
                  <option value="gaming">Gaming</option>
                  <option value="work">Professional/Work</option>
                  <option value="student">Student</option>
                  <option value="general">General Use</option>
                </select>
              </div>
              <div class="profile-field">
                <label>Preferred Budget Range</label>
                <select v-model="profileForm.budget" class="profile-input">
                  <option value="budget">Budget ($300-$700)</option>
                  <option value="midrange">Mid-range ($700-$1200)</option>
                  <option value="premium">Premium ($1200-$2000)</option>
                  <option value="highend">High-end ($2000+)</option>
                </select>
              </div>
            </div>

            <div class="profile-actions">
              <button @click="saveProfileChanges" class="profile-save-btn">{{ saveButtonText }}</button>
              <button @click="handleLogout" class="profile-logout-btn">Logout</button>
            </div>
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
const showRegister = ref(false);
const saveButtonText = ref('Save Changes');

const loginForm = reactive({
  username: '',
  password: ''
});

const registerForm = reactive({
  username: '',
  email: '',
  password: ''
});

const profileForm = reactive({
  name: '',
  email: '',
  primaryUse: 'general',
  budget: 'midrange'
});

// Set initial values when component mounts
onMounted(() => {
  if (userStore.isLoggedIn) {
    profileForm.name = userStore.currentUser.name;
    profileForm.email = userStore.currentUser.email;
  }
});

function handleLogin() {
  if (userStore.login(loginForm.username, loginForm.password)) {
    // Success
  } else {
    alert("Please enter both username and password");
  }
}

function handleRegister() {
  if (userStore.register(registerForm.username, registerForm.email, registerForm.password)) {
    // Success
  } else {
    alert("Please fill in all fields");
  }
}

function saveProfileChanges() {
  userStore.saveProfile(profileForm.name, profileForm.email);

  saveButtonText.value = 'Saved!';
  setTimeout(() => {
    saveButtonText.value = 'Save Changes';
  }, 2000);
}

function handleLogout() {
  userStore.logout();
  navigateTo('/');
}
</script>
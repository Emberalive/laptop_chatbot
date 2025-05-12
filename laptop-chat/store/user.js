export const useUserStore = defineStore('user', {
    state: () => ({
        isLoggedIn: false,
        currentUser: {
            username: '',
            email: '',
            name: ''
        }
    }),

    actions: {
        setUser(user) {
            this.isLoggedIn = true;
            this.currentUser.id = user.id;
            this.currentUser.username = user.username;
            this.currentUser.email = user.email;
            this.currentUser.name = user.username; // Default name to username
            return true;
        },

        saveProfile(name, email) {
            this.currentUser.username = username;
            this.currentUser.email = email;
            this.currentUser.primaryUse = primaryUse;
            this.currentUser.budget = budget;
            return true;
        },

        logout() {
            this.isLoggedIn = false;
            this.currentUser = {
                username: '',
                email: '',
                name: ''
            };
        }
    }
});
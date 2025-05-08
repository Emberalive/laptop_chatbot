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
        login(username, password) {
            // For demo purposes - would connect to backend in production
            if (username && password) {
                this.isLoggedIn = true;
                this.currentUser.username = username;
                this.currentUser.name = username;
                return true;
            }
            return false;
        },

        register(username, email, password) {
            if (username && email && password) {
                this.isLoggedIn = true;
                this.currentUser.username = username;
                this.currentUser.email = email;
                this.currentUser.name = username;
                return true;
            }
            return false;
        },

        saveProfile(name, email) {
            this.currentUser.name = name;
            this.currentUser.email = email;
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
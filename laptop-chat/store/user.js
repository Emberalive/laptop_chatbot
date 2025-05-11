export const useUserStore = defineStore('user', {
    state: () => ({
        isLoggedIn: false,
        currentUser: {
            id: null,
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
            this.currentUser.name = name;
            this.currentUser.email = email;
        },

        logout() {
            this.isLoggedIn = false;
            this.currentUser = {
                id: null,
                username: '',
                email: '',
                name: ''
            };
        }
    }
});
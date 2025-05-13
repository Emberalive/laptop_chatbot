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
            this.currentUser.primaryUse = user.primaryUse;
            this.currentUser.budget = user.budget;
            return true;
        },

        saveProfile(username, email, primaryUse, budget) {
            this.currentUser.username = username;
            this.currentUser.email = email;
            this.currentUser.primaryUse = primaryUse;
            this.currentUser.budget = budget;
            return true;
        },

        async checkAuth() {
            try {
                const { data } = await useFetch('/api/db', {
                    method: 'POST',
                    body: {
                        action: 'verify'
                    }
                });

                if (data.value?.success) {
                    this.setUser(data.value.user);
                    return true;
                }
                return false;
            } catch (error) {
                console.error('Auth check error:', error);
                return false;
            }
        },

        async logout() {
            try {
                await useFetch('/api/db', {
                    method: 'POST',
                    body: { action: 'logout' }
                });
            } catch (error) {
                console.error('Logout error:', error);
            }

            this.isLoggedIn = false;
            this.currentUser = {
                username: '',
                email: '',
                name: ''
            };
        }
    }
});
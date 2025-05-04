document.addEventListener('DOMContentLoaded', () => {
    // Initialize elements
    const splashScreen = document.getElementById('splash-screen');
    const chatContainer = document.getElementById('chat-container');
    const startChatBtn = document.getElementById('start-chat-btn');
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const themeToggleCheckbox = document.getElementById('theme-toggle-checkbox');
    const profileContainer = document.getElementById('profile-container');
    const originalProfileContent = document.querySelector('.profile-content').innerHTML;
    let isLoggedIn = false;

    // Add a variable to store current user data
    let currentUser = {
        username: '',
        email: '',
        name: ''
    };

    // Add laptop details panel to the HTML
    const laptopDetailsPanel = document.createElement('div');
    laptopDetailsPanel.className = 'laptop-details-panel';
    laptopDetailsPanel.innerHTML = `
    <div class="laptop-details-header">
        <button class="laptop-details-close">←</button>
        <h2>Laptop Details</h2>
    </div>
    <div class="laptop-details-content"></div>
    `;
    chatContainer.parentNode.insertBefore(laptopDetailsPanel, chatContainer.nextSibling);
    // Get the close button after the panel is added to DOM
    const laptopDetailsClose = laptopDetailsPanel.querySelector('.laptop-details-close');

    // Close button functionality for laptop details
    if (laptopDetailsClose) {
        laptopDetailsClose.addEventListener('click', () => {
            laptopDetailsPanel.classList.remove('open');
            chatContainer.classList.remove('shifted');
        });
    }

    //API Config
    const API_URL = 'http://localhost:8000';
    let sessionId = crypto.randomUUID();

    // comparison variables
    let comparisonMode = false;
    let comparisonLaptops = [];
    let recommendationsCache = [];

    // Theme handling
    const currentTheme = localStorage.getItem('theme') ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? 'dark' : 'light');

    if (currentTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        themeToggleCheckbox.checked = true;
    }

    function toggleTheme(e) {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    }

    themeToggleCheckbox.addEventListener('change', toggleTheme);

    startChatBtn.addEventListener('click', () => {
        splashScreen.classList.add('fade-out');
        chatContainer.style.display = 'flex';
        setTimeout(() => {
            chatContainer.classList.add('fade-in');
            splashScreen.style.display = 'none';
        }, 800);
    });

    function showLaptopDetails(laptop, isComparison = false) {
        // Cache the full recommendations data when showing first laptop
        if (recommendationsCache.length === 0 && !isComparison) {
            const recsElements = document.querySelectorAll('.recommendation-item');
            if (recsElements.length > 0) {
                const recsList = document.querySelector('.recommendations');
                if (recsList && recsList.dataset.recommendationsData) {
                    recommendationsCache = JSON.parse(recsList.dataset.recommendationsData);
                }
            }
        }

        // Handle comparison mode
        if (isComparison) {
            comparisonMode = true;
            if (!comparisonLaptops.includes(laptop)) {
                comparisonLaptops.push(laptop);
            }
            if (comparisonLaptops.length > 2) {
                comparisonLaptops.shift(); // Keep only 2 laptops
            }
        } else {
            comparisonMode = false;
            comparisonLaptops = [laptop];
        }

        // Split specs for all laptops in comparison
        const laptopSpecs = comparisonLaptops.map(lap => {
            const specsList = lap.specs.split(',').map(spec => spec.trim());
            return {
                laptop: lap,
                cpu: specsList[0] || 'Not specified',
                ram: specsList[1] || 'Not specified',
                storage: specsList[2] || 'Not specified',
                screen: specsList[3] || 'Not specified',
                gpu: specsList[4] || 'Not specified'
            };
        });

        // Update panel title based on mode
        const panelTitle = comparisonMode && comparisonLaptops.length === 2 ?
            'Laptop Comparison' : 'Laptop Details';

        // Prepare HTML for the panel header
        const headerHTML = `
        <div class="laptop-details-header">
            <button class="laptop-details-close">←</button>
            <h2>${panelTitle}</h2>
            ${comparisonMode ? '<button class="exit-comparison-btn">Exit Comparison</button>' : ''}
        </div>
    `;

        // Prepare the content HTML
        let contentHTML = '';

        if (comparisonMode && comparisonLaptops.length === 2) {
            // Side-by-side comparison with same styling as single view
            contentHTML = `
            <div class="comparison-container">
                <div class="laptop-column">
                    <h3>${laptopSpecs[0].laptop.brand} ${laptopSpecs[0].laptop.name}</h3>
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">CPU</div>
                        <div class="laptop-spec-value">${laptopSpecs[0].cpu}</div>
                    </div>
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">RAM</div>
                        <div class="laptop-spec-value">${laptopSpecs[0].ram}</div>
                    </div>
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">Storage</div>
                        <div class="laptop-spec-value">${laptopSpecs[0].storage}</div>
                    </div>
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">Screen</div>
                        <div class="laptop-spec-value">${laptopSpecs[0].screen}</div>
                    </div>
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">GPU</div>
                        <div class="laptop-spec-value">${laptopSpecs[0].gpu}</div>
                    </div>
                    ${laptopSpecs[0].laptop.price ? `
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">Price</div>
                        <div class="laptop-spec-value">${laptopSpecs[0].laptop.price}</div>
                    </div>` : ''}
                    ${laptopSpecs[0].laptop.features ? `
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">Features</div>
                        <div class="laptop-spec-value">${laptopSpecs[0].laptop.features}</div>
                    </div>` : ''}
                </div>

                <div class="laptop-column">
                    <h3>${laptopSpecs[1].laptop.brand} ${laptopSpecs[1].laptop.name}</h3>
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">CPU</div>
                        <div class="laptop-spec-value">${laptopSpecs[1].cpu}</div>
                    </div>
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">RAM</div>
                        <div class="laptop-spec-value">${laptopSpecs[1].ram}</div>
                    </div>
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">Storage</div>
                        <div class="laptop-spec-value">${laptopSpecs[1].storage}</div>
                    </div>
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">Screen</div>
                        <div class="laptop-spec-value">${laptopSpecs[1].screen}</div>
                    </div>
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">GPU</div>
                        <div class="laptop-spec-value">${laptopSpecs[1].gpu}</div>
                    </div>
                    ${laptopSpecs[1].laptop.price ? `
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">Price</div>
                        <div class="laptop-spec-value">${laptopSpecs[1].laptop.price}</div>
                    </div>` : ''}
                    ${laptopSpecs[1].laptop.features ? `
                    <div class="laptop-spec">
                        <div class="laptop-spec-label">Features</div>
                        <div class="laptop-spec-value">${laptopSpecs[1].laptop.features}</div>
                    </div>` : ''}
                </div>
            </div>
        `;
        } else {
            // Single laptop view - keep as is
            contentHTML = `
            <div class="laptop-spec">
                <div class="laptop-spec-label">Model</div>
                <div class="laptop-spec-value">${laptop.brand} ${laptop.name}</div>
            </div>
            <div class="laptop-spec">
                <div class="laptop-spec-label">CPU</div>
                <div class="laptop-spec-value">${laptopSpecs[0].cpu}</div>
            </div>
            <div class="laptop-spec">
                <div class="laptop-spec-label">RAM</div>
                <div class="laptop-spec-value">${laptopSpecs[0].ram}</div>
            </div>
            <div class="laptop-spec">
                <div class="laptop-spec-label">Storage</div>
                <div class="laptop-spec-value">${laptopSpecs[0].storage}</div>
            </div>
            <div class="laptop-spec">
                <div class="laptop-spec-label">Screen</div>
                <div class="laptop-spec-value">${laptopSpecs[0].screen}</div>
            </div>
            <div class="laptop-spec">
                <div class="laptop-spec-label">GPU</div>
                <div class="laptop-spec-value">${laptopSpecs[0].gpu}</div>
            </div>
            ${laptop.price ? `
            <div class="laptop-spec">
                <div class="laptop-spec-label">Price</div>
                <div class="laptop-spec-value">${laptop.price}</div>
            </div>` : ''}
            ${laptop.features ? `
            <div class="laptop-spec">
                <div class="laptop-spec-label">Features</div>
                <div class="laptop-spec-value">${laptop.features}</div>
            </div>` : ''}
            ${!comparisonMode ? '<button class="compare-btn">Compare with another laptop</button>' : ''}
        `;
        }

        // Update the panel HTML
        laptopDetailsPanel.innerHTML = headerHTML + `<div class="laptop-details-content">${contentHTML}</div>`;

        // Set wider panel class for comparison mode
        if (comparisonMode && comparisonLaptops.length === 2) {
            laptopDetailsPanel.classList.add('comparison-mode');
        } else {
            laptopDetailsPanel.classList.remove('comparison-mode');
        }

        // Add event listeners for buttons
        laptopDetailsPanel.querySelector('.laptop-details-close').addEventListener('click', () => {
            laptopDetailsPanel.classList.remove('open');
            laptopDetailsPanel.classList.remove('comparison-mode');
            chatContainer.classList.remove('shifted');
            chatContainer.classList.remove('comparison-mode');
            comparisonMode = false;
            comparisonLaptops = [];
        });

        const exitComparisonBtn = laptopDetailsPanel.querySelector('.exit-comparison-btn');
        if (exitComparisonBtn) {
            exitComparisonBtn.addEventListener('click', () => {
                comparisonMode = false;
                laptopDetailsPanel.classList.remove('comparison-mode');
                chatContainer.classList.remove('comparison-mode');
                if (comparisonLaptops.length > 0) {
                    showLaptopDetails(comparisonLaptops[0]);
                }
            });
        }

        const compareBtn = laptopDetailsPanel.querySelector('.compare-btn');
        if (compareBtn) {
            compareBtn.addEventListener('click', () => {
                toggleComparisonSelection();
            });
        }

        laptopDetailsPanel.classList.add('open');
        chatContainer.classList.add('shifted');
    }

// Function to toggle selection mode for comparison
    function toggleComparisonSelection() {
        // Create an overlay for selecting a laptop to compare
        const selectionOverlay = document.createElement('div');
        selectionOverlay.className = 'comparison-selection-overlay';
        selectionOverlay.innerHTML = `
        <div class="comparison-selection-container">
            <h3>Select a laptop to compare</h3>
            <div class="comparison-selection-list"></div>
            <button class="cancel-comparison-btn">Cancel</button>
        </div>
    `;

        document.body.appendChild(selectionOverlay);

        // Fill the selection list with available laptops
        const selectionList = selectionOverlay.querySelector('.comparison-selection-list');

        // Use cached recommendations or get them from the page
        let availableLaptops = recommendationsCache;
        if (availableLaptops.length === 0) {
            const recItems = document.querySelectorAll('.recommendation-item');
            recItems.forEach(item => {
                const laptopId = item.dataset.laptopId;
                const recsContainer = item.closest('.recommendations');
                if (recsContainer && recsContainer.dataset.recommendationsData) {
                    const allLaptops = JSON.parse(recsContainer.dataset.recommendationsData);
                    if (allLaptops[laptopId]) {
                        availableLaptops.push(allLaptops[laptopId]);
                    }
                }
            });
        }

        // Filter out the currently selected laptop
        availableLaptops = availableLaptops.filter(laptop =>
            !comparisonLaptops.some(selected =>
                selected.brand === laptop.brand && selected.name === laptop.name));

        // Add laptops to selection list
        availableLaptops.forEach((laptop, index) => {
            const item = document.createElement('div');
            item.className = 'comparison-selection-item';
            item.innerHTML = `<strong>${laptop.brand} ${laptop.name}</strong>`;
            item.addEventListener('click', () => {
                document.body.removeChild(selectionOverlay);
                showLaptopDetails(laptop, true);
            });
            selectionList.appendChild(item);
        });

        // Cancel button functionality
        selectionOverlay.querySelector('.cancel-comparison-btn').addEventListener('click', () => {
            document.body.removeChild(selectionOverlay);
        });
    }

    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;

        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'message user';
        userMessageDiv.innerHTML = `<div class="message-content">${message}</div>`;
        chatMessages.appendChild(userMessageDiv);

        userInput.value = '';
        chatMessages.scrollTop = chatMessages.scrollHeight;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                chatMessages.removeChild(typingDiv);

                if (data.session_id) {
                    sessionId = data.session_id;
                }

                const botMessageDiv = document.createElement('div');
                botMessageDiv.className = 'message bot';
                botMessageDiv.innerHTML = `<div class="message-content">${data.message}</div>`;
                chatMessages.appendChild(botMessageDiv);

                if (data.recommendations && data.recommendations.length > 0) {
                    const recsDiv = document.createElement('div');
                    recsDiv.className = 'recommendations';
                    recsDiv.dataset.recommendationsData = JSON.stringify(data.recommendations);

                    let recsHTML = '<h4>Recommended Laptops:</h4><ul>';
                    data.recommendations.forEach((laptop, index) => {
                        recsHTML += `
                            <li class="recommendation-item" data-laptop-id="${index}">
                                <strong>${laptop.brand} ${laptop.name}</strong><br>
                                <span>Click for more details</span>
                            </li>`;
                    });
                    recsHTML += '</ul>';

                    recsDiv.innerHTML = recsHTML;
                    chatMessages.appendChild(recsDiv);

                    const recItems = recsDiv.querySelectorAll('.recommendation-item');
                    recItems.forEach(item => {
                        item.addEventListener('click', () => {
                            const laptopId = item.dataset.laptopId;
                            const laptop = data.recommendations[laptopId];
                            showLaptopDetails(laptop);
                        });
                    });
                }

                if (data.next_question) {
                    const nextQuestionDiv = document.createElement('div');
                    nextQuestionDiv.className = 'message bot';
                    nextQuestionDiv.innerHTML = `<div class="message-content">${data.next_question}</div>`;
                    chatMessages.appendChild(nextQuestionDiv);
                }

                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(error => {
                chatMessages.removeChild(typingDiv);

                const errorDiv = document.createElement('div');
                errorDiv.className = 'message bot error';
                errorDiv.innerHTML = `
                    <div class="message-content">
                        Sorry, I encountered an error connecting to the service. Please try again later.
                    </div>
                `;
                chatMessages.appendChild(errorDiv);
                console.error('Error:', error);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            });
    }

    function resetConversation() {
        fetch(`${API_URL}/api/reset`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    chatMessages.innerHTML = '';

                    // Add system message about reset
                    const tempAlert = document.createElement('div');
                    tempAlert.className = 'alert-popup';
                    tempAlert.textContent = data.message;
                    document.body.appendChild(tempAlert);
                    setTimeout(() => { tempAlert.classList.add('fade-out'); }, 2000);
                    setTimeout(() => { document.body.removeChild(tempAlert); }, 4000);

                    // Add the initial greeting message
                    const greetingMessage = document.createElement('div');
                    greetingMessage.className = 'message bot';
                    greetingMessage.innerHTML = `
                    <div class="message-content">
                        Hello! I'm your laptop recommendation assistant. Tell me what type of laptop you're looking for and I'll find the best options for you.
                    </div>
                `;
                    chatMessages.appendChild(greetingMessage);

                    // Close laptop details panel if it's open
                    if (laptopDetailsPanel.classList.contains('open')) {
                        laptopDetailsPanel.classList.remove('open');
                        chatContainer.classList.remove('shifted');
                    }
                }
            })
            .catch(error => {
                console.error('Error resetting conversation:', error);
            });
    }

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Get the restart button and add event listener
    const restartChatBtn = document.getElementById('restart-chat-btn');
    if (restartChatBtn) {
        restartChatBtn.addEventListener('click', resetConversation);
    }

    // Sidebar functionality
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebarClose = document.getElementById('sidebar-close');
    const overlay = document.getElementById('overlay');

    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('active');
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    }

    sidebarToggle.addEventListener('click', openSidebar);
    sidebarClose.addEventListener('click', closeSidebar);
    overlay.addEventListener('click', closeSidebar);

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeSidebar();
            laptopDetailsPanel.classList.remove('open');
            chatContainer.classList.remove('shifted');
        }
    });

    // Handle login function
    // Handle login function
    function handleLogin() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        if (username && password) {
            // Simple validation for demo purposes
            isLoggedIn = true;

            // Store user information
            currentUser.username = username;
            currentUser.email = ''; // Will be filled in later
            currentUser.name = username; // Default name to username

            // Show success message
            const loginBtn = document.getElementById('login-btn');
            loginBtn.textContent = "Logged in!";

            // Redirect to profile page after delay
            setTimeout(() => {
                // Restore original profile page HTML first
                document.querySelector('.profile-content').innerHTML = originalProfileContent;
                displayProfilePage();
            }, 10);
        } else {
            alert("Please enter both username and password");
        }
    }

    // Show registration form
    function showRegisterForm() {
        const loginForm = document.querySelector('.login-form');
        loginForm.innerHTML = `
            <div class="form-group">
                <label for="reg-username">Username</label>
                <input type="text" id="reg-username" class="profile-input" placeholder="Choose a username">
            </div>
            <div class="form-group">
                <label for="reg-email">Email</label>
                <input type="email" id="reg-email" class="profile-input" placeholder="Enter your email">
            </div>
            <div class="form-group">
                <label for="reg-password">Password</label>
                <input type="password" id="reg-password" class="profile-input" placeholder="Choose a password">
            </div>
            <div class="login-actions">
                <button id="register-btn" class="profile-save-btn">Register</button>
            </div>
            <div class="register-link">
                <p>Already have an account? <a href="#" id="login-link">Login</a></p>
            </div>
        `;

        document.getElementById('register-btn').addEventListener('click', handleRegister);
        document.getElementById('login-link').addEventListener('click', showLoginForm);
    }

    // Handle registration
    function handleRegister() {
        const username = document.getElementById('reg-username').value;
        const email = document.getElementById('reg-email').value;
        const password = document.getElementById('reg-password').value;

        if (username && email && password) {
            isLoggedIn = true;

            // Store user information
            currentUser.username = username;
            currentUser.email = email;
            currentUser.name = username; // Default name to username initially

            const registerBtn = document.getElementById('register-btn');
            registerBtn.textContent = "Registered!";

            setTimeout(() => {
                // Restore original profile page HTML first
                document.querySelector('.profile-content').innerHTML = originalProfileContent;
                displayProfilePage();
            }, 10);
        } else {
            alert("Please fill in all fields");
        }
    }


    // Show login form
    function showLoginForm() {
        const profileContent = document.querySelector('.profile-content');

        profileContent.innerHTML = `
            <button class="close-profile-btn" id="close-profile-btn">&times;</button>
            <div class="profile-header">
                <div class="profile-avatar"><i><ion-icon name="person-outline"></ion-icon></i></div>
                <h1>Account Login</h1>
            </div>
            <div class="login-form">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input type="text" id="username" class="profile-input" placeholder="Enter your username">
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" class="profile-input" placeholder="Enter your password">
                </div>
                <div class="login-actions">
                    <button id="login-btn" class="profile-save-btn">Login</button>
                </div>
                <div class="register-link">
                    <p>Don't have an account? <a href="#" id="register-link">Register</a></p>
                </div>
            </div>
        `;

        document.getElementById('login-btn').addEventListener('click', handleLogin);
        document.getElementById('register-link').addEventListener('click', showRegisterForm);
        document.getElementById('close-profile-btn').addEventListener('click', closeProfile);
    }

    // Display profile page after login - using the existing HTML structure
    function displayProfilePage() {
        // Use the original profile content structure from HTML
        const profileContent = document.querySelector('.profile-content');

        // Get the header element and update it
        const headerElement = profileContent.querySelector('.profile-header h1');
        if (headerElement) {
            headerElement.textContent = `Welcome, ${currentUser.username}!`;
        }

        // Update the personal information inputs with user data
        const nameInput = profileContent.querySelector('.profile-section:nth-child(1) .profile-field:nth-child(2) input');
        const emailInput = profileContent.querySelector('.profile-section:nth-child(1) .profile-field:nth-child(3) input');

        if (nameInput) {
            nameInput.value = currentUser.name || '';
        }

        if (emailInput) {
            emailInput.value = currentUser.email || '';
        }

        // Make sure close button works
        const closeProfileBtn = profileContent.querySelector('.close-profile-btn');
        if (closeProfileBtn) {
            closeProfileBtn.addEventListener('click', closeProfile);

        }

        // Set up the save button functionality
        const saveBtn = profileContent.querySelector('.profile-save-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', saveProfileChanges);
        }
    }

    // Add function to save profile changes
    function saveProfileChanges() {
        const nameInput = document.querySelector('.profile-section:nth-child(1) .profile-field:nth-child(2) input');
        const emailInput = document.querySelector('.profile-section:nth-child(1) .profile-field:nth-child(3) input');

        // Update user data
        if (nameInput) currentUser.name = nameInput.value;
        if (emailInput) currentUser.email = emailInput.value;

        // Show saved confirmation
        const saveBtn = document.querySelector('.profile-save-btn');
        const originalText = saveBtn.textContent;
        saveBtn.textContent = 'Saved!';
        saveBtn.disabled = true;

        setTimeout(() => {
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
        }, 2000);
    }

    // Function to close profile
    function closeProfile() {
        profileContainer.classList.remove('fade-in');

        setTimeout(() => {
            profileContainer.style.display = 'none';
            if (splashScreen.style.display === 'none') {
                chatContainer.style.display = 'flex';
                setTimeout(() => {
                    chatContainer.classList.add('fade-in');
                }, 50);
            } else {
                splashScreen.style.display = 'flex';
                splashScreen.classList.remove('fade-out');
            }
        }, 800);
    }

    // Profile functionality
    const profileLink = document.querySelector('.sidebar-nav li');

    if (profileLink && profileContainer) {
        profileLink.addEventListener('click', () => {
            closeSidebar();

            if (chatContainer.style.display !== 'none') {
                chatContainer.classList.remove('fade-in');
                setTimeout(() => {
                    chatContainer.style.display = 'none';
                }, 400);
            }

            if (splashScreen.style.display !== 'none') {
                splashScreen.classList.add('fade-out');
                setTimeout(() => {
                    splashScreen.style.display = 'none';
                }, 400);
            }

            // Update profile content based on login state
            if (!isLoggedIn) {
                showLoginForm();
            } else {
                displayProfilePage();
            }

            setTimeout(() => {
                profileContainer.style.display = 'flex';
                setTimeout(() => {
                    profileContainer.classList.add('fade-in');
                }, 50);
            }, 500);
        });
    }
});
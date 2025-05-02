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
    const closeProfileBtn = document.getElementById('close-profile-btn');


    //API Config
    const API_URL = 'http://localhost:8000'; // Change this to your API URL

    let sessionId = crypto.randomUUID(); // To track conversation state

    // Check for saved theme preference or use preferred color scheme
    const currentTheme = localStorage.getItem('theme') ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? 'dark' : 'light');

    // Set initial theme
    if (currentTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        themeToggleCheckbox.checked = true;
    }

    // Theme toggle handler
    function toggleTheme(e) {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    }

    // Add theme toggle event listener
    themeToggleCheckbox.addEventListener('change', toggleTheme);

    // Start chat button click handler
    startChatBtn.addEventListener('click', () => {
        splashScreen.classList.add('fade-out');
        chatContainer.style.display = 'flex';
        setTimeout(() => {
            chatContainer.classList.add('fade-in');
            splashScreen.style.display = 'none';
        }, 800);
    });

    // Send message function
// Send message function
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;

        // Add user's message
        const userMessageDiv = document.createElement('div');
        userMessageDiv.className = 'message user';
        userMessageDiv.innerHTML = `<div class="message-content">${message}</div>`;
        chatMessages.appendChild(userMessageDiv);

        // Clear input
        userInput.value = '';

        // Scroll to bottom of chat
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Show typing indicator
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

        // Call the API
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
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Remove typing indicator
                chatMessages.removeChild(typingDiv);

                // Save the session ID
                if (data.session_id) {
                    sessionId = data.session_id;
                }

                // Add bot's response
                const botMessageDiv = document.createElement('div');
                botMessageDiv.className = 'message bot';
                botMessageDiv.innerHTML = `<div class="message-content">${data.message}</div>`;
                chatMessages.appendChild(botMessageDiv);

                // Display recommendations if present
                if (data.recommendations && data.recommendations.length > 0) {
                    const recsDiv = document.createElement('div');
                    recsDiv.className = 'recommendations';

                    let recsHTML = '<h4>Recommended Laptops:</h4><ul>';
                    data.recommendations.forEach(laptop => {
                        recsHTML += `<li><strong>${laptop.brand} ${laptop.name}</strong><br>Specs: ${laptop.specs}</li>`;
                    });
                    recsHTML += '</ul>';

                    recsDiv.innerHTML = recsHTML;
                    chatMessages.appendChild(recsDiv);
                }

                // Display next question if present
                if (data.next_question) {
                    const nextQuestionDiv = document.createElement('div');
                    nextQuestionDiv.className = 'message bot';
                    nextQuestionDiv.innerHTML = `<div class="message-content">${data.next_question}</div>`;
                    chatMessages.appendChild(nextQuestionDiv);
                }

                // Scroll to bottom of chat
                chatMessages.scrollTop = chatMessages.scrollHeight;
            })
            .catch(error => {
                // Remove typing indicator
                chatMessages.removeChild(typingDiv);

                // Show error message
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
                    // Clear chat messages
                    chatMessages.innerHTML = '';

                    // Add a system message indicating reset
                    const systemMessage = document.createElement('div');
                    systemMessage.className = 'message system';
                    systemMessage.innerHTML = `<div class="message-content">${data.message}</div>`;
                    chatMessages.appendChild(systemMessage);
                }
            })
            .catch(error => {
                console.error('Error resetting conversation:', error);
            });
    }

    // Event listeners for sending message
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

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

    // Close sidebar when pressing escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeSidebar();
        }
    });

    // Profile page functionality
    const profileLink = document.querySelector('.sidebar-nav li');

    // Make sure profileLink exists before adding event listener
    if (profileLink && profileContainer && closeProfileBtn) {
        // Open profile page when clicked in sidebar
        profileLink.addEventListener('click', () => {
            closeSidebar();

            // Hide other containers first
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

            // Show profile with fade-in effect
            setTimeout(() => {
                profileContainer.style.display = 'flex';
                setTimeout(() => {
                    profileContainer.classList.add('fade-in');
                }, 50);
            }, 500);
        });

        // Close profile when clicking close button
        closeProfileBtn.addEventListener('click', () => {
            profileContainer.classList.remove('fade-in');

            setTimeout(() => {
                profileContainer.style.display = 'none';

                // Return to chat if splash was already dismissed
                if (splashScreen.style.display === 'none') {
                    chatContainer.style.display = 'flex';
                    setTimeout(() => {
                        chatContainer.classList.add('fade-in');
                    }, 50);
                } else {
                    // Otherwise show splash
                    splashScreen.style.display = 'flex';
                    splashScreen.classList.remove('fade-out');
                }
            }, 800);
        });
    }

    // Save profile changes button (if exists)
    const profileSaveBtn = document.querySelector('.profile-save-btn');
    if (profileSaveBtn) {
        profileSaveBtn.addEventListener('click', () => {
            const originalText = profileSaveBtn.textContent;
            profileSaveBtn.textContent = 'Saved!';
            profileSaveBtn.disabled = true;

            setTimeout(() => {
                profileSaveBtn.textContent = originalText;
                profileSaveBtn.disabled = false;
            }, 2000);
        });
    }
});
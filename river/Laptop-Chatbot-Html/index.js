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
    chatContainer.appendChild(laptopDetailsPanel);

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

    function showLaptopDetails(laptop) {
        const content = laptopDetailsPanel.querySelector('.laptop-details-content');
        content.innerHTML = `
        <div class="laptop-spec">
            <div class="laptop-spec-label">Model</div>
            <div class="laptop-spec-value">${laptop.brand} ${laptop.name}</div>
        </div>
        <div class="laptop-spec">
            <div class="laptop-spec-label">Specifications</div>
            <div class="laptop-spec-value">${laptop.specs}</div>
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
    `;
        laptopDetailsPanel.classList.add('open');
        chatContainer.classList.add('shifted');
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

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeSidebar();
            laptopDetailsPanel.classList.remove('open');
            chatContainer.classList.remove('shifted');
        }
    });

    // Profile functionality
    const profileLink = document.querySelector('.sidebar-nav li');

    if (profileLink && profileContainer && closeProfileBtn) {
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

            setTimeout(() => {
                profileContainer.style.display = 'flex';
                setTimeout(() => {
                    profileContainer.classList.add('fade-in');
                }, 50);
            }, 500);
        });

        closeProfileBtn.addEventListener('click', () => {
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
        });
    }

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
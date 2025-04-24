document.addEventListener('DOMContentLoaded', () => {
    const splashScreen = document.getElementById('splash-screen');
    const chatContainer = document.getElementById('chat-container');
    const startChatBtn = document.getElementById('start-chat-btn');
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const themeToggleCheckbox = document.getElementById('theme-toggle-checkbox');

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

    // Show chat interface when start button is clicked
    startChatBtn.addEventListener('click', () => {
        // Add fade-out class to splash screen
        splashScreen.classList.add('fade-out');

        // Display chat container but keep it invisible for animation
        chatContainer.style.display = 'flex';

        // Small delay before starting the fade-in animation
        setTimeout(() => {
            chatContainer.classList.add('fade-in');
        }, 100);

        // Hide splash screen after transition completes
        setTimeout(() => {
            splashScreen.style.display = 'none';
            userInput.focus();
        }, 800);
    });

    // Function to add a new message to the chat
    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = content;

        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);

        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to show typing indicator
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message bot';
        typingDiv.id = 'typing-indicator';

        const typingContent = document.createElement('div');
        typingContent.className = 'typing-indicator';

        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            dot.className = 'typing-dot';
            typingContent.appendChild(dot);
        }

        typingDiv.appendChild(typingContent);
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return typingDiv;
    }

    // Function to remove typing indicator
    function removeTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    // Function to send a message to backend
    async function sendToLLM(message) {
        // Here you would make an API call to your Python LLM backend
        // For now, we'll simulate a response

        const typingIndicator = showTypingIndicator();

        try {
            // Simulating API call delay - replace with actual fetch to your Python backend
            await new Promise(resolve => setTimeout(resolve, 1500));

            // Mock responses for demonstration
            const responses = [
                "Based on your requirements, I'd recommend a laptop with at least 16GB RAM and an i7 processor.",
                "For your budget range, consider the Dell XPS 13 or MacBook Air M1.",
                "If you need a laptop for gaming, look for models with dedicated graphics like NVIDIA GTX or RTX series.",
                "For programming and development, I recommend laptops with SSD storage and at least 16GB RAM.",
                "If portability is important, ultrabooks like the LG Gram or Microsoft Surface might be good options."
            ];

            const response = responses[Math.floor(Math.random() * responses.length)];

            // In a real implementation, replace with:
            // const response = await fetch('/api/llm', {
            //     method: 'POST',
            //     headers: { 'Content-Type': 'application/json' },
            //     body: JSON.stringify({ message })
            // }).then(res => res.json()).then(data => data.response);

            removeTypingIndicator();
            addMessage(response);

        } catch (error) {
            console.error('Error:', error);
            removeTypingIndicator();
            addMessage("Sorry, I'm having trouble connecting to the recommendation service. Please try again later.");
        }
    }

    // Event handler for sending messages
    function handleSendMessage() {
        const message = userInput.value.trim();

        if (message) {
            addMessage(message, true);
            userInput.value = '';

            sendToLLM(message);
        }
    }

    // Event listeners
    sendBtn.addEventListener('click', handleSendMessage);

    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSendMessage();
        }
    });
});
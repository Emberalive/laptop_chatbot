export default defineEventHandler(async (event) => {
    const body = await readBody(event);

    try {
        const userMessage = body.message;
        const sessionId = body.session_id || null;

        const response = await $fetch('http://localhost:8000/api/chat', {
            method: 'POST',
            body: JSON.stringify({
                message: userMessage,
                session_id: sessionId
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // Handle the response properly
        return {
            // If message is an array, pass it through, otherwise wrap it
            messages: Array.isArray(response.messages) ? response.messages :
                [(response.message || response.response || "No response content")],
            recommendations: response.recommendations || response._get_recommendations || [],
            session_id: response.session_id || sessionId
        };
    } catch (error) {
        console.error('Error calling chatbot API:', error);
        return {
            messages: ["I'm having trouble connecting to my knowledge base. Please try again later."],
            recommendations: []
        };
    }
});
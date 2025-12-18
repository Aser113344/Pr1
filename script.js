document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const typingIndicator = document.getElementById('typing-indicator');

    function appendMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        messageDiv.textContent = content;
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function showTypingIndicator() {
        typingIndicator.style.display = 'block';
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    function hideTypingIndicator() {
        typingIndicator.style.display = 'none';
    }

    async function queryAI(userMessage) {
        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: userMessage
                })
            });

            if (!response.ok) {
                throw new Error("Server Error");
            }

            const data = await response.json();
            return data.reply || "مفيش رد من الذكاء الاصطناعي";

        } catch (error) {
            console.error(error);
            return "حصل خطأ في السيرفر، حاول تاني";
        }
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const userText = userInput.value.trim();
        if (!userText) return;

        appendMessage(userText, 'user');
        userInput.value = '';
        showTypingIndicator();

        const aiReply = await queryAI(userText);

        hideTypingIndicator();
        appendMessage(aiReply, 'ai');
    });
});
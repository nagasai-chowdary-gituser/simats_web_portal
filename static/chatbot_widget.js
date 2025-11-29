(function () {
    // Create launcher button
    const launcher = document.createElement("button");
    launcher.id = "chatbot-launcher";
    launcher.innerHTML = '<img src="/static/bot_logo1.png" class="bot-icon">';
    document.body.appendChild(launcher);

    // Create chat window
    const chatWindow = document.createElement("div");
    chatWindow.id = "chatbot-window";
    chatWindow.innerHTML = `
        <div id="chatbot-header">
            <div>
                SIM-BOT <br/>
                <span>Ask anything about your college</span>
            </div>
            <div id="chatbot-close">✕</div>
        </div>
        <div id="chatbot-messages"></div>
        <div id="chatbot-input-area">
            <input id="chatbot-input" type="text" placeholder="Type your question..." />
            <button id="chatbot-send">➤</button>
        </div>
    `;
    document.body.appendChild(chatWindow);

    const messagesDiv = chatWindow.querySelector("#chatbot-messages");
    const inputEl = chatWindow.querySelector("#chatbot-input");
    const sendBtn = chatWindow.querySelector("#chatbot-send");
    const closeBtn = chatWindow.querySelector("#chatbot-close");

    let userId = "web_user_" + Math.random().toString(36).slice(2);

    function addMessage(text, isUser) {
        const div = document.createElement("div");
        div.className = "chat-msg " + (isUser ? "chat-user" : "chat-bot");
        div.textContent = text;
        messagesDiv.appendChild(div);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    async function sendMessage() {
        const text = inputEl.value.trim();
        if (!text) return;

        addMessage(text, true);
        inputEl.value = "";

        addMessage("Typing...", false);
        const loadingBubble = messagesDiv.lastChild;

        try {
            const res = await fetch("/chatbot-ask", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    message: text,
                    agentic: true,
                    userId: userId
                })
            });

            const data = await res.json();
            loadingBubble.remove();
            addMessage(data.answer || "No response.", false);
        } catch (err) {
            loadingBubble.remove();
            addMessage("⚠️ Error talking to server.", false);
            console.error(err);
        }
    }

    launcher.addEventListener("click", () => {
        chatWindow.style.display = "flex";
    });

    closeBtn.addEventListener("click", () => {
        chatWindow.style.display = "none";
    });

    sendBtn.addEventListener("click", sendMessage);
    inputEl.addEventListener("keydown", (e) => {
        if (e.key === "Enter") sendMessage();
    });
})();

document.addEventListener('DOMContentLoaded', () => {
    const buildKbBtn = document.getElementById('build-kb-btn');
    const analyzePrescriptionBtn = document.getElementById('analyze-prescription-btn');
    const sendChatBtn = document.getElementById('send-chat-btn');
    const chatMessages = document.getElementById('chat-messages');
    const chatInput = document.getElementById('chat-input');
    const logContent = document.getElementById('log-content');
    const summaryContent = document.getElementById('summary-content');

    console.log('DOM fully loaded and parsed');

    function addToLog(message) {
        console.log('Adding to log:', message);
        const logEntry = document.createElement('div');
        logEntry.textContent = `${new Date().toLocaleTimeString()}: ${message}`;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    function displaySummary(summary) {
        console.log('Displaying summary');
        summaryContent.innerHTML = summary;
    }

    buildKbBtn.addEventListener('click', async () => {
        console.log('Build KB button clicked');
        // Reset summary and chat windows
        summaryContent.innerHTML = '<p>Building knowledge base...</p>';
        chatMessages.innerHTML = ''; // Clear chat messages
        addToLog('Building knowledge base...');
        showLoading('build-kb-btn');

        const query = document.getElementById('query-input').value;
        const sources = Array.from(document.querySelectorAll('input[name="source"]:checked')).map(el => el.value);
        const pdfFile = document.getElementById('pdf-upload').files[0];

        console.log('Query:', query);
        console.log('Sources:', sources);
        console.log('PDF File:', pdfFile ? pdfFile.name : 'None');

        const formData = new FormData();
        formData.append('query', query);
        sources.forEach(source => formData.append('sources', source));
        if (pdfFile) {
            formData.append('pdf', pdfFile);
        }

        try {
            console.log('Sending request to build KB');
            const response = await fetch('/api/build_kb', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            console.log('Response received:', data);
            if (response.ok) {
                addToLog(`Knowledge base built successfully. Articles reviewed: ${data.articles_reviewed}`);
                displaySummary(data.summary);
            } else {
                addToLog(`Error: ${data.error}`);
                summaryContent.innerHTML = `<p>Error: ${data.error}</p>`;
            }
        } catch (error) {
            console.error('Error building knowledge base:', error);
            addToLog('Error building knowledge base. Please try again.');
            summaryContent.innerHTML = '<p>Error building knowledge base. Please try again.</p>';
        } finally {
            hideLoading('build-kb-btn', 'Build Knowledge Base');
        }
    });

    analyzePrescriptionBtn.addEventListener('click', async () => {
        console.log('Analyze Prescription button clicked');
        const prescriptionFile = document.getElementById('prescription-upload').files[0];
        if (!prescriptionFile) {
            addToLog('Error: No prescription image selected.');
            return;
        }

        showLoading('analyze-prescription-btn');
        const formData = new FormData();
        formData.append('prescription', prescriptionFile);

        try {
            const response = await fetch('/api/analyze_prescription', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (response.ok) {
                addToLog('Prescription analysis complete');
                summaryContent.innerHTML = `<h2>Prescription Analysis</h2>${data.result}`;
            } else {
                addToLog(`Error: ${data.error}`);
                summaryContent.innerHTML = `<p>Error: ${data.error}</p>`;
            }
        } catch (error) {
            console.error('Error analyzing prescription:', error);
            addToLog('Error analyzing prescription. Please try again.');
            summaryContent.innerHTML = '<p>Error analyzing prescription. Please try again.</p>';
        } finally {
            hideLoading('analyze-prescription-btn', 'Analyze Prescription');
        }
    });

    sendChatBtn.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });

    async function sendChatMessage() {
        const message = chatInput.value.trim();
        if (!message) return;
    
        addMessageToChat('You', message);
        chatInput.value = '';
        showLoading('send-chat-btn');
    
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            const data = await response.json();
            if (response.ok) {
                const assistantMessage = document.createElement('div');
                assistantMessage.className = 'chat-message assistant';
                // Convert double asterisks to bold HTML tags
                assistantMessage.innerHTML = data.response.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                chatMessages.appendChild(assistantMessage);
            } else {
                addMessageToChat('Assistant', `Error: ${data.error}`);
            }
        } catch (error) {
            console.error('Error sending chat message:', error);
            addMessageToChat('Assistant', 'Error: Unable to get a response. Please try again.');
        } finally {
            hideLoading('send-chat-btn', 'Send');
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }

    function showLoading(elementId) {
        const element = document.getElementById(elementId);
        element.disabled = true;
        element.innerHTML = '<span class="spinner"></span> Processing...';
    }
    
    function hideLoading(elementId, originalText) {
        const element = document.getElementById(elementId);
        element.disabled = false;
        element.innerHTML = originalText;
    }

    function addMessageToChat(sender, message) {
        const messageElement = document.createElement('div');
        messageElement.className = `chat-message ${sender.toLowerCase()}`;
        messageElement.innerHTML = `<strong>${sender}:</strong> ${message}`;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
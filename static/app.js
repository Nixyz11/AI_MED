// Web Speech API setup
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = SpeechRecognition ? new SpeechRecognition() : null;

// Speech synthesis
const synth = window.speechSynthesis;

// DOM elements
const voiceButton = document.getElementById('voiceButton');
const textInput = document.getElementById('textInput');
const sendButton = document.getElementById('sendButton');
const conversation = document.getElementById('conversation');
const resetButton = document.getElementById('resetButton');
const toggleModeButton = document.getElementById('toggleModeButton');
const listeningIndicator = document.getElementById('listeningIndicator');
const loadingOverlay = document.getElementById('loadingOverlay');
const errorToast = document.getElementById('errorToast');
const errorMessage = document.getElementById('errorMessage');
const statusIndicator = document.getElementById('status-indicator');
const statusText = document.getElementById('status-text');

// State
let isListening = false;
let isSpeaking = false;
let voiceMode = true;
let recognitionStarted = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    // Check system status
    checkStatus();

    // Configure speech recognition
    if (recognition) {
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
            isListening = true;
            voiceButton.classList.add('listening');
            listeningIndicator.classList.add('active');
            voiceButton.querySelector('.button-text').textContent = 'Listening...';
        };

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            console.log('Recognized:', transcript);
            handleUserMessage(transcript);
        };

        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            if (event.error !== 'no-speech') {
                showError(`Speech recognition error: ${event.error}`);
            }
            stopListening();
        };

        recognition.onend = () => {
            stopListening();
        };

        voiceButton.disabled = false;
    } else {
        showError('Speech recognition not supported in this browser');
        voiceMode = false;
    }

    // Event listeners
    voiceButton.addEventListener('mousedown', startListening);
    voiceButton.addEventListener('mouseup', () => {
        if (recognition && recognitionStarted) {
            recognition.stop();
        }
    });
    voiceButton.addEventListener('touchstart', startListening);
    voiceButton.addEventListener('touchend', () => {
        if (recognition && recognitionStarted) {
            recognition.stop();
        }
    });

    sendButton.addEventListener('click', () => {
        const message = textInput.value.trim();
        if (message) {
            handleUserMessage(message);
            textInput.value = '';
        }
    });

    textInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const message = textInput.value.trim();
            if (message) {
                handleUserMessage(message);
                textInput.value = '';
            }
        }
    });

    resetButton.addEventListener('click', resetConversation);
    toggleModeButton.addEventListener('click', toggleMode);
}

function startListening() {
    if (!recognition || isListening || isSpeaking) return;

    try {
        recognition.start();
        recognitionStarted = true;
    } catch (error) {
        console.error('Error starting recognition:', error);
        showError('Could not start voice recognition');
    }
}

function stopListening() {
    isListening = false;
    recognitionStarted = false;
    voiceButton.classList.remove('listening');
    listeningIndicator.classList.remove('active');
    voiceButton.querySelector('.button-text').textContent = 'Press and Hold to Speak';
}

async function handleUserMessage(message) {
    // Add user message to UI
    addMessage('user', message);

    // Show loading
    showLoading(true);

    try {
        // Send to backend
        const response = await fetch('/api/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();

        // Add assistant response to UI
        addMessage('assistant', data.response, data.intent);

        // Speak response if in voice mode
        if (voiceMode) {
            speak(data.response);
        }

    } catch (error) {
        console.error('Error:', error);
        showError('Failed to process message. Please try again.');
        addMessage('assistant', "I apologize, I'm having trouble processing your request. Please try again.");
    } finally {
        showLoading(false);
    }
}

function addMessage(role, text, intent = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    const label = document.createElement('strong');
    label.textContent = role === 'user' ? 'You:' : 'Assistant:';

    const textP = document.createElement('p');
    textP.textContent = text;

    contentDiv.appendChild(label);
    contentDiv.appendChild(textP);

    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });

    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);

    conversation.appendChild(messageDiv);
    conversation.scrollTop = conversation.scrollHeight;
}

function speak(text) {
    if (!synth) return;

    // Cancel any ongoing speech
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Get a pleasant voice (prefer female voice if available)
    const voices = synth.getVoices();
    const femaleVoice = voices.find(voice => 
        voice.name.includes('Female') || 
        voice.name.includes('Samantha') ||
        voice.name.includes('Google US English')
    );
    if (femaleVoice) {
        utterance.voice = femaleVoice;
    }

    utterance.onstart = () => {
        isSpeaking = true;
        voiceButton.disabled = true;
    };

    utterance.onend = () => {
        isSpeaking = false;
        voiceButton.disabled = false;
    };

    utterance.onerror = (error) => {
        console.error('Speech synthesis error:', error);
        isSpeaking = false;
        voiceButton.disabled = false;
    };

    synth.speak(utterance);
}

async function resetConversation() {
    if (!confirm('Start a new conversation? This will clear the current chat.')) {
        return;
    }

    try {
        const response = await fetch('/api/reset', {
            method: 'POST'
        });

        if (response.ok) {
            // Clear conversation UI
            conversation.innerHTML = '';
            
            // Add welcome message
            addMessage('assistant', 'Hello! Welcome to MedClinic. How may I assist you today?');
            
            if (voiceMode) {
                speak('Hello! Welcome to MedClinic. How may I assist you today?');
            }
        }
    } catch (error) {
        console.error('Error resetting conversation:', error);
        showError('Failed to reset conversation');
    }
}

function toggleMode() {
    voiceMode = !voiceMode;
    toggleModeButton.textContent = voiceMode ? '🎤 Voice Mode' : '⌨️ Text Mode';
    
    if (voiceMode && synth) {
        // Announcement
        const msg = new SpeechSynthesisUtterance('Voice mode enabled');
        synth.speak(msg);
    }
}

async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        if (data.ollama_available) {
            statusIndicator.classList.remove('offline');
            statusText.textContent = `Connected (${data.model})`;
        } else {
            statusIndicator.classList.add('offline');
            statusText.textContent = 'Ollama Offline (Rule-based)';
        }
    } catch (error) {
        statusIndicator.classList.add('offline');
        statusText.textContent = 'Connection Error';
        showError('Cannot connect to server. Please check if the server is running.');
    }
}

function showLoading(show) {
    if (show) {
        loadingOverlay.classList.remove('hidden');
    } else {
        loadingOverlay.classList.add('hidden');
    }
}

function showError(message) {
    errorMessage.textContent = message;
    errorToast.classList.remove('hidden');

    setTimeout(() => {
        hideError();
    }, 5000);
}

function hideError() {
    errorToast.classList.add('hidden');
}

// Load voices (for speech synthesis)
if (synth) {
    // Chrome loads voices asynchronously
    speechSynthesis.onvoiceschanged = () => {
        console.log('Voices loaded:', speechSynthesis.getVoices().length);
    };
}

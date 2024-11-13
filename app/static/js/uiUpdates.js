/**
 * @file uiUpdates.js
 * @description Manages UI updates for the Atlas application chat interface.
 *
 * This module provides functions for displaying and updating various types of messages,
 * including chat messages, macro scripts, error messages, and loading indicators.
 * It also handles scrolling, UI element management, and streaming content updates.
 */

/**
 * Creates a new message bubble in the chat log.
 * @param {string} sender - The sender of the message.
 * @param {string} section - The section type of the message.
 * @returns {HTMLElement} The newly created message bubble.
 */
export function createNewMessageBubble(sender, section) {
    const chatLog = document.getElementById('chat-log');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${section.includes('user-input') ? 'user-input-bubble' : 'output-bubble'}`;
    messageDiv.setAttribute('data-section', section);
    messageDiv.innerHTML = `<span>${sender}: </span><div class="message-content"></div>`;
    chatLog.appendChild(messageDiv);
    scrollChatToBottom();
    return messageDiv;
}

/**
 * Updates or creates a chat message in the chat log.
 * @param {string} sender - The sender of the message.
 * @param {string} message - The message content.
 * @param {string} section - The section type of the message.
 * @param {boolean} isStreaming - Whether the content is being streamed.
 */
export function updateChatMessage(sender, message, section, isStreaming = false) {
    const chatLog = document.getElementById('chat-log');
    let messageDiv = chatLog.querySelector(`.chat-message[data-section="${section}"]`);

    if (!messageDiv) {
        messageDiv = createNewMessageBubble(sender, section);
    }

    const contentDiv = messageDiv.querySelector('.message-content');
    contentDiv.textContent = message;

    if (isStreaming) {
        contentDiv.classList.add('streaming-content');
    } else {
        contentDiv.classList.remove('streaming-content');
    }

    scrollChatToBottom();
}

/**
 * Updates or creates the macro script window in the chat log.
 * Applies syntax highlighting and sets up copy and paste buttons.
 * @param {string} script - The macro script content.
 * @param {boolean} isStreaming - Whether the content is being streamed.
 * @param {string} section - The section identifier for the macro script.
 */
export function updateMacroScript(script, isStreaming = false, section = 'macro_script') {
    const chatLog = document.getElementById('chat-log');
    let scriptDiv = chatLog.querySelector(`.macro-script-window[data-section="${section}"]`);

    if (!scriptDiv) {
        scriptDiv = createMacroScriptWindow(section);
        chatLog.appendChild(scriptDiv);
    }

    const codeElement = scriptDiv.querySelector('code');
    codeElement.textContent = script;

    if (typeof hljs !== 'undefined') {
        hljs.highlightElement(codeElement);
    }

    setupMacroScriptButtons(scriptDiv, script);
    scrollChatToBottom();
}

/**
 * Creates the macro script window element and sets up its structure.
 * @param {string} section - The section identifier for the macro script window.
 * @returns {HTMLElement} The created macro script window element.
 */
function createMacroScriptWindow(section) {
    const scriptDiv = document.createElement('div');
    scriptDiv.className = 'macro-script-window';
    scriptDiv.setAttribute('data-section', section);
    scriptDiv.innerHTML = `
        <div class="macro-script-header">Macro Script</div>
        <pre class="macro-script-content"><code class="language-javascript"></code></pre>
        <div class="macro-script-actions">
            <button class="copy-btn">Copy</button>
            <button class="paste-btn">Paste</button>
        </div>
    `;
    return scriptDiv;
}

/**
 * Sets up the copy and paste buttons for the macro script interface.
 * @param {HTMLElement} scriptDiv - The macro script window element.
 * @param {string} script - The macro script content.
 */
function setupMacroScriptButtons(scriptDiv, script) {
    const copyBtn = scriptDiv.querySelector('.copy-btn');
    const pasteBtn = scriptDiv.querySelector('.paste-btn');

    copyBtn.onclick = () => copyToClipboard(script, 'Macro script copied to clipboard.');
    pasteBtn.onclick = () => pasteToMacroEditor(script);
}




/**
 * Copies the given text to clipboard.
 * @param {string} text - The text to copy.
 * @param {string} successMessage - The message to display on successful copy.
 */
function copyToClipboard(text, successMessage) {
    navigator.clipboard.writeText(text).then(() => {
        displaySuccessMessage(successMessage);
    }).catch(err => {
        displayErrorMessage('Failed to copy the macro script.');
        console.error('Error copying to clipboard:', err);
    });
}

/**
 * Pastes the given script into the macro editor textarea.
 * @param {string} script - The script to paste.
 */
function pasteToMacroEditor(script) {
    const macroScriptTextarea = document.getElementById('macro_script');
    if (macroScriptTextarea) {
        macroScriptTextarea.value = script;
        macroScriptTextarea.dispatchEvent(new Event('input'));
        displaySuccessMessage('Macro script pasted into the editor.');
    } else {
        displayErrorMessage('Unable to paste the macro script into the interface.');
    }
}

/**
 * Scrolls the chat log to the bottom to ensure the latest content is visible.
 */
export function scrollChatToBottom() {
    const chatLog = document.getElementById('chat-log');
    chatLog.scrollTop = chatLog.scrollHeight;
}

/**
 * Displays an error message in the chat log.
 * @param {string} message - The error message to display.
 */
export function displayErrorMessage(message) {
    displayMessage(message, 'error-message');
}

/**
 * Displays a success message in the chat log.
 * @param {string} message - The success message to display.
 */
export function displaySuccessMessage(message) {
    displayMessage(message, 'success-message');
}

/**
 * Displays a message in the chat log with a specific class.
 * @param {string} message - The message to display.
 * @param {string} className - The CSS class for styling the message.
 */
function displayMessage(message, className) {
    const chatLog = document.getElementById('chat-log');
    const messageDiv = document.createElement('div');
    messageDiv.className = className;
    messageDiv.textContent = message;
    chatLog.appendChild(messageDiv);
    scrollChatToBottom();
    setTimeout(() => messageDiv.remove(), 5000);
}

/**
 * Shows the loading indicator in the chat log.
 */
export function showLoadingIndicator() {
    const chatLog = document.getElementById('chat-log');
    let loadingDiv = chatLog.querySelector('.loading-indicator');
    if (!loadingDiv) {
        loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading-indicator';
        loadingDiv.textContent = 'Generating...';
        chatLog.appendChild(loadingDiv);
    }
    scrollChatToBottom();
}

/**
 * Hides the loading indicator in the chat log.
 */
export function hideLoadingIndicator() {
    const loadingDiv = document.querySelector('.loading-indicator');
    if (loadingDiv) loadingDiv.remove();
}

/**
 * Updates the input area with streamed content.
 * @param {string} content - The content to update the input area with.
 */
export function updateInputArea(content) {
    const userInput = document.getElementById('user-input');
    userInput.value = content;
    adjustTextareaHeight(userInput);
}

/**
 * Adjusts the height of the textarea to fit the content.
 * @param {HTMLTextAreaElement} textarea - The textarea element to adjust.
 */
export function adjustTextareaHeight(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
}


/**
 * Displays structured results or additional information in the chat log.
 * @param {Object|string} data - The data to display. Can be an object or a string.
 * @param {string} [title='Results'] - Optional title for the results section.
 */
export function displayResults(data, title = 'Results') {
    const chatLog = document.getElementById('chat-log');
    const resultsDiv = document.createElement('div');
    resultsDiv.className = 'results-message output-bubble';

    let content = '';
    if (typeof data === 'object') {
        content = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    } else {
        content = `<p>${data}</p>`;
    }

    resultsDiv.innerHTML = `
        <div class="results-header">${title}</div>
        <div class="results-content">${content}</div>
    `;

    chatLog.appendChild(resultsDiv);
    scrollChatToBottom();
}

/**
 * @file chatInterface.js
 * @description Manages the chat interface for the Atlas application.
 *
 * This module provides a ChatInterface class that handles user interactions,
 * prompt improvements, and macro generation. It offers a dynamic and responsive
 * interface for real-time communication with the AI.
 *
 * @module chatInterface
 * @requires apiCalls
 * @requires uiUpdates
 * @requires utils
 */

import { generateMacro, generateImprovedPrompt } from './apiCalls.js';
import {
    updateChatMessage,
    scrollChatToBottom,
    updateMacroScript,
    displayErrorMessage,
    displaySuccessMessage,
    showLoadingIndicator,
    hideLoadingIndicator,
    updateInputArea,
} from './uiUpdates.js';
import { adjustTextareaHeight } from './utils.js';

/**
 * @class ChatInterface
 * @description Manages the chat interface and user interactions.
 */
export default class ChatInterface {
    /**
     * @constructor
     * @param {Object} sidebar - The sidebar instance for managing UI updates.
     */
    constructor(sidebar) {
        this.sidebar = sidebar;
        this.userInput = document.getElementById('user-input');
        this.chatForm = document.getElementById('chat-form');
        this.chatSubmitBtn = document.getElementById('chat-submit-btn');
        this.improvePromptCheckbox = document.getElementById('improve-prompt');

        this.currentSection = '';
        this.accumulatedContent = {};
        this.isImprovedPromptGenerated = false;

        // Property to keep track of the conversation index
        this.conversationIndex = 0;

        this.initializeEventListeners();
    }

    /**
     * @method initializeEventListeners
     * @description Sets up event listeners and initializes the chat interface.
     */
    initializeEventListeners() {
        this.userInput.addEventListener('input', () => adjustTextareaHeight(this.userInput));
        this.chatForm.addEventListener('submit', (e) => this.submitChat(e));
        this.chatSubmitBtn.addEventListener('click', (e) => this.submitChat(e));
        this.userInput.addEventListener('keydown', (e) => this.handleEnterKey(e));
    }

    /**
     * @method submitChat
     * @async
     * @description Handles form submission for chat messages.
     * @param {Event} e - The form submit event.
     */
    async submitChat(e) {
        e.preventDefault();
        const userInputValue = this.userInput.value.trim();
        const shouldImprovePrompt = this.improvePromptCheckbox.checked;

        if (!userInputValue) return;

        try {
            if (shouldImprovePrompt && !this.isImprovedPromptGenerated) {
                // User wants to improve the prompt and we haven't done it yet
                showLoadingIndicator();
                await this.handleImprovedPromptStreaming(userInputValue);
                hideLoadingIndicator();
                // Now, the improved prompt is in the input box, and the user can edit it
                // Set isImprovedPromptGenerated to true, so that next time we know we've improved it
                this.isImprovedPromptGenerated = true;
            } else {
                // Proceed with macro generation
                showLoadingIndicator();
                // Increment the conversation index
                this.conversationIndex += 1;

                // Use the conversation index to ensure messages are appended to the bottom
                const userMessageSection = `user-input-${this.conversationIndex}`;
                updateChatMessage('You', userInputValue, userMessageSection);

                await this.handleMacroGeneration(userInputValue, this.isImprovedPromptGenerated);

                displaySuccessMessage('Macro generated successfully.');
                // Reset the flag
                this.isImprovedPromptGenerated = false;
                this.improvePromptCheckbox.checked = false;
                // Clear the input
                this.userInput.value = '';
                adjustTextareaHeight(this.userInput);
            }
        } catch (error) {
            console.error('Error in chat submission:', error);
            displayErrorMessage('An error occurred: ' + error.message);
        } finally {
            hideLoadingIndicator();
        }
    }

    /**
     * @method handleEnterKey
     * @description Handles the Enter key press in the input area.
     * @param {KeyboardEvent} e - The keyboard event.
     */
    handleEnterKey(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.submitChat(e);
        }
    }

    /**
     * @method handleImprovedPromptStreaming
     * @async
     * @description Handles the streaming of improved prompts.
     * @param {string} input - The original user input.
     */
    async handleImprovedPromptStreaming(input) {
        this.accumulatedContent = { improved_prompt: '' };
        const eventSource = generateImprovedPrompt(input);

        return new Promise((resolve, reject) => {
            eventSource.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.event === 'improved_prompt_chunk') {
                    this.accumulatedContent.improved_prompt += data.data.chunk;
                    updateInputArea(this.accumulatedContent.improved_prompt);
                } else if (data.event === 'improved_prompt_complete') {
                    eventSource.close();
                    this.isImprovedPromptGenerated = true;
                    this.improvePromptCheckbox.checked = false;
                    // The improved prompt is now in the input area
                    // The user can edit it and decide whether to submit
                    resolve();
                }
            };

            eventSource.onerror = (error) => {
                console.error('Error in EventSource:', error);
                eventSource.close();
                displayErrorMessage('Failed to improve prompt. Please try again or proceed with the original input.');
                this.isImprovedPromptGenerated = false;
                this.improvePromptCheckbox.checked = false;
                reject(error);
            };
        });
    }

    /**
     * @method handleMacroGeneration
     * @async
     * @description Initiates macro generation using the provided prompt.
     * @param {string} prompt - The final prompt for macro generation.
     * @param {boolean} improvedPrompt - Whether the prompt was improved.
     */
    async handleMacroGeneration(prompt, improvedPrompt) {
        try {
            const eventSource = await generateMacro(prompt, improvedPrompt);

            return new Promise((resolve, reject) => {
                eventSource.onmessage = async (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        await this.handleStreamedContent(data, this.conversationIndex);
                        if (data.event === 'complete') {
                            eventSource.close();
                            resolve();
                        }
                    } catch (error) {
                        eventSource.close();
                        reject(error);
                    }
                };

                eventSource.onerror = (error) => {
                    eventSource.close();
                    reject(new Error(error.status === 401 ?
                        'Authentication failed. Please check your credentials.' :
                        'An error occurred during macro generation.'));
                };
            });
        } catch (error) {
            throw new Error(`Failed to initialize macro generation: ${error.message}`);
        }
    }
    /**
     * @method handleStreamedContent
     * @async
     * @description Processes streamed content based on the event type and updates the UI accordingly.
     * @param {Object} data - The data object containing event and content details.
     * @param {number} interactionId - The unique interaction ID for this conversation.
     */
    async handleStreamedContent(data, interactionId) {
        switch (data.event) {
            case 'section_change':
                this.handleSectionChange(data.data, interactionId);
                break;
            case 'message':
                await this.updateStreamingContent(data.data.section, data.data.content, interactionId);
                break;
            case 'complete':
                this.finalizeSectionContent(interactionId);
                const systemMessageSection = `system-${interactionId}`;
                updateChatMessage('System', 'Macro generation complete.', systemMessageSection);
                break;
            case 'error':
                displayErrorMessage(data.data.error);
                break;
            default:
                console.warn('Unknown event type:', data.event);
        }
        scrollChatToBottom();
    }

    /**
     * @method handleSectionChange
     * @description Handles section changes in the streamed content.
     * @param {Object} data - The section change data.
     * @param {number} interactionId - The unique interaction ID for this conversation.
     */
    handleSectionChange(data, interactionId) {
        this.finalizeSectionContent(interactionId);
        this.currentSection = data.section;
        this.accumulatedContent[this.currentSection] = '';

        // Update the current section with the interaction ID to ensure uniqueness
        this.currentSectionWithId = `${this.currentSection}-${interactionId}`;
    }

    /**
     * @method updateStreamingContent
     * @async
     * @description Updates the content within a section, handling accumulation and real-time updates.
     * @param {string} section - The section type being updated.
     * @param {string} content - The new content to add to the section.
     * @param {number} interactionId - The unique interaction ID for this conversation.
     */
    async updateStreamingContent(section, content, interactionId) {
        if (!this.accumulatedContent[section]) {
            this.accumulatedContent[section] = '';
        }

        this.accumulatedContent[section] += content;
        const cleanedContent = this.cleanContent(this.accumulatedContent[section], section);

        const sectionWithId = `${section}-${interactionId}`;

        if (section === 'macro_script') {
            updateMacroScript(cleanedContent, true, sectionWithId);
        } else if (section !== 'improved_prompt') {
            updateChatMessage('Atlas', cleanedContent, sectionWithId, true);
        }
    }

    /**
     * @method cleanContent
     * @description Cleans the content by removing specific tags.
     * @param {string} content - The raw content.
     * @param {string} section - The section type.
     * @returns {string} The cleaned content.
     */
    cleanContent(content, section) {
        let cleanContent = content.replace(/\[DESCRIPTION\]|\[EXPLANATION\]/gi, '').trim();
        if (section === 'macro_script') {
            const firstCodeIndex = cleanContent.indexOf('//');
            cleanContent = firstCodeIndex !== -1 ? cleanContent.slice(firstCodeIndex) : cleanContent;
        }
        return cleanContent;
    }

    /**
     * @method finalizeSectionContent
     * @description Finalizes content for the current section, ensuring no incomplete data remains.
     * @param {number} interactionId - The unique interaction ID for this conversation.
     */
    finalizeSectionContent(interactionId) {
        if (this.currentSection && this.accumulatedContent[this.currentSection]) {
            const cleanedContent = this.cleanContent(this.accumulatedContent[this.currentSection], this.currentSection);

            const sectionWithId = `${this.currentSection}-${interactionId}`;

            if (this.currentSection === 'macro_script') {
                updateMacroScript(cleanedContent, false, sectionWithId);
            } else {
                updateChatMessage('Atlas', cleanedContent, sectionWithId, false);
            }
        }
    }
}

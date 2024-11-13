/**
 * @file eventListeners.js
 * @description Sets up event listeners for the Atlas application.
 *
 * This module provides a function to initialize all event listeners,
 * ensuring that elements are properly referenced and handlers are correctly bound.
 *
 * @module eventListeners
 */

/**
 * Sets up event listeners for the application.
 * @param {Sidebar} sidebar - The sidebar instance.
 * @param {FileHandler} fileHandling - The file handling instance.
 * @param {ChatInterface} chatInterface - The chat interface instance.
 * @param {MacroScriptInterface} macroScriptInterface - The macro script interface instance.
 */
export function setupEventListeners(sidebar, fileHandling, chatInterface, macroScriptInterface) {
    // Helper function to safely add event listeners
    function addListener(id, event, handler) {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener(event, handler);
        } else {
            console.warn(`Element with ID '${id}' not found.`);
        }
    }

    // Ensure the DOM is fully loaded before setting up event listeners
    document.addEventListener('DOMContentLoaded', () => {
        // Chat form submission
        addListener('chat-form', 'submit', (e) => chatInterface.submitChat(e));

        // Image upload form submission
        addListener('image-upload-form', 'submit', (e) => macroScriptInterface.submitImageUpload(e));

        // Attach buttons
        addListener('attach-btn', 'click', () => document.getElementById('chat-file-input')?.click());
        addListener('macro-attach-btn', 'click', () => document.getElementById('images')?.click());

        // File inputs change events
        addListener('chat-file-input', 'change', function () {
            fileHandling.handleFiles(this.files, 'chat');
        });

        addListener('images', 'change', function () {
            fileHandling.handleFiles(this.files, 'macro');
        });

        // Drop zone events
        const dropZone = document.getElementById('drop-zone');
        if (dropZone) {
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.classList.add('drag-over');
            });

            dropZone.addEventListener('dragleave', () => {
                dropZone.classList.remove('drag-over');
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.classList.remove('drag-over');
                fileHandling.handleFiles(e.dataTransfer.files, 'macro');
            });

            dropZone.addEventListener('click', () => document.getElementById('images')?.click());
        } else {
            console.warn('Drop zone element not found.');
        }
    });
}

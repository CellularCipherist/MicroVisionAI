/**
 * @file macroScriptInterface.js
 * @description Manages the macro script interface for the Atlas application.
 *
 * This module provides a MacroScriptInterface class that handles macro script
 * submissions, image uploads associated with macros, and result processing.
 *
 * @module macroScriptInterface
 * @requires apiCalls
 * @requires uiUpdates
 */

import { uploadImage } from './apiCalls.js';
import {
    displaySuccessMessage,
    displayErrorMessage,
    displayResults,
    showLoadingIndicator,
    hideLoadingIndicator,
} from './uiUpdates.js';

/**
 * @class MacroScriptInterface
 * @description Manages the macro script interface and associated image uploads.
 */
export class MacroScriptInterface {
    /**
     * @constructor
     * @param {Sidebar} sidebar - The sidebar instance for managing image previews.
     */
    constructor(sidebar) {
        this.sidebar = sidebar;
        this.macroScriptTextarea = document.getElementById('macro_script');
        this.uploadBtn = document.getElementById('upload-btn');

        this.initializeEventListeners();
    }

    /**
     * @method initializeEventListeners
     * @description Sets up event listeners for the macro script interface.
     */
    initializeEventListeners() {
        this.uploadBtn.addEventListener('click', (e) => this.submitImageUpload(e));
    }

    /**
     * @method stripFirstLine
     * @description Removes the first line of the script if it starts with 'ijm' or 'javascript'.
     * @param {string} script - The original macro script.
     * @returns {string} The script with the first line potentially removed.
     */
    stripFirstLine(script) {
        const lines = script.split('\n');
        const firstLine = lines[0].trim().toLowerCase();
        if (firstLine.startsWith('ijm') || firstLine.startsWith('javascript')) {
            return lines.slice(1).join('\n');
        }
        return script;
    }

    /**
     * @method submitImageUpload
     * @async
     * @description Handles the submission of images with associated macro scripts.
     * @param {Event} e - The event object from the submit button click.
     */
    async submitImageUpload(e) {
        e.preventDefault();

        // Get all files from the sidebar previews for the 'macro' context
        const previews = this.sidebar.getAllPreviews('macro');
        if (previews.length === 0) {
            displayErrorMessage('No images selected for processing.');
            return;
        }
        const files = previews.map(preview => preview.file);

        const macroScript = this.macroScriptTextarea.value.trim();
        if (!macroScript) {
            displayErrorMessage('Macro script cannot be empty.');
            return;
        }

        const strippedMacro = this.stripFirstLine(macroScript);

        try {
            showLoadingIndicator();

            const response = await uploadImage(files, true, strippedMacro);
            await this.processResponse(response);
        } catch (error) {
            console.error('Error:', error);
            displayErrorMessage('An error occurred while communicating with the server.');
        } finally {
            hideLoadingIndicator();
        }
    }

    /**
     * @method processResponse
     * @async
     * @description Processes the server response after image upload and macro execution.
     * @param {Object|Blob} response - The response from the server.
     */
    async processResponse(response) {
        if (response instanceof Blob) {
            await this.handleZipResponse(response);
        } else if (typeof response === 'object') {
            await this.handleJsonResponse(response);
        } else {
            console.error('Unexpected response type:', typeof response);
            displayErrorMessage('Received an unexpected response from the server.');
        }
    }

    /**
     * @method handleZipResponse
     * @async
     * @description Handles a ZIP file response from the server.
     * @param {Blob} blob - The Blob object containing the ZIP file.
     */
    async handleZipResponse(blob) {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'results.zip';
        document.body.appendChild(a);
        a.click();
        URL.revokeObjectURL(url);
        a.remove();
        displaySuccessMessage('Results downloaded successfully.');
    }

    /**
     * @method handleJsonResponse
     * @async
     * @description Handles a JSON response from the server.
     * @param {Object} data - The JSON data from the server.
     */
    async handleJsonResponse(data) {
        if (data.error) {
            displayErrorMessage(data.error);
        } else {
            displayResults(data);
            displaySuccessMessage('Macro executed successfully.');
        }
    }
}

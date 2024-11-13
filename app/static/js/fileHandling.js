/**
 * @file fileHandling.js
 * @description Manages file handling operations for the Atlas application.
 *
 * This module provides a FileHandler class that handles file uploads,
 * drag-and-drop functionality, and interaction with the sidebar for
 * displaying file previews.
 *
 * @module fileHandling
 * @requires apiCalls
 * @requires uiUpdates
 */

import { uploadImage } from './apiCalls.js';
import { displayErrorMessage, displaySuccessMessage } from './uiUpdates.js';

/**
 * @class FileHandler
 * @description Manages file handling operations and UI interactions for file uploads.
 */
export class FileHandler {
    /**
     * @constructor
     * @param {Object} sidebar - An object representing the sidebar module with methods to add and remove image previews.
     */
    constructor(sidebar) {
        this.sidebar = sidebar;
        this.dropZone = document.getElementById('drop-zone');
        this.macroFileInput = document.getElementById('images');
        this.chatFileInput = document.getElementById('chat-file-input');
        this.chatAttachBtn = document.getElementById('attach-btn');
        this.macroScriptInput = document.getElementById('macro_script');
        this.uploadBtn = document.getElementById('upload-btn');

        this.microscopySupportedExtensions = ['czi', 'lif', 'nd2', 'oib', 'oif', 'ome.tiff', 'ome.tif'];

        // New property to keep track of the processing runs
        this.processingRunCounter = 0;

        // Element to display download links
        this.resultsContainer = document.getElementById('results-container');

        this.initializeEventListeners();
    }

    /**
     * @method initializeEventListeners
     * @description Sets up event listeners for various file handling interactions.
     */
    initializeEventListeners() {
        this.uploadBtn.addEventListener('click', this.handleUploadButtonClick.bind(this));
        this.dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
        this.dropZone.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.dropZone.addEventListener('drop', this.handleDrop.bind(this));
        this.dropZone.addEventListener('click', () => this.macroFileInput.click());
        this.macroFileInput.addEventListener('change', (event) => this.handleFiles(event.target.files, 'macro'));
        this.chatAttachBtn.addEventListener('click', () => this.chatFileInput.click());
        this.chatFileInput.addEventListener('change', (event) => this.handleFiles(event.target.files, 'chat'));
    }

    /**
     * @method handleUploadButtonClick
     * @description Handles the click event for the upload button.
     * @param {Event} event - The click event triggered by the upload button.
     */
    async handleUploadButtonClick(event) {
        event.preventDefault();
        const files = this.sidebar.getAllFiles('macro');
        const macroScript = this.macroScriptInput.value;

        if (!files.length) {
            displayErrorMessage('Please select at least one image file to process.');
            return;
        }

        if (!macroScript.trim()) {
            displayErrorMessage('Please provide a macro script to execute.');
            return;
        }

        await this.handleFiles(files, 'macro', true, macroScript);
    }

    /**
     * @method handleFiles
     * @description Processes uploaded files based on the context.
     * @param {FileList|File[]} fileList - The list of files to be processed.
     * @param {string} context - The context in which the files are being processed ('upload', 'chat', or 'macro').
     * @param {boolean} executeMacro - Whether a macro should be executed on the uploaded files.
     * @param {string} macroScript - The macro script to execute if applicable.
     */
    async handleFiles(fileList, context, executeMacro = false, macroScript = '') {
        const files = Array.isArray(fileList) ? fileList : Array.from(fileList);

        if (files.length === 0) {
            displayErrorMessage('No files selected for processing.');
            return;
        }

        // Filter valid files
        const validFiles = files.filter(file => this.isValidFile(file));
        const invalidFiles = files.filter(file => !this.isValidFile(file));

        if (invalidFiles.length > 0) {
            invalidFiles.forEach(file => {
                displayErrorMessage(`${file.name} is not a supported image format`);
            });
        }

        if (validFiles.length === 0) {
            displayErrorMessage('No valid files to process.');
            return;
        }

        try {
            const response = await this.uploadFiles(validFiles, executeMacro, macroScript);
            this.processUploadResponse(response, validFiles, context, executeMacro);
        } catch (error) {
            console.error('Error processing files:', error);
            displayErrorMessage(`Error processing files: ${error.message}`);
        }

        // Update the file input to include all current files
        this.updateFileInput(context);
    }

    /**
     * @method isValidFile
     * @description Validates whether a file is a supported format.
     * @param {File} file - The file to validate.
     * @returns {boolean} - True if the file is valid, false otherwise.
     */
    isValidFile(file) {
        const fileExtension = file.name.split('.').pop().toLowerCase();
        return file.type.startsWith('image/') || this.microscopySupportedExtensions.includes(fileExtension);
    }

    /**
     * @method uploadFiles
     * @description Uploads files to the server and handles the response.
     * @param {File[]} files - Array of files to be uploaded.
     * @param {boolean} executeMacro - Indicates whether to execute a macro script.
     * @param {string} macroScript - The macro script to be executed.
     * @returns {Promise<Object>} - The processed results from the server.
     * @throws {Error} - Throws an error if the upload fails or the response is invalid.
     */
    async uploadFiles(files, executeMacro = false, macroScript = '') {
        try {
            const response = await uploadImage(files, executeMacro, macroScript);

            if (response instanceof Blob || Array.isArray(response)) {
                return response;
            } else {
                throw new Error('Unexpected response format from server');
            }
        } catch (error) {
            throw error;
        }
    }

    /**
     * @method processUploadResponse
     * @description Processes the server response after file upload.
     * @param {Blob|Object[]} response - The server response to process.
     * @param {File[]} files - The original files that were uploaded.
     * @param {string} context - The context of the upload ('upload', 'chat', or 'macro').
     * @param {boolean} executeMacro - Whether a macro was executed.
     */
    processUploadResponse(response, files, context, executeMacro) {
        if (executeMacro) {
            if (response instanceof Blob) {
                this.processingRunCounter += 1;

                // Create a download link for the results
                const zipUrl = URL.createObjectURL(response);
                const downloadLink = document.createElement('a');
                downloadLink.href = zipUrl;
                downloadLink.download = `results_${this.processingRunCounter}.zip`;
                downloadLink.textContent = `Download Results ${this.processingRunCounter}`;

                // Append the download link to the results container
                if (!this.resultsContainer) {
                    this.resultsContainer = document.createElement('div');
                    this.resultsContainer.id = 'results-container';
                    // Place the results container below the execute button
                    this.uploadBtn.insertAdjacentElement('afterend', this.resultsContainer);
                }
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                resultItem.appendChild(downloadLink);

                // Optionally, add a timestamp
                const timestamp = new Date().toLocaleString();
                const timestampDiv = document.createElement('div');
                timestampDiv.className = 'result-timestamp';
                timestampDiv.textContent = `Generated on: ${timestamp}`;
                resultItem.appendChild(timestampDiv);

                this.resultsContainer.appendChild(resultItem);

                displaySuccessMessage(`Macro executed successfully. Results ${this.processingRunCounter} available for download.`);
            } else {
                throw new Error('Unexpected response format from server');
            }
        } else {
            if (Array.isArray(response)) {
                response.forEach((result, index) => {
                    const file = files[index];
                    this.sidebar.addImagePreview(file, result.preview, context);
                });
                displaySuccessMessage('Images uploaded successfully.');
            } else {
                throw new Error('Unexpected response format from server');
            }
        }
    }

    /**
     * @method updateFileInput
     * @description Updates the file input element to reflect the current state of accumulated previews.
     * @param {string} context - The context for the file input ('upload', 'chat', 'macro').
     */
    updateFileInput(context) {
        const targetInput = context === 'chat' ? this.chatFileInput : this.macroFileInput;
        const allFiles = this.sidebar.getAllFiles(context);

        const dataTransfer = new DataTransfer();
        allFiles.forEach(file => {
            dataTransfer.items.add(file);
        });

        targetInput.files = dataTransfer.files;
    }

    /**
     * @method handleDragOver
     * @description Handles drag-over event for the drop zone.
     * @param {DragEvent} e - The drag event.
     */
    handleDragOver(e) {
        e.preventDefault();
        this.dropZone.classList.add('drag-over');
    }

    /**
     * @method handleDragLeave
     * @description Handles drag-leave event for the drop zone.
     */
    handleDragLeave() {
        this.dropZone.classList.remove('drag-over');
    }

    /**
     * @method handleDrop
     * @description Handles the drop event for the drop zone.
     * @param {DragEvent} e - The drop event.
     */
    handleDrop(e) {
        e.preventDefault();
        this.dropZone.classList.remove('drag-over');
        this.handleFiles(e.dataTransfer.files, 'macro');
    }
}

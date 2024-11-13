/**
 * @file sidebar.js
 * @description Manages the sidebar functionality for the Atlas application.
 *
 * This module provides a Sidebar class that handles image preview management,
 * sidebar toggling, and interaction with the backend for image deletion.
 *
 * @module sidebar
 * @requires apiCalls
 */

import { deleteImage } from './apiCalls.js';

/**
 * @class Sidebar
 * @description Manages sidebar functionality and image preview handling.
 */
export class Sidebar {
    /**
     * @constructor
     * @description Initializes the Sidebar instance and sets up event listeners.
     */
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.sidebarToggle = document.getElementById('sidebar-toggle');
        this.imagePreviewContainer = document.getElementById('image-preview-container');

        this.initializeEventListeners();
    }

    /**
     * @method initializeEventListeners
     * @description Sets up event listeners for sidebar functionality.
     */
    initializeEventListeners() {
        this.sidebarToggle.addEventListener('click', this.toggleSidebar.bind(this));
    }

    /**
     * @method toggleSidebar
     * @description Toggles the sidebar's collapsed state.
     */
    toggleSidebar() {
        this.sidebar.classList.toggle('collapsed');
        document.body.classList.toggle('sidebar-expanded');
    }

    /**
     * @method addImagePreview
     * @description Adds an image preview to the sidebar.
     * @param {File} file - The file to preview.
     * @param {string} previewUrl - The URL of the preview image.
     * @param {string} context - The context of the preview ('upload', 'chat', 'macro').
     */
    addImagePreview(file, previewUrl, context) {
        const previewElement = document.createElement('div');
        previewElement.className = 'image-preview';
        previewElement.innerHTML = `
            <img src="${previewUrl}" alt="${file.name}">
            <div class="file-name">${file.name}</div>
            <button class="remove-image" data-context="${context}">×</button>
        `;
        previewElement.file = file;
        previewElement.dataset.context = context;
        this.imagePreviewContainer.appendChild(previewElement);

        const removeBtn = previewElement.querySelector('.remove-image');
        removeBtn.addEventListener('click', () => this.removeImagePreview(file, context));
    }

    /**
     * @method removeImagePreview
     * @description Removes an image preview from the sidebar and deletes it from the backend.
     * @param {File} file - The file to remove.
     * @param {string} context - The context of the preview ('upload', 'chat', 'macro').
     */
    async removeImagePreview(file, context) {
        // Remove the preview element
        const previews = this.imagePreviewContainer.querySelectorAll('.image-preview');
        previews.forEach(preview => {
            if (preview.file && preview.file.name === file.name && preview.file.size === file.size) {
                preview.remove();
            }
        });

        // Update the file input
        const fileInput = context === 'chat' ? document.getElementById('chat-file-input') : document.getElementById('images');
        const dt = new DataTransfer();

        Array.from(fileInput.files).forEach(f => {
            if (!(f.name === file.name && f.size === file.size)) {
                dt.items.add(f);
            }
        });

        fileInput.files = dt.files;

        // Delete the image from the backend
        const uniqueFilename = file.uniqueFilename || file.name;

        try {
            await deleteImage(uniqueFilename);
        } catch (error) {
            console.error('Error removing image from backend:', error);
        }
    }

    /**
     * @method clearPreviews
     * @description Clears all image previews from the sidebar.
     */
    clearPreviews() {
        this.imagePreviewContainer.innerHTML = '';
    }

    /**
     * @method getAllPreviews
     * @description Gets all image previews for a specific context.
     * @param {string} context - The context to filter previews ('upload', 'chat', 'macro').
     * @returns {Array} An array of preview objects containing file and element information.
     */
    getAllPreviews(context) {
        const previews = [];
        const previewElements = this.imagePreviewContainer.querySelectorAll('.image-preview');
        previewElements.forEach(preview => {
            if (preview.dataset.context === context) {
                const file = preview.file;
                if (file) {
                    previews.push({ file: file, element: preview });
                }
            }
        });
        return previews;
    }
}

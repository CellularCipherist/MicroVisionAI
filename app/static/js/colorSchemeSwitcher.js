/**
 * @file colorSchemeSwitcher.js
 * @description Manages the color scheme switching functionality for the Atlas application.
 *
 * This module provides functions to initialize and handle color scheme changes,
 * persisting the user's preference across sessions.
 *
 * @module colorSchemeSwitcher
 */

/**
 * Initializes the color scheme switching functionality.
 */
export function initializeColorScheme() {
    const schemeSelect = document.getElementById('color-scheme-select');
    if (!schemeSelect) {
        console.warn('Color scheme select element not found.');
        return;
    }

    schemeSelect.addEventListener('change', function () {
        const selectedScheme = this.value;
        applyColorScheme(selectedScheme);
    });

    // Load previously selected scheme from local storage on page load
    const savedScheme = localStorage.getItem('selectedColorScheme') || 'default-scheme';
    applyColorScheme(savedScheme);
    schemeSelect.value = savedScheme;
}

/**
 * Applies the selected color scheme to the document body.
 * @param {string} scheme - The selected color scheme.
 */
function applyColorScheme(scheme) {
    // Clears previous scheme classes to avoid conflicts
    document.body.className = '';

    // Applies the selected scheme
    document.body.classList.add(scheme);

    // Persist the user's choice in local storage
    localStorage.setItem('selectedColorScheme', scheme);
}

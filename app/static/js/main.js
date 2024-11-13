/**
 * @file main.js
 * @description Main entry point for the Atlas application.
 *
 * This module initializes all the major components of the application,
 * sets up event listeners, and manages the overall application state.
 *
 * @module main
 */

import { Sidebar } from './sidebar.js';
import { FileHandler } from './fileHandling.js';
import ChatInterface from './chatInterface.js';
import { MacroScriptInterface } from './macroScriptInterface.js';
import { setupEventListeners } from './eventListeners.js';
import { initializeColorScheme } from './colorSchemeSwitcher.js';

/**
 * @class AtlasApp
 * @description Main application class that initializes and manages all components.
 */
class AtlasApp {
    /**
     * @constructor
     * @description Initializes the Atlas application.
     */
    constructor() {
        this.sidebar = null;
        this.fileHandler = null;
        this.chatInterface = null;
        this.macroScriptInterface = null;
    }

    /**
     * @method initialize
     * @description Initializes all components of the application.
     */
    initialize() {
        this.sidebar = new Sidebar();
        this.fileHandler = new FileHandler(this.sidebar);
        this.chatInterface = new ChatInterface(this.sidebar);
        this.macroScriptInterface = new MacroScriptInterface(this.sidebar);

        setupEventListeners(this.sidebar, this.fileHandler, this.chatInterface, this.macroScriptInterface);
        initializeColorScheme();
    }
}

// Initialize the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    const app = new AtlasApp();
    app.initialize();
});

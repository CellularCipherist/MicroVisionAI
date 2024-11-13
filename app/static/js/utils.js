/**
 * @file utils.js
 * @description Utility functions for the Atlas application.
 * @module utils
 */

/**
 * Adjusts the height of a textarea to fit its content.
 * @param {HTMLTextAreaElement} textarea - The textarea element to adjust.
 */
export function adjustTextareaHeight(textarea) {
    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    // Set the height to the scrollHeight
    textarea.style.height = textarea.scrollHeight + 'px';
}

/**
 * Creates a debounced function that delays invoking `func` until after `wait` milliseconds have elapsed since the last time the debounced function was invoked.
 * @param {Function} func - The function to debounce.
 * @param {number} wait - The number of milliseconds to delay.
 * @returns {Function} The debounced function.
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Generates a unique identifier.
 * @returns {string} A unique identifier string.
 */
export function generateUniqueId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Safely parses JSON, returning null if parsing fails.
 * @param {string} jsonString - The JSON string to parse.
 * @returns {Object|null} The parsed object or null if parsing failed.
 */
export function safeJSONParse(jsonString) {
    try {
        return JSON.parse(jsonString);
    } catch (error) {
        console.error('Error parsing JSON:', error);
        return null;
    }
}

/**
 * Truncates a string to a specified length, appending an ellipsis if truncated.
 * @param {string} str - The string to truncate.
 * @param {number} maxLength - The maximum length of the string.
 * @returns {string} The truncated string.
 */
export function truncateString(str, maxLength) {
    if (str.length <= maxLength) return str;
    return str.slice(0, maxLength - 3) + '...';
}

/**
 * Escapes HTML special characters in a string.
 * @param {string} unsafe - The string with potentially unsafe HTML.
 * @returns {string} The string with HTML special characters escaped.
 */
export function escapeHTML(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/**
 * Formats a date object to a string in the format "YYYY-MM-DD HH:MM:SS".
 * @param {Date} date - The date to format.
 * @returns {string} The formatted date string.
 */
export function formatDate(date) {
    return date.toISOString().replace('T', ' ').substr(0, 19);
}

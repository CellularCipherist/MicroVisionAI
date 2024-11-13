/**
 * @file apiCalls.js
 * @description Manages API calls for the Atlas application.
 *
 * This module provides functions for generating macros, improving prompts,
 * and handling streaming responses from the server.
 */

import { ROUTES } from './routes.js';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';
/**
 * Generates a macro using EventSource and handles streamed responses.
 *
 * @function generateMacro
 * @param {string} input - The prompt input for macro generation.
 * @param {boolean} improvePrompt - Whether the prompt was improved.
 * @returns {EventSource} - The EventSource instance.
 */

// apiCalls.js


export function generateMacro(input, improvePrompt = false) {
    const params = new URLSearchParams({
        input: input,
        improve_prompt: improvePrompt.toString()
    });

    const url = `${API_BASE_URL}${ROUTES.GENERATE_MACRO}?${params.toString()}`;

    return new EventSource(url, {
        withCredentials: true
    });
}
/**
 * Initiates prompt improvement and streams the improved prompt back to the user.
 *
 * @function generateImprovedPrompt
 * @param {string} input - The original user input.
 * @returns {EventSource} - The EventSource instance for streaming responses.
 */
export function generateImprovedPrompt(input) {
    const params = new URLSearchParams({
        input: input,
    });
    const url = `${API_BASE_URL}${ROUTES.IMPROVE_PROMPT}?${params.toString()}`;
    return new EventSource(url);
}

/**
 * Handles API errors consistently.
 * @param {Response} response - The fetch Response object.
 * @throws {Error} Throws an error with status and message if the response is not ok.
 */
async function handleApiError(response) {
    if (!response.ok) {
        const errorMessage = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorMessage}`);
    }
}

/**
 * Uploads images and optionally executes a macro.
 * Handles response parsing with clear content type checks.
 *
 * @param {File[]} files - The list of files to upload.
 * @param {boolean} [executeMacro=false] - Whether to execute a macro script.
 * @param {string} [macroScript=''] - The macro script to execute.
 * @returns {Promise<Object|Blob>} The response from the server.
 * @throws {Error} If the upload fails.
 */
export async function uploadImage(files, executeMacro = false, macroScript = '') {
    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));
    formData.append('execute_macro', executeMacro.toString());
    if (executeMacro && macroScript) {
        formData.append('macro_script', macroScript);
    }

    try {
        const response = await fetch(`${API_BASE_URL}${ROUTES.UPLOAD_IMAGE}`, {
            method: 'POST',
            body: formData,
        });

        // Check content type and handle accordingly
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            return data.results;
        } else if (contentType && contentType.includes('application/zip')) {
            const blob = await response.blob();
            return blob;
        } else {
            console.error('Unexpected response content type:', contentType);
            throw new Error('Unsupported response format received');
        }
    } catch (error) {
        console.error('Error uploading image:', error);
        throw error;
    }
}

/**
 * Fetches a base64 encoded image preview.
 * @param {string} filename - The filename for which to generate a preview.
 * @returns {Promise<string>} The base64-encoded preview image.
 * @throws {Error} If fetching the preview fails.
 */
export async function generateImagePreview(filename) {
    try {
        const response = await fetch(`${API_BASE_URL}/get_image_preview/${filename}`, {
            method: 'GET',
        });

        await handleApiError(response);
        const data = await response.json();
        return data.preview;
    } catch (error) {
        console.error('Error generating image preview:', error);
        throw error;
    }
}

/**
 * Deletes an image and its associated data.
 * @param {string} filename - The filename of the image to delete.
 * @returns {Promise<Object>} The response from the server.
 * @throws {Error} If the deletion fails.
 */
export async function deleteImage(filename) {
    try {
        const response = await fetch(`${API_BASE_URL}${ROUTES.DELETE_IMAGE}${filename}`, {
            method: 'DELETE',
        });

        await handleApiError(response);
        return await response.json();
    } catch (error) {
        console.error('Error deleting image:', error);
        throw error;
    }
}

/**
 * Executes a macro on the provided images.
 * @param {File[]} files - The list of image files.
 * @param {string} macroScript - The macro script to execute.
 * @returns {Promise<Object|Blob>} The response from the server.
 */
export async function executeImageMacro(files, macroScript) {
    return uploadImage(files, true, macroScript);
}

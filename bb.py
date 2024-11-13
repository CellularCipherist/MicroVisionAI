

files_core = [
    "app/config.py",          # Configuration loader - used by most other modules
    "app/database.py",        # Database setup - core dependency
    "app/__init__.py",        # Application initialization
    "app/main.py",           # Entry point
    "app/auth.py",           # Authentication system
    "config.yaml"            # Configuration data
]

files_services = [
    "app/services/__init__.py",
    "app/services/file_service.py",      # File handling operations
    "app/services/image_service.py",     # Image processing logic
    "app/services/imagej_service.py",    # ImageJ integration
    "app/services/atlas_service.py"      # AI integration
]

files_routes = [
    "app/routes/app_primer.json",    # API documentation
    "app/routes/chat_routes.py",     # Chat endpoints
    "app/routes/image_routes.py"     # Image handling endpoints
]

files_templates = [
    "app/templates/index.html",
    "app/templates/macros/headless_macro_template.ijm",
    "app/templates/macros/conversion_macro.ijm"
]

files_js = [
    "app/static/js/main.js",              # Main application entry
    "app/static/js/apiCalls.js",          # API integration
    "app/static/js/routes.js",            # Frontend routing
    "app/static/js/chatInterface.js",     # Chat functionality
    "app/static/js/fileHandling.js",      # File operations
    "app/static/js/macroScriptInterface.js",
    "app/static/js/sidebar.js",
    "app/static/js/eventListeners.js",
    "app/static/js/colorSchemeSwitcher.js",
    "app/static/js/uiUpdates.js",
    "app/static/js/utils.js"
]

files_css = [
    "app/static/css/main.css",
    "app/static/css/layout.css",
    "app/static/css/chat.css",
    "app/static/css/messages.css",
    "app/static/css/macro-script.css",
    "app/static/css/sidebar.css",
    "app/static/css/drag-drop.css",
    "app/static/css/color-scheme-selector.css",
    "app/static/css/colors.css",
    "app/static/css/responsive.css",
    "app/static/css/utilities.css"
]

files_prompts = [
    "app/prompts/__init__.py",
    "app/prompts/system_prompts.py"
]

import os

# Base directory for your project
base_directory = "/home/alex/projects/Tests/FijiAI_Next"

# Organized file groups
files_to_combine = (
    files_core +          # Core application files
    files_services +      # Service layer
    files_routes +        # API routes
    files_templates +     # Templates and macros
    files_prompts +       # AI prompts
    files_js +           # Frontend JavaScript
    files_css            # Styling
)

output_file = "/home/alex/projects/Tests/FijiAI_Next/combined_chat_interface.txt"

# Combine files with section headers
with open(output_file, 'w') as outfile:
    for file in files_to_combine:
        file_path = os.path.join(base_directory, file)
        if os.path.exists(file_path):
            outfile.write(f"===== {file} =====\n\n")
            with open(file_path, 'r') as infile:
                outfile.write(infile.read())
            outfile.write("\n\n")

print(f"Combined content saved to: {output_file}")

# MicroVisionAI

A sophisticated platform integrating AI-driven microscopy image analysis with real-time processing capabilities. Built using FastAPI, ImageJ/Fiji, and Anthropic's Claude AI, MicroVisionAI streamlines complex microscopy analysis workflows through an intuitive interface.

## Core Features

- **AI-Powered Analysis Generation**
  - Real-time macro generation using Anthropic's Claude AI
  - Context-aware prompt improvement for microscopy workflows
  - Streaming responses for immediate feedback


- **Advanced Image Processing**
  - Headless ImageJ integration via scyjava
  - Multi-channel and z-stack image support
  - Parallel processing capabilities
  - Automatic preview generation

- **Real-Time Updates**
  - Server-Sent Events (EventSource) for live processing status
  - Streaming macro generation feedback
  - Real-time image preview updates

- **Robust Architecture**
  - Modular service-based design
  - Comprehensive error handling
  - Resource-optimized file operations
  - Automated cleanup processes

## Technical Stack

### Backend
- Python 3.8+
- FastAPI
- SQLAlchemy
- ImageJ (via scyjava)
- Anthropic API
- Server-Sent Events

### Frontend
- Modern JavaScript (ES6+)
- Dynamic UI components
- Real-time event handling
- Responsive design

## Quick Start

1. **Clone & Setup**
```bash
git clone https://github.com/yourusername/FijiAI_Next.git
cd FijiAI_Next
python -m venv venv
source venv/bin/activate
pip install -r [requirements.txt](http://_vscodecontentref_/0)

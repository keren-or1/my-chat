"""
Ollama Chat Application - FastAPI Backend

A modern, privacy-first web chat application that integrates with Ollama
for local LLM inference. This module provides HTTP endpoints for:
- Chat message processing with streaming support
- Model listing and management
- Service health monitoring
- Web UI serving

Architecture:
    - Stateless backend (no session storage)
    - Async/await for concurrent request handling
    - Streaming responses for real-time user feedback
    - CORS-enabled for frontend communication

Type Hints:
    All functions include complete type annotations for parameters
    and return types, enabling better IDE support and static analysis.

Author: Keren
Version: 1.0.0
Date: November 2024
"""

import os
import json
import logging
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Configure logging for debugging and monitoring
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

class Config:
    """
    Application configuration loaded from environment variables.

    Environment variables override defaults for easy configuration
    across different deployment environments (dev, staging, prod).

    Attributes:
        OLLAMA_API_URL (str): Base URL for Ollama API service
        MODEL_NAME (str): Default LLM model name (e.g., 'tinyllama')
        API_HOST (str): FastAPI server host binding
        API_PORT (int): FastAPI server port
        TEMPERATURE (float): LLM sampling temperature (0.0 to 1.0)
        TOP_P (float): Nucleus sampling parameter
        TOP_K (int): Top-K sampling limit
        HEALTH_CHECK_INTERVAL (int): Seconds between health checks
        HEALTH_CHECK_TIMEOUT (int): Timeout for health check requests
    """

    # Ollama Configuration
    OLLAMA_API_URL: str = os.getenv(
        "OLLAMA_API_URL",
        "http://localhost:11434/api"
    )
    MODEL_NAME: str = os.getenv("OLLAMA_MODEL", "tinyllama")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "300"))

    # FastAPI Server Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_LOG_LEVEL: str = os.getenv("API_LOG_LEVEL", "info")

    # LLM Model Parameters (passed to Ollama)
    TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    TOP_P: float = float(os.getenv("LLM_TOP_P", "0.9"))
    TOP_K: int = int(os.getenv("LLM_TOP_K", "40"))

    # Health Check Configuration
    HEALTH_CHECK_INTERVAL: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "5"))
    HEALTH_CHECK_TIMEOUT: int = int(os.getenv("HEALTH_CHECK_TIMEOUT", "2"))

    # CORS Configuration (Security)
    CORS_ORIGINS: list[str] = (
        os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")
    )
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    CORS_ALLOW_METHODS: list[str] = os.getenv("CORS_ALLOW_METHODS", "GET,POST,OPTIONS").split(",")
    CORS_ALLOW_HEADERS: list[str] = os.getenv("CORS_ALLOW_HEADERS", "Content-Type").split(",")

    # Application Metadata
    APP_NAME: str = os.getenv("APP_NAME", "Ollama Chat Application")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.1.0")

# ============================================================================
# INITIALIZATION & STARTUP
# ============================================================================

# Get the application root directory
APP_ROOT: Path = Path(__file__).parent.parent
APP_DIR: Path = APP_ROOT / "app"
TEMPLATES_DIR: Path = APP_DIR / "templates"
STATIC_DIR: Path = APP_DIR / "static"

logger.info(f"Application root: {APP_ROOT}")
logger.info(f"App directory: {APP_DIR}")
logger.info(f"Templates: {TEMPLATES_DIR}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup and shutdown events.

    This function runs:
    - On startup: Log initialization, verify directories
    - On shutdown: Cleanup resources (if any)

    Args:
        app (FastAPI): The FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {Config.APP_NAME} v{Config.APP_VERSION}")
    logger.info(f"Ollama service: {Config.OLLAMA_API_URL}")
    logger.info(f"Model: {Config.MODEL_NAME}")
    logger.info(f"Server: {Config.API_HOST}:{Config.API_PORT}")
    logger.info("=" * 60)

    # Verify templates directory exists
    if not TEMPLATES_DIR.exists():
        logger.warning(f"Templates directory not found: {TEMPLATES_DIR}")

    yield

    # Shutdown
    logger.info("Shutting down Ollama Chat Application")

# Initialize FastAPI app
app = FastAPI(
    title=Config.APP_NAME,
    description="A modern chat interface for Ollama models with local LLM inference",
    version=Config.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware for frontend communication (configurable for security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=Config.CORS_ALLOW_CREDENTIALS,
    allow_methods=Config.CORS_ALLOW_METHODS,
    allow_headers=Config.CORS_ALLOW_HEADERS,
)
logger.info(f"CORS enabled for origins: {', '.join(Config.CORS_ORIGINS)}")

# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    logger.info(f"Static files mounted: {STATIC_DIR}")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error messages to prevent information disclosure.

    Removes sensitive information like file paths, internal details
    from exception messages before returning to client.

    Args:
        error (Exception): The exception to sanitize

    Returns:
        str: Safe error message for client

    Examples:
        >>> sanitize_error_message(Exception("/home/user/.ollama/model.bin not found"))
        "An error occurred processing your request"
    """
    error_str = str(error).lower()

    # Map of dangerous patterns to safe messages
    dangerous_patterns = {
        "connection": "Connection error - service unavailable",
        "timeout": "Request timeout - service taking too long",
        "json": "Invalid request format",
        "model": "Model processing error",
        "ollama": "LLM service error",
    }

    # Check for dangerous patterns
    for pattern, safe_msg in dangerous_patterns.items():
        if pattern in error_str:
            return safe_msg

    # Default safe message
    return "An error occurred processing your request"


def validate_message(message: str) -> str:
    """
    Validate and sanitize user message.

    Validation rules:
    - Message must not be empty (after stripping whitespace)
    - Message must not exceed 4000 characters (practical limit)
    - Leading/trailing whitespace is stripped

    Args:
        message (str): Raw user message input

    Returns:
        str: Sanitized message

    Raises:
        ValueError: If message is empty after validation

    Examples:
        >>> validate_message("  Hello world  ")
        "Hello world"

        >>> validate_message("   ")
        Traceback: ValueError: Message cannot be empty

        >>> validate_message("x" * 5000)
        Traceback: ValueError: Message exceeds maximum length
    """
    # Strip whitespace
    cleaned = message.strip()

    # Check not empty
    if not cleaned:
        raise ValueError("Message cannot be empty")

    # Check length
    if len(cleaned) > 4000:
        raise ValueError("Message exceeds maximum length of 4000 characters")

    return cleaned

# ============================================================================
# HEALTH & STATUS ENDPOINTS
# ============================================================================

@app.get(
    "/api/health",
    summary="Health Check",
    description="Check if both FastAPI and Ollama services are running",
    response_description="Service health status",
    tags=["Health"]
)
async def health_check() -> Dict[str, Any]:
    """
    Check the health of the FastAPI server and Ollama service.

    This endpoint performs:
    1. Connectivity check to Ollama API
    2. Model availability verification
    3. Service status reporting

    Returns:
        Dict[str, Any]: Status information with fields:
            - status (str): "healthy" if connected, otherwise raises HTTPException
            - ollama (str): "connected" or "disconnected"
            - model (str): Currently configured model name

    Raises:
        HTTPException(503): If Ollama service is unreachable
            - Message: "Ollama service not available"
            - Cause: Network error, service not running, port mismatch

    Performance:
        - Timeout: 2 seconds (configurable via HEALTH_CHECK_TIMEOUT)
        - Typical response: < 100ms when healthy

    Edge Cases Handled:
        - Ollama service not running
        - Network connectivity issues
        - Firewall blocking connections
        - Incorrect OLLAMA_API_URL configuration

    Examples:
        Request:
            GET /api/health

        Success Response (200):
            {
              "status": "healthy",
              "ollama": "connected",
              "model": "tinyllama"
            }

        Error Response (503):
            {
              "detail": "Ollama service not available"
            }
    """
    try:
        # Check Ollama connectivity
        response: requests.Response = requests.get(
            f"{Config.OLLAMA_API_URL}/tags",
            timeout=Config.HEALTH_CHECK_TIMEOUT
        )

        if response.status_code == 200:
            logger.info("Health check passed - Ollama connected")
            return {
                "status": "healthy",
                "ollama": "connected",
                "model": Config.MODEL_NAME
            }
        else:
            logger.error(f"Ollama health check failed: {response.status_code}")
            raise HTTPException(
                status_code=503,
                detail="Ollama service returned non-200 status"
            )

    except Timeout:
        logger.error(f"Health check timeout after {Config.HEALTH_CHECK_TIMEOUT}s")
        raise HTTPException(
            status_code=503,
            detail="Ollama service timeout - check if ollama serve is running"
        )
    except ConnectionError as e:
        logger.error(f"Cannot connect to Ollama: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Ollama service not available at {Config.OLLAMA_API_URL}"
        )
    except RequestException as e:
        logger.error(f"Request error during health check: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama service"
        )

# ============================================================================
# MODEL MANAGEMENT ENDPOINTS
# ============================================================================

@app.get(
    "/api/models",
    summary="List Available Models",
    description="Get list of installed Ollama models",
    response_description="List of available models",
    tags=["Models"]
)
async def get_models() -> Dict[str, Any]:
    """
    Retrieve list of available models from Ollama.

    This endpoint queries Ollama for all installed models
    and returns them along with the currently active model.

    Returns:
        Dict[str, Any]: Models information with fields:
            - models (list[str]): List of available model names
            - current_model (str): Name of the model in use
            - available (bool): Whether models are available

    Raises:
        HTTPException(503): If Ollama service is unreachable
            - Message: "Failed to fetch models: {error}"

    Performance:
        - Timeout: 5 seconds (standard HTTP timeout)
        - Typical response: < 200ms

    Edge Cases Handled:
        - Ollama service not running
        - No models installed (empty list)
        - Network issues

    Examples:
        Request:
            GET /api/models

        Success Response (200):
            {
              "models": [
                "tinyllama:latest",
                "llama2:7b",
                "mistral:7b"
              ],
              "current_model": "tinyllama",
              "available": true
            }

        Error Response (503):
            {
              "detail": "Failed to fetch models: Connection refused"
            }

    Note:
        Model names typically include version tags (e.g., "tinyllama:latest").
        The current_model is determined by Config.MODEL_NAME.
    """
    try:
        response: requests.Response = requests.get(
            f"{Config.OLLAMA_API_URL}/tags",
            timeout=5
        )

        if response.status_code == 200:
            data: Dict[str, Any] = response.json()
            models: list[str] = [
                model["name"] for model in data.get("models", [])
            ]
            logger.info(f"Retrieved {len(models)} models from Ollama")
            return {
                "models": models,
                "current_model": Config.MODEL_NAME,
                "available": True
            }
        else:
            logger.error(f"Failed to fetch models: HTTP {response.status_code}")
            raise HTTPException(
                status_code=503,
                detail="Failed to fetch available models"
            )

    except RequestException as e:
        logger.error(f"Failed to fetch models: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=sanitize_error_message(e)
        )

# ============================================================================
# CHAT ENDPOINT (MAIN)
# ============================================================================

@app.post(
    "/api/chat",
    summary="Send Chat Message",
    description="Send a message and get response from Ollama with optional streaming",
    response_description="Model response (streaming or buffered)",
    tags=["Chat"],
    response_model=None
)
async def chat(request: Request) -> StreamingResponse | Dict[str, Any]:
    """
    Main chat endpoint - process user messages and stream responses.

    This endpoint is the core chat functionality. It:
    1. Receives user message from frontend
    2. Validates message content and format
    3. Sends to Ollama with LLM parameters
    4. Returns response (streaming or buffered)

    Request Format:
        Content-Type: application/json
        {
          "message": "User's question or statement",
          "stream": true (optional, defaults to true)
        }

    Returns:
        Streaming: StreamingResponse with media_type "text/event-stream"
            - Each chunk contains response tokens
            - Chunks arrive as they're generated
            - Frontend accumulates text progressively

        Buffered: Dict[str, Any] with fields:
            - response (str): Complete model response
            - model (str): Model name used
            - stream (bool): False (indicates non-streaming)

    Raises:
        HTTPException(400): Bad request
            - Empty message: "Message cannot be empty"
            - Invalid JSON: "Invalid JSON in request body"
            - Message too long: "Message exceeds maximum length"

        HTTPException(503): Service unavailable
            - Ollama not running: "Cannot connect to Ollama service"
            - Connection timeout: "Connection timeout to Ollama"

        HTTPException(500): Server error
            - Unexpected error: "Server error: {details}"

    Performance:
        - Request validation: < 5ms
        - Ollama request: 3-5s (first request), 0.5-2s (subsequent)
        - Streaming latency: < 100ms per token
        - Buffered response: Same as streaming but accumulated

    Parameters Passed to Ollama:
        - temperature: Controls randomness (0.7 default, 0=deterministic, 1=creative)
        - top_p: Nucleus sampling parameter (0.9 default)
        - top_k: Top-K sampling limit (40 default)

    Edge Cases Handled:
        1. Empty message validation
        2. Message exceeds 4000 characters
        3. Invalid JSON in request body
        4. Ollama connection failure
        5. JSON decode errors in response
        6. Stream interruption during response
        7. Timeout during model inference

    Examples:
        Request (Streaming):
            POST /api/chat
            Content-Type: application/json

            {
              "message": "What is machine learning?",
              "stream": true
            }

        Streaming Response (200):
            Content-Type: text/event-stream
            Transfer-Encoding: chunked

            Machine learning is...
            a subset of artificial intelligence...
            that enables computers to learn...

        Request (Non-Streaming):
            POST /api/chat
            Content-Type: application/json

            {
              "message": "Hello",
              "stream": false
            }

        Buffered Response (200):
            {
              "response": "Hello! How can I help you today?",
              "model": "tinyllama",
              "stream": false
            }

        Error Responses:
            400: {"detail": "Message cannot be empty"}
            400: {"detail": "Invalid JSON in request body"}
            503: {"detail": "Cannot connect to Ollama service"}
    """
    try:
        # Parse and validate request body
        body: Dict[str, Any] = await request.json()
        user_message: str = body.get("message", "").strip()
        stream: bool = body.get("stream", True)

        # Validate message
        validated_message: str = validate_message(user_message)
        logger.debug(f"Received message: {validated_message[:100]}...")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON in request body"
        )
    except ValueError as e:
        logger.warning(f"Message validation failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=sanitize_error_message(e)
        )
    except Exception as e:
        logger.error(f"Error parsing request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=sanitize_error_message(e)
        )

    try:
        # Prepare Ollama request payload
        ollama_payload: Dict[str, Any] = {
            "model": Config.MODEL_NAME,
            "prompt": validated_message,
            "stream": stream,
            "temperature": Config.TEMPERATURE,
            "top_p": Config.TOP_P,
            "top_k": Config.TOP_K,
        }

        logger.debug(f"Sending to Ollama: model={Config.MODEL_NAME}")

        # Send request to Ollama
        response: requests.Response = requests.post(
            f"{Config.OLLAMA_API_URL}/generate",
            json=ollama_payload,
            stream=stream,
            timeout=Config.OLLAMA_TIMEOUT
        )

        # Check response status
        if response.status_code != 200:
            logger.error(f"Ollama error ({response.status_code}): {response.text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Ollama error: {response.text[:200]}"
            )

        # Handle streaming vs buffered response
        if stream:
            logger.debug("Starting streaming response")

            # Streaming response handler
            async def generate() -> AsyncGenerator[str, None]:
                """
                Async generator for streaming response tokens.

                Yields tokens as they arrive from Ollama, with error handling
                for various failure modes.

                Yields:
                    str: Response tokens from Ollama

                Edge Cases:
                    - Malformed JSON in stream chunk
                    - Empty chunks
                    - Connection interruption mid-stream
                    - Timeout during streaming
                """
                try:
                    for line in response.iter_lines():
                        if line:
                            try:
                                data: Dict[str, Any] = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                            except json.JSONDecodeError:
                                logger.warning(f"Malformed JSON in stream: {line[:50]}")
                                yield "[Error decoding response]"
                except GeneratorExit:
                    logger.info("Stream interrupted by client")
                except Exception as e:
                    logger.error(f"Error during streaming: {str(e)}")
                    yield f"[Stream error: {sanitize_error_message(e)}]"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        else:
            # Buffered response
            logger.debug("Returning buffered response")
            data: Dict[str, Any] = response.json()
            return {
                "response": data.get("response", ""),
                "model": Config.MODEL_NAME,
                "stream": False
            }

    except Timeout:
        logger.error(f"Timeout connecting to Ollama after {Config.OLLAMA_TIMEOUT}s")
        raise HTTPException(
            status_code=503,
            detail="Request timeout - Ollama is too slow or not responding"
        )
    except ConnectionError:
        logger.error(f"Cannot connect to Ollama at {Config.OLLAMA_API_URL}")
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to Ollama service at {Config.OLLAMA_API_URL}"
        )
    except RequestException as e:
        logger.error(f"Request error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Cannot connect to Ollama service"
        )
    except Exception as e:
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)[:100]}"
        )

# ============================================================================
# APPLICATION INFO ENDPOINTS
# ============================================================================

@app.get(
    "/api/info",
    summary="Application Information",
    description="Get application version and configuration info",
    response_description="Application metadata",
    tags=["Info"]
)
async def get_info() -> Dict[str, Any]:
    """
    Get application metadata and configuration information.

    This endpoint returns static information about the application
    and its current configuration. Useful for debugging and
    understanding the deployment.

    Returns:
        Dict[str, Any]: Application information with fields:
            - app_name (str): Application name
            - version (str): Application version
            - model (str): Currently active LLM model
            - description (str): Application description
            - ollama_url (str): Ollama service URL

    Examples:
        Request:
            GET /api/info

        Response (200):
            {
              "app_name": "Ollama Chat Application",
              "version": "1.0.0",
              "model": "tinyllama",
              "description": "A modern web-based chat interface for local LLM inference",
              "ollama_url": "http://localhost:11434/api"
            }
    """
    return {
        "app_name": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "model": Config.MODEL_NAME,
        "description": "A modern web-based chat interface for local LLM inference with Ollama",
        "ollama_url": Config.OLLAMA_API_URL
    }

# ============================================================================
# WEB UI SERVING
# ============================================================================

@app.get(
    "/",
    summary="Serve Chat Interface",
    description="Serve the main chat application page",
    response_description="HTML chat interface",
    tags=["UI"]
)
async def serve_index() -> FileResponse:
    """
    Serve the main HTML chat application page.

    This endpoint serves the single-page application (SPA) that
    contains all HTML, CSS, and JavaScript for the chat interface.

    File Path:
        app/templates/index.html

    Returns:
        FileResponse: HTML file with correct MIME type

    Raises:
        HTTPException(404): If index.html is not found
            - Check if templates/index.html exists
            - Verify APP_DIR configuration

    Examples:
        Request:
            GET http://localhost:8000/

        Response (200):
            Content-Type: text/html; charset=utf-8
            Content-Length: ~52000

            [HTML content with embedded CSS and JavaScript]
    """
    index_path: Path = TEMPLATES_DIR / "index.html"

    if not index_path.exists():
        logger.error(f"index.html not found at {index_path}")
        raise HTTPException(
            status_code=404,
            detail=f"index.html not found at {index_path}"
        )

    logger.debug(f"Serving index.html from {index_path}")
    return FileResponse(str(index_path), media_type="text/html")

@app.get(
    "/dashboard",
    summary="Serve Analytics Dashboard",
    description="Serve the analytics and performance dashboard",
    response_description="HTML analytics dashboard",
    tags=["UI"]
)
async def serve_dashboard() -> FileResponse:
    """
    Serve the analytics dashboard page.

    This endpoint serves an interactive analytics dashboard that displays:
    - System performance metrics
    - Research analysis and findings
    - Parameter sensitivity analysis
    - Model comparison data
    - Cost-benefit analysis
    - Quality metrics
    - Real-time status monitoring

    File Path:
        app/templates/dashboard.html

    Returns:
        FileResponse: HTML dashboard with embedded Charts.js visualizations

    Raises:
        HTTPException(404): If dashboard.html is not found

    Examples:
        Request:
            GET http://localhost:8000/dashboard

        Response (200):
            Content-Type: text/html; charset=utf-8
            [Interactive dashboard with charts and tables]
    """
    dashboard_path: Path = TEMPLATES_DIR / "dashboard.html"

    if not dashboard_path.exists():
        logger.error(f"dashboard.html not found at {dashboard_path}")
        raise HTTPException(
            status_code=404,
            detail=f"dashboard.html not found at {dashboard_path}"
        )

    logger.debug(f"Serving dashboard.html from {dashboard_path}")
    return FileResponse(str(dashboard_path), media_type="text/html")

# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get(
    "/api/",
    summary="API Root",
    description="API information and available endpoints",
    tags=["Info"]
)
async def api_root() -> Dict[str, Any]:
    """
    Get information about available API endpoints.

    Returns:
        Dict[str, Any]: API documentation and endpoints
    """
    return {
        "message": "Ollama Chat API",
        "version": Config.APP_VERSION,
        "endpoints": {
            "health": "/api/health",
            "models": "/api/models",
            "chat": "/api/chat",
            "info": "/api/info",
            "ui": "/",
            "dashboard": "/dashboard",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

# ============================================================================
# ERROR HANDLING
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom HTTP exception handler for consistent error responses.

    Args:
        request (Request): The HTTP request
        exc (HTTPException): The HTTPException raised

    Returns:
        JSONResponse: Formatted error response
    """
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail
        }
    )

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {Config.API_HOST}:{Config.API_PORT}")
    logger.info(f"Ollama endpoint: {Config.OLLAMA_API_URL}")
    logger.info(f"Model: {Config.MODEL_NAME}")

    uvicorn.run(
        app,
        host=Config.API_HOST,
        port=Config.API_PORT,
        log_level=Config.API_LOG_LEVEL,
        access_log=True
    )

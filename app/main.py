"""
Ollama Chat Application - FastAPI Backend
A modern chat application with web UI that integrates with Ollama for local LLM inference.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import os
from pathlib import Path
from typing import AsyncGenerator, Dict, Any

# Initialize FastAPI app
app = FastAPI(
    title="Ollama Chat App",
    description="A modern chat interface for Ollama models",
    version="1.0.0"
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama configuration
OLLAMA_API_URL: str = "http://localhost:11434/api"
MODEL_NAME: str = "tinyllama"

# Get the app directory
APP_DIR: Path = Path(__file__).parent
STATIC_DIR: Path = APP_DIR / "static"
TEMPLATES_DIR: Path = APP_DIR / "templates"

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Health check endpoint
@app.get("/api/health")
async def health_check() -> Dict[str, Any]:
    """Check if both the API and Ollama service are running."""
    try:
        response: requests.Response = requests.get(f"{OLLAMA_API_URL}/tags", timeout=2)
        if response.status_code == 200:
            return {
                "status": "healthy",
                "ollama": "connected",
                "model": MODEL_NAME
            }
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Ollama service not available")


# Get available models
@app.get("/api/models")
async def get_models() -> Dict[str, Any]:
    """Get list of available Ollama models."""
    try:
        response: requests.Response = requests.get(f"{OLLAMA_API_URL}/tags", timeout=5)
        if response.status_code == 200:
            data: Dict[str, Any] = response.json()
            models: list[str] = [model["name"] for model in data.get("models", [])]
            return {
                "models": models,
                "current_model": MODEL_NAME,
                "available": True
            }
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Failed to fetch models: {str(e)}")


@app.post("/api/chat")
async def chat(request: Request) -> StreamingResponse | Dict[str, Any]:
    """
    Chat endpoint that accepts a message and streams the response from Ollama.
    Supports both streaming and non-streaming responses.
    """
    try:
        body: Dict[str, Any] = await request.json()
        user_message: str = body.get("message", "").strip()
        stream: bool = body.get("stream", True)

        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Prepare the prompt
        prompt: str = user_message

        # Make request to Ollama
        ollama_payload: Dict[str, Any] = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": stream,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
        }

        response: requests.Response = requests.post(
            f"{OLLAMA_API_URL}/generate",
            json=ollama_payload,
            stream=stream,
            timeout=None  # Allow long-running requests
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Ollama error: {response.text}"
            )

        if stream:
            # Return streaming response
            async def generate() -> AsyncGenerator[str, None]:
                try:
                    for line in response.iter_lines():
                        if line:
                            data: Dict[str, Any] = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                except json.JSONDecodeError:
                    yield "Error decoding response"
                except Exception as e:
                    yield f"Error: {str(e)}"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        else:
            # Return complete response
            data: Dict[str, Any] = response.json()
            return {
                "response": data.get("response", ""),
                "model": MODEL_NAME,
                "stream": False
            }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot connect to Ollama service")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


# Serve the main HTML page
@app.get("/")
async def serve_index() -> FileResponse:
    """Serve the main chat application page."""
    index_path: Path = TEMPLATES_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    else:
        raise HTTPException(status_code=404, detail="index.html not found")


@app.get("/api/info")
async def get_info() -> Dict[str, Any]:
    """Get application information."""
    return {
        "app_name": "Ollama Chat Application",
        "version": "1.0.0",
        "model": MODEL_NAME,
        "description": "A modern web-based chat interface for local LLM inference with Ollama"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

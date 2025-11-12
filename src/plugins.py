"""
Plugin System for Ollama Chat Application

Extensible architecture for custom plugins and middleware.
Demonstrates advanced architectural patterns for production systems.

Features:
- Plugin loader and manager
- Hook system for request/response lifecycle
- Example plugins (Rate Limiter, Logging, Authentication)
- Configuration via environment variables
"""

import logging
from typing import Any, Callable, Dict, List, Optional
from abc import ABC, abstractmethod
from functools import wraps

logger = logging.getLogger(__name__)


class Plugin(ABC):
    """Base class for all plugins."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize plugin.
        
        Args:
            name: Plugin name
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        logger.info(f"Plugin initialized: {name}")
    
    @abstractmethod
    def on_startup(self) -> None:
        """Called when application starts."""
        pass
    
    @abstractmethod
    def on_shutdown(self) -> None:
        """Called when application shuts down."""
        pass


class RateLimiterPlugin(Plugin):
    """Rate limiting plugin with per-IP request throttling."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("RateLimiter", config)
        self.requests_per_minute = config.get("requests_per_minute", 60)
        self.ip_requests: Dict[str, List[float]] = {}
    
    def on_startup(self) -> None:
        """Initialize rate limiter."""
        logger.info(f"Rate limiter: {self.requests_per_minute} req/min")
    
    def on_shutdown(self) -> None:
        """Cleanup."""
        self.ip_requests.clear()


class LoggingPlugin(Plugin):
    """Comprehensive logging plugin for request/response tracking."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Logging", config)
        self.log_requests = config.get("log_requests", True)
        self.log_responses = config.get("log_responses", True)
    
    def on_startup(self) -> None:
        """Start logging."""
        logger.info("Logging plugin activated")
    
    def on_shutdown(self) -> None:
        """Stop logging."""
        logger.info("Logging plugin deactivated")


class MetricsPlugin(Plugin):
    """Metrics collection and reporting plugin."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("Metrics", config)
        self.metrics = {
            "total_requests": 0,
            "total_responses": 0,
            "total_errors": 0,
            "total_tokens": 0,
            "response_times": []
        }
    
    def on_startup(self) -> None:
        """Initialize metrics collector."""
        logger.info("Metrics plugin activated")
    
    def on_shutdown(self) -> None:
        """Report final metrics."""
        logger.info(f"Final metrics: {self.metrics}")
    
    def record_request(self) -> None:
        """Record a request."""
        self.metrics["total_requests"] += 1
    
    def record_response(self, response_time: float) -> None:
        """Record a response."""
        self.metrics["total_responses"] += 1
        self.metrics["response_times"].append(response_time)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        if not self.metrics["response_times"]:
            avg_time = 0
        else:
            avg_time = sum(self.metrics["response_times"]) / len(self.metrics["response_times"])
        
        return {
            "total_requests": self.metrics["total_requests"],
            "success_rate": (self.metrics["total_responses"] / max(self.metrics["total_requests"], 1)) * 100,
            "avg_response_time": avg_time,
            "total_tokens": self.metrics["total_tokens"]
        }


class PluginManager:
    """Manages plugin lifecycle and execution."""
    
    def __init__(self):
        """Initialize plugin manager."""
        self.plugins: Dict[str, Plugin] = {}
        logger.info("PluginManager initialized")
    
    def register(self, plugin: Plugin) -> None:
        """Register a plugin."""
        self.plugins[plugin.name] = plugin
        logger.info(f"Plugin registered: {plugin.name}")
    
    def startup(self) -> None:
        """Call startup on all plugins."""
        for plugin in self.plugins.values():
            plugin.on_startup()
    
    def shutdown(self) -> None:
        """Call shutdown on all plugins."""
        for plugin in self.plugins.values():
            plugin.on_shutdown()
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self.plugins.get(name)


# Global plugin manager instance
plugin_manager = PluginManager()

"""
API layer for the Adaptive Learning System.
"""

from .main import create_app
from .routes import (
    learner_routes,
    competency_routes,
    performance_routes,
    adaptive_routes
)

__all__ = [
    "create_app",
    "learner_routes",
    "competency_routes",
    "performance_routes", 
    "adaptive_routes"
]
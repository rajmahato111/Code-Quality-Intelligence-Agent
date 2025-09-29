"""Web interface for the Code Quality Intelligence Agent."""

from .api import app
from .models import *
from .auth import *

__all__ = ['app']
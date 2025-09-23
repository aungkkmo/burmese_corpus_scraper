#!/usr/bin/env python3
"""
Utility module for news scrapers
Contains common utilities for IP rotation, header rotation, and other scraping helpers
"""

from .ip_rotation import ProxyRotator
from .header_rotation import HeaderRotator

__all__ = ['ProxyRotator', 'HeaderRotator']

"""Passive network traffic capture module for Salsa2 Simulator."""
from .traffic_capture import CaptureSession, CaptureError, get_parent_targets

__all__ = ['CaptureSession', 'CaptureError', 'get_parent_targets']

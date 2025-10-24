"""
V.O.T. Guardian - Voice Authentication System
=============================================

A neuro-inspired system for detecting AI-generated voice fraud
 targeting vulnerable elderly populations.

Architecture: E2B + Red Hat OpenShift + Datadog
Security: Protocole Tenebris (auto-destruction < 100ms)
Compliance: Loi 25 Québec, GDPR, PIPEDA, SOC 2

Author: Jean-Sébastien Beaulieu
Created: October 2025
"""

__version__ = "1.0.0"
__author__ = "Jean-Sébastien Beaulieu"
__description__ = "AI Voice Fraud Detection System for Elderly Protection"

# Core modules
from .core.security.tenebris import TenebrisProtocol
from .core.monitoring.datadog_client import DatadogClient
from .core.e2b.sandbox_manager import E2BSandboxManager
from .core.audio.processor import AudioProcessor
from .core.ml.predictor import MLPredictor

__all__ = [
    'TenebrisProtocol',
    'DatadogClient',
    'E2BSandboxManager',
    'AudioProcessor',
    'MLPredictor'
]
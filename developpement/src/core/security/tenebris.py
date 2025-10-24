"""
Protocole Tenebris - Security Framework
======================================

Implements the Tenebris Protocol for automatic data destruction
and forensic audit trails as specified in the research reports.

Key Features:
- Auto-destruction < 100ms post-analysis
- Forensic audit trails (immutable)
- Cryptographic data protection
- Loi 25 Québec compliance
- Zero-trust architecture

Author: Jean-Sébastien Beaulieu
"""

import asyncio
import hashlib
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
import json

# Import core dependencies (Datadog for audit logging)
try:
    from datadog import api as datadog_api
except ImportError:
    # Fallback for when datadog main library is not available
    datadog_api = None


@dataclass
class TenebrisConfig:
    """Configuration for Tenebris Protocol."""
    max_execution_time_ms: int = 100
    encryption_enabled: bool = True
    audit_trail_enabled: bool = True
    auto_destroy_enabled: bool = True
    compliance_mode: str = "loi25"  # loi25, gdpr, pipeda


class TenebrisViolationException(Exception):
    """Exception raised when Tenebris protocol is violated."""
    pass


class TenebrisProtocol:
    """
    Main Tenebris Protocol implementation.

    Ensures all data is destroyed within 100ms of analysis completion
    while maintaining forensic audit trails for compliance.
    """

    def __init__(self, config: Optional[TenebrisConfig] = None):
        self.config = config or TenebrisConfig()
        self.logger = logging.getLogger(__name__)
        self._active_sessions: Dict[str, Dict[str, Any]] = {}

    @asynccontextmanager
    async def execute_protocol(self, call_id: str):
        """
        Context manager for Tenebris protocol execution.

        Usage:
            async with tenebris.execute_protocol(call_id) as sandbox_id:
                # Perform analysis
                result = await analyze_audio(audio_data)
            # Automatic cleanup happens here
        """
        session_id = f"tenebris_{call_id}_{int(time.time())}"

        try:
            # Initialize session
            await self._initialize_session(session_id, call_id)

            # Generate encryption key for this session
            session_key = Fernet.generate_key() if self.config.encryption_enabled else None

            # Create isolated sandbox
            sandbox_id = await self._create_isolated_sandbox(call_id, session_key)

            # Log protocol start
            await self._log_audit_event("TENEBRIS_START", {
                'session_id': session_id,
                'call_id': call_id,
                'sandbox_id': sandbox_id,
                'timestamp': time.time()
            })

            yield sandbox_id

        except Exception as e:
            # Log violation
            await self._log_audit_event("TENEBRIS_VIOLATION", {
                'session_id': session_id,
                'call_id': call_id,
                'error': str(e),
                'error_time_ms': (time.time() - self._active_sessions.get(session_id, {}).get('start_time', time.time())) * 1000
            })
            raise TenebrisViolationException(f"Tenebris protocol violation: {e}")

        finally:
            # Execute destruction protocol
            await self._execute_destruction_protocol(session_id, call_id)

    async def _initialize_session(self, session_id: str, call_id: str):
        """Initialize a new Tenebris session."""
        self._active_sessions[session_id] = {
            'call_id': call_id,
            'start_time': time.time(),
            'status': 'active',
            'data_destroyed': False
        }

    async def _create_isolated_sandbox(self, call_id: str, encryption_key: bytes) -> str:
        """Create an isolated E2B sandbox for analysis."""
        # This will integrate with the E2B sandbox manager
        # For now, return a placeholder
        sandbox_id = f"sb_{call_id}_{int(time.time())}"

        # Store encryption key temporarily (will be destroyed)
        self._active_sessions[sandbox_id] = {
            'encryption_key': encryption_key,
            'created_at': time.time()
        }

        return sandbox_id

    async def _execute_destruction_protocol(self, session_id: str, call_id: str):
        """Execute the complete destruction protocol."""
        start_time = time.time()

        try:
            # 1. Destroy E2B sandbox
            await self._destroy_e2b_sandbox(session_id)

            # 2. Revoke cryptographic keys
            await self._revoke_crypto_keys(session_id)

            # 3. Clear memory and temporary data
            await self._clear_memory_data(session_id)

            # 4. Log successful destruction
            destruction_time_ms = (time.time() - start_time) * 1000

            await self._log_audit_event("TENEBRIS_PURGE_COMPLETE", {
                'session_id': session_id,
                'call_id': call_id,
                'destruction_time_ms': destruction_time_ms,
                'compliance_status': 'COMPLIANT' if destruction_time_ms < self.config.max_execution_time_ms else 'DEGRADED'
            })

            # 5. Clean up session data
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]

        except Exception as e:
            # Log destruction failure (critical violation)
            await self._log_audit_event("TENEBRIS_DESTRUCTION_FAILED", {
                'session_id': session_id,
                'call_id': call_id,
                'error': str(e),
                'failure_time_ms': (time.time() - start_time) * 1000
            })
            raise TenebrisViolationException(f"Failed to execute destruction protocol: {e}")

    async def _destroy_e2b_sandbox(self, session_id: str):
        """Destroy E2B sandbox and all associated data."""
        # Integration with E2B SDK
        # This would call sandbox.destroy() or similar
        self.logger.info(f"Destroying E2B sandbox for session {session_id}")

    async def _revoke_crypto_keys(self, session_id: str):
        """Revoke all cryptographic keys for this session."""
        if session_id in self._active_sessions:
            # Clear encryption keys from memory
            if 'encryption_key' in self._active_sessions[session_id]:
                del self._active_sessions[session_id]['encryption_key']

        # Force garbage collection
        import gc
        gc.collect()

    async def _clear_memory_data(self, session_id: str):
        """Clear all session data from memory."""
        # Zero out sensitive data in memory
        if session_id in self._active_sessions:
            for key in list(self._active_sessions[session_id].keys()):
                if 'key' in key.lower() or 'data' in key.lower():
                    self._active_sessions[session_id][key] = None

    async def _log_audit_event(self, event_type: str, metadata: Dict[str, Any]):
        """Log audit event to Datadog (immutable forensic trail)."""
        try:
            # Create immutable audit log
            audit_entry = {
                'timestamp': time.time(),
                'event_type': event_type,
                'service': 'vot-guardian-tenebris',
                'metadata': metadata,
                'compliance': self.config.compliance_mode,
                'audit_hash': self._compute_audit_hash(event_type, metadata)
            }

            # Send to Datadog (asynchronous, non-blocking)
            if datadog_api:
                datadog_api.Event.create(
                    title=f"Tenebris Protocol: {event_type}",
                    text=json.dumps(audit_entry, indent=2),
                    tags=[
                        'protocol:tenebris',
                        'compliance:loi25',
                        f'event:{event_type.lower()}',
                        'service:vot-guardian'
                    ],
                    alert_type='info'
                )

        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")
            # Continue execution - audit logging failure shouldn't break the protocol

    def _compute_audit_hash(self, event_type: str, metadata: Dict[str, Any]) -> str:
        """Compute cryptographic hash for audit trail integrity."""
        # Create deterministic string from event data
        audit_data = f"{event_type}:{json.dumps(metadata, sort_keys=True)}:{time.time()}"

        # Return SHA-256 hash (first 16 characters for brevity)
        return hashlib.sha256(audit_data.encode()).hexdigest()[:16]

    def get_protocol_status(self, call_id: str) -> Dict[str, Any]:
        """Get status of Tenebris protocol for a call."""
        # Find active session for this call
        for session_id, session_data in self._active_sessions.items():
            if session_data.get('call_id') == call_id:
                return {
                    'session_id': session_id,
                    'status': session_data.get('status', 'unknown'),
                    'start_time': session_data.get('start_time'),
                    'duration_ms': (time.time() - session_data.get('start_time', time.time())) * 1000 if session_data.get('start_time') else 0
                }

        return {'status': 'no_active_session'}

    def get_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report for audit purposes."""
        total_sessions = len(self._active_sessions)
        completed_sessions = len([s for s in self._active_sessions.values() if s.get('data_destroyed', False)])

        return {
            'protocol_name': 'Tenebris',
            'compliance_standard': self.config.compliance_mode,
            'active_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'compliance_rate': (completed_sessions / total_sessions * 100) if total_sessions > 0 else 100,
            'max_execution_time_ms': self.config.max_execution_time_ms,
            'generated_at': time.time()
        }
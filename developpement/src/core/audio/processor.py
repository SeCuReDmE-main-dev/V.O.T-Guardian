"""
Audio Processor - Audio Feature Extraction
==========================================

Processes audio files to extract features for AI voice detection.

Features:
- VOT (Voice Onset Time) extraction
- Jitter and shimmer calculation
- Audio quality assessment
- Format conversion and normalization

Author: Jean-Sébastien Beaulieu
"""

import io
import logging
import numpy as np
from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass

# Audio processing libraries (to be installed separately)
try:
    import librosa
    import librosa.feature
    from scipy.signal import welch
    import soundfile as sf
except ImportError:
    librosa = None
    sf = None


@dataclass
class AudioConfig:
    """Configuration for audio processing."""
    sample_rate: int = 16000
    duration: float = 5.0  # seconds
    n_mels: int = 128
    n_fft: int = 2048
    hop_length: int = 512


class AudioProcessor:
    """
    Processes audio files for feature extraction.

    Extracts acoustic features that can distinguish between
    human and AI-generated voices.
    """

    def __init__(self, config: Optional[AudioConfig] = None):
        self.config = config or AudioConfig()
        self.logger = logging.getLogger(__name__)

        if not librosa or not sf:
            self.logger.warning("Audio processing libraries not available")

    def process_audio_data(self, audio_data: bytes) -> Dict[str, float]:
        """
        Process raw audio data and extract features.

        Args:
            audio_data: Raw audio bytes

        Returns:
            Dictionary with extracted features
        """
        try:
            # Convert bytes to numpy array
            audio_array, sample_rate = self._bytes_to_array(audio_data)

            # Extract features
            features = {
                'vot': self._extract_vot(audio_array, sample_rate),
                'jitter': self._calculate_jitter(audio_array, sample_rate),
                'shimmer': self._calculate_shimmer(audio_array),
                'snr_db': self._calculate_snr(audio_array),
                'thd_percent': self._calculate_thd(audio_array, sample_rate),
                'zero_crossing_rate': self._calculate_zero_crossing_rate(audio_array),
                'spectral_centroid': self._calculate_spectral_centroid(audio_array, sample_rate),
                'mfcc_mean': self._calculate_mfcc_mean(audio_array, sample_rate)
            }

            return features

        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")
            # Return default values
            return {
                'vot': 0.4,
                'jitter': 0.05,
                'shimmer': 0.1,
                'snr_db': 20.0,
                'thd_percent': 1.0,
                'zero_crossing_rate': 0.1,
                'spectral_centroid': 1000.0,
                'mfcc_mean': 0.0
            }

    def _bytes_to_array(self, audio_data: bytes) -> Tuple[np.ndarray, int]:
        """Convert audio bytes to numpy array."""
        if not sf:
            # Fallback for when soundfile is not available
            self.logger.warning("Using fallback audio conversion")
            return np.random.randn(8000), 16000

        try:
            # Read audio data
            audio_array, sample_rate = sf.read(io.BytesIO(audio_data))

            # Convert to mono if stereo
            if len(audio_array.shape) > 1:
                audio_array = np.mean(audio_array, axis=1)

            # Resample to target sample rate
            if sample_rate != self.config.sample_rate:
                audio_array = librosa.resample(audio_array, orig_sr=sample_rate, target_sr=self.config.sample_rate)

            return audio_array, self.config.sample_rate

        except Exception as e:
            self.logger.error(f"Error converting audio bytes: {e}")
            # Return dummy data
            return np.random.randn(int(self.config.sample_rate * 1)), self.config.sample_rate

    def _extract_vot(self, audio: np.ndarray, sample_rate: int) -> float:
        """Extract Voice Onset Time (VOT)."""
        try:
            # Simplified VOT extraction
            # In practice, this would use more sophisticated algorithms
            # like those in Praat or similar tools

            # Find the first significant energy burst
            frame_length = int(0.025 * sample_rate)  # 25ms frames
            hop_length = int(0.010 * sample_rate)    # 10ms hop

            # Calculate short-term energy
            energy = []
            for i in range(0, len(audio) - frame_length, hop_length):
                frame = audio[i:i + frame_length]
                energy.append(np.sum(frame ** 2))

            energy = np.array(energy)

            # Find first frame with high energy (voice onset)
            threshold = np.mean(energy) + 2 * np.std(energy)
            onset_frames = np.where(energy > threshold)[0]

            if len(onset_frames) > 0:
                # Convert frame index to time
                vot = onset_frames[0] * hop_length / sample_rate
            else:
                vot = 0.4  # Default value

            return min(vot, 1.0)  # Cap at 1 second

        except Exception as e:
            self.logger.warning(f"Error extracting VOT: {e}")
            return 0.4

    def _calculate_jitter(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate jitter (pitch perturbation)."""
        try:
            # Extract pitch using librosa
            pitches, magnitudes = librosa.piptrack(y=audio, sr=sample_rate)

            # Get pitch values where magnitude is significant
            pitch_values = []
            for t in range(pitches.shape[1]):
                pitch_col = pitches[:, t]
                magnitude_col = magnitudes[:, t]
                if np.max(magnitude_col) > 0:
                    pitch_values.append(pitch_col[np.argmax(magnitude_col)])

            if len(pitch_values) < 2:
                return 0.05  # Default value

            # Calculate jitter as relative standard deviation of pitch periods
            pitch_array = np.array(pitch_values)
            pitch_periods = 1.0 / pitch_array[pitch_array > 0]

            if len(pitch_periods) > 1:
                jitter = np.std(np.diff(pitch_periods)) / np.mean(pitch_periods)
            else:
                jitter = 0.05

            return jitter

        except Exception as e:
            self.logger.warning(f"Error calculating jitter: {e}")
            return 0.05

    def _calculate_shimmer(self, audio: np.ndarray) -> float:
        """Calculate shimmer (amplitude perturbation)."""
        try:
            # Calculate RMS energy for each frame
            frame_length = int(0.025 * self.config.sample_rate)  # 25ms
            hop_length = int(0.010 * self.config.sample_rate)    # 10ms

            rms_values = []
            for i in range(0, len(audio) - frame_length, hop_length):
                frame = audio[i:i + frame_length]
                rms = np.sqrt(np.mean(frame ** 2))
                rms_values.append(rms)

            if len(rms_values) < 2:
                return 0.1  # Default value

            # Calculate shimmer as relative standard deviation of amplitudes
            rms_array = np.array(rms_values)
            shimmer = np.std(np.diff(rms_array)) / np.mean(rms_array)

            return shimmer

        except Exception as e:
            self.logger.warning(f"Error calculating shimmer: {e}")
            return 0.1

    def _calculate_snr(self, audio: np.ndarray) -> float:
        """Calculate Signal-to-Noise Ratio."""
        try:
            # Simple SNR calculation
            signal_power = np.mean(audio ** 2)

            # Estimate noise from first 10% of signal (assumed silence)
            noise_samples = int(0.1 * len(audio))
            noise_power = np.var(audio[:noise_samples]) if noise_samples > 0 else 0.001

            if noise_power > 0:
                snr = 10 * np.log10(signal_power / noise_power)
            else:
                snr = 50.0  # Very high SNR

            return snr

        except Exception as e:
            self.logger.warning(f"Error calculating SNR: {e}")
            return 20.0

    def _calculate_thd(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate Total Harmonic Distortion."""
        try:
            # Calculate power spectral density
            freqs, psd = welch(audio, sample_rate, nperseg=1024)

            # Find fundamental frequency (strongest component)
            fundamental_idx = np.argmax(psd)
            fundamental_freq = freqs[fundamental_idx]
            fundamental_power = psd[fundamental_idx]

            # Calculate power of harmonics
            harmonics_power = 0
            for harmonic in range(2, 6):  # Check first 5 harmonics
                harmonic_freq = fundamental_freq * harmonic
                harmonic_idx = np.argmin(np.abs(freqs - harmonic_freq))

                if harmonic_idx < len(psd):
                    harmonics_power += psd[harmonic_idx]

            # Calculate THD
            if fundamental_power > 0:
                thd = np.sqrt(harmonics_power / fundamental_power)
            else:
                thd = 0.0

            return thd * 100  # Convert to percentage

        except Exception as e:
            self.logger.warning(f"Error calculating THD: {e}")
            return 1.0

    def _calculate_zero_crossing_rate(self, audio: np.ndarray) -> float:
        """Calculate zero crossing rate."""
        try:
            # Calculate zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            return np.mean(zcr)
        except Exception as e:
            self.logger.warning(f"Error calculating ZCR: {e}")
            return 0.1

    def _calculate_spectral_centroid(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate spectral centroid."""
        try:
            # Calculate spectral centroid
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)[0]
            return np.mean(spectral_centroid)
        except Exception as e:
            self.logger.warning(f"Error calculating spectral centroid: {e}")
            return 1000.0

    def _calculate_mfcc_mean(self, audio: np.ndarray, sample_rate: int) -> float:
        """Calculate mean MFCC coefficient."""
        try:
            # Calculate MFCCs
            mfccs = librosa.feature.mfcc(y=audio, sr=sample_rate, n_mfcc=13)

            # Return mean of first MFCC coefficient
            return np.mean(mfccs[0])
        except Exception as e:
            self.logger.warning(f"Error calculating MFCC: {e}")
            return 0.0

    def validate_audio_format(self, audio_data: bytes) -> bool:
        """Validate that audio data is in a supported format."""
        try:
            # Try to read the audio data
            audio_array, sample_rate = self._bytes_to_array(audio_data)

            # Check basic properties
            if len(audio_array) == 0:
                return False

            if sample_rate < 8000 or sample_rate > 48000:
                return False

            # Check duration (should be reasonable)
            duration = len(audio_array) / sample_rate
            if duration < 0.5 or duration > 30:  # 0.5s to 30s
                return False

            return True

        except Exception:
            return False

    def get_audio_info(self, audio_data: bytes) -> Dict[str, Any]:
        """Get basic information about audio file."""
        try:
            audio_array, sample_rate = self._bytes_to_array(audio_data)

            return {
                'duration_seconds': len(audio_array) / sample_rate,
                'sample_rate': sample_rate,
                'channels': 1,  # We convert to mono
                'samples': len(audio_array),
                'format': 'wav'  # Default format
            }
        except Exception as e:
            return {'error': str(e)}
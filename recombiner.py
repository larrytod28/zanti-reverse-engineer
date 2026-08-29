"""
recombiner.py

Take what you learned. Make something new.

The Reverse Engineer does not merely observe.
The Reverse Engineer experiments.

Break it. Reassemble it. See what happens.
"""

import librosa
import soundfile as sf
import numpy as np
from typing import List, Tuple, Optional
import pyloudnorm


class AudioRecombiner:
    """
    Extract elements from audio. Recombine them in new ways.
    
    Not remixing. Not mashups. Not borrowing.
    
    Reverse engineering in action.
    
    Take the parts apart. Understand the relationships.
    Then see what else is possible.
    """
    
    def __init__(self, sr: int = 22050):
        """
        Initialize the recombiner.
        
        Args:
            sr: Sample rate for all operations.
        """
        self.sr = sr
        self.meter = pyloudnorm.Meter(sr)
    
    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """
        Load an audio file.
        
        Returns:
            (audio_waveform, sample_rate)
        """
        y, sr = librosa.load(audio_path, sr=self.sr)
        return y, sr
    
    def isolate_harmonic(self, audio_path: str) -> np.ndarray:
        """
        Extract the sustained, harmonic content.
        
        Useful for: extracting melodies, chord progressions, pads.
        """
        y, sr = self.load_audio(audio_path)
        D = librosa.stft(y)
        H, P = librosa.decompose.hpss(D, margin=2.0)
        harmonic = librosa.istft(H)
        return harmonic
    
    def isolate_percussive(self, audio_path: str) -> np.ndarray:
        """
        Extract the rhythmic, percussive content.
        
        Useful for: drums, attacks, rhythmic elements.
        """
        y, sr = self.load_audio(audio_path)
        D = librosa.stft(y)
        H, P = librosa.decompose.hpss(D, margin=2.0)
        percussive = librosa.istft(P)
        return percussive
    
    def isolate_frequency_range(self, audio_path: str, 
                                  freq_min: int = 0, 
                                  freq_max: int = 8000) -> np.ndarray:
        """
        Extract only a specific frequency band.
        
        Args:
            freq_min: Minimum frequency (Hz)
            freq_max: Maximum frequency (Hz)
        
        Example:
            bass = isolate_frequency_range('track.mp3', freq_min=0, freq_max=250)
            mids = isolate_frequency_range('track.mp3', freq_min=250, freq_max=4000)
            highs = isolate_frequency_range('track.mp3', freq_min=4000, freq_max=22050)
        """
        y, sr = self.load_audio(audio_path)
        
        # Design a bandpass filter
        from scipy.signal import butter, filtfilt
        
        nyquist = sr / 2.0
        low = freq_min / nyquist
        high = freq_max / nyquist
        
        # Clamp to valid range
        low = max(0.01, low)
        high = min(0.99, high)
        
        if low >= high:
            return np.zeros_like(y)
        
        b, a = butter(4, [low, high], btype='band')
        filtered = filtfilt(b, a, y)
        
        return filtered
    
    def time_stretch(self, audio: np.ndarray, rate: float) -> np.ndarray:
        """
        Change the speed without changing pitch.
        
        Args:
            audio: Audio waveform
            rate: Speed factor (2.0 = twice as fast, 0.5 = half as fast)
        
        Returns:
            Time-stretched audio.
        """
        return librosa.effects.time_stretch(audio, rate=rate)
    
    def pitch_shift(self, audio: np.ndarray, n_steps: int) -> np.ndarray:
        """
        Change the pitch without changing speed.
        
        Args:
            audio: Audio waveform
            n_steps: Number of semitones to shift (positive = up, negative = down)
        
        Returns:
            Pitch-shifted audio.
        """
        return librosa.effects.pitch_shift(audio, sr=self.sr, n_steps=n_steps)
    
    def normalize_loudness(self, audio: np.ndarray, target_loudness: float = -20.0) -> np.ndarray:
        """
        Normalize audio to a target loudness (LUFS).
        
        Args:
            audio: Audio waveform
            target_loudness: Target loudness in LUFS (typical: -20 for streaming, -14 for mastering)
        
        Returns:
            Loudness-normalized audio.
        """
        loudness = self.meter.integrated_loudness(audio)
        if loudness == -np.inf:
            return audio
        
        loudness_normalized = pyloudnorm.normalize(audio, loudness, target_loudness)
        return loudness_normalized
    
    def crossfade(self, audio1: np.ndarray, audio2: np.ndarray, 
                  crossfade_duration: float = 2.0) -> np.ndarray:
        """
        Crossfade between two audio segments.
        
        Args:
            audio1: First audio segment
            audio2: Second audio segment
            crossfade_duration: Duration of crossfade in seconds
        
        Returns:
            Concatenated audio with crossfade.
        """
        crossfade_samples = int(crossfade_duration * self.sr)
        
        if crossfade_samples > len(audio1) or crossfade_samples > len(audio2):
            # If crossfade is longer than either audio, just concatenate
            return np.concatenate([audio1, audio2])
        
        # Create fade out and fade in curves
        fade_out = np.linspace(1.0, 0.0, crossfade_samples)
        fade_in = np.linspace(0.0, 1.0, crossfade_samples)
        
        # Apply fades
        end_of_first = audio1[-crossfade_samples:] * fade_out
        start_of_second = audio2[:crossfade_samples] * fade_in
        
        # Combine
        transition = end_of_first + start_of_second
        
        # Construct result
        result = np.concatenate([
            audio1[:-crossfade_samples],
            transition,
            audio2[crossfade_samples:]
        ])
        
        return result
    
    def layer(self, audio_list: List[np.ndarray], weights: Optional[List[float]] = None) -> np.ndarray:
        """
        Layer multiple audio segments on top of each other.
        
        Args:
            audio_list: List of audio waveforms (all should be same length)
            weights: Optional list of amplitude weights (default: equal weights)
        
        Returns:
            Layered audio.
        """
        if not audio_list:
            return np.array([])
        
        if weights is None:
            weights = [1.0 / len(audio_list)] * len(audio_list)
        
        # Pad all to the same length
        max_length = max(len(a) for a in audio_list)
        padded = []
        for audio, weight in zip(audio_list, weights):
            padded_audio = np.pad(audio, (0, max_length - len(audio)))
            padded.append(padded_audio * weight)
        
        result = np.sum(padded, axis=0)
        return result
    
    def export(self, audio: np.ndarray, output_path: str, normalize: bool = True):
        """
        Export audio to a file.
        
        Args:
            audio: Audio waveform
            output_path: Path to save (.wav, .mp3, etc.)
            normalize: Whether to normalize to -1dB peak
        """
        if normalize:
            # Normalize to prevent clipping
            max_val = np.max(np.abs(audio))
            if max_val > 0:
                audio = audio * (0.99 / max_val)
        
        sf.write(output_path, audio, self.sr)
        print(f"Exported to {output_path}")
    
    def experiment(self, base_audio_path: str, output_path: str):
        """
        Example experiment workflow.
        
        This demonstrates the Reverse Engineer's method:
        1. Decompose
        2. Analyze
        3. Recombine
        4. Export
        """
        print(f"\n=== Reverse Engineering Experiment ===")
        print(f"Source: {base_audio_path}\n")
        
        # Step 1: Decompose
        print("Step 1: Decomposing...")
        harmonic = self.isolate_harmonic(base_audio_path)
        percussive = self.isolate_percussive(base_audio_path)
        bass = self.isolate_frequency_range(base_audio_path, freq_min=0, freq_max=250)
        
        print("  ✓ Harmonic extracted")
        print("  ✓ Percussive extracted")
        print("  ✓ Bass extracted")
        
        # Step 2: Transform
        print("\nStep 2: Transforming...")
        harmonic_shifted = self.pitch_shift(harmonic, n_steps=2)
        percussive_sped_up = self.time_stretch(percussive, rate=1.2)
        
        print("  ✓ Harmonic pitched up 2 semitones")
        print("  ✓ Percussive sped up 20%")
        
        # Step 3: Recombine
        print("\nStep 3: Recombining...")
        recombined = self.layer([
            bass,
            harmonic_shifted,
            percussive_sped_up,
        ])
        
        print("  ✓ Elements layered")
        
        # Step 4: Normalize and export
        print("\nStep 4: Normalizing and exporting...")
        recombined = self.normalize_loudness(recombined, target_loudness=-20.0)
        self.export(recombined, output_path, normalize=True)
        
        print(f"\n=== Experiment Complete ===\n")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 2:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        
        recombiner = AudioRecombiner()
        recombiner.experiment(input_file, output_file)
    else:
        print("Usage: python recombiner.py <input_audio> <output_audio>")
        print("\nExample:")
        print("  python recombiner.py track.mp3 experiment.wav")

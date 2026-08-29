"""
analyzer.py

Break down audio files. See what is actually happening.

The Reverse Engineer does not enter the room pretending to know everything.
The Reverse Engineer enters the room looking for relationships.

What talks to what? What depends on what? What changed?
"""

import librosa
import numpy as np
from typing import Tuple, List, Dict


class AudioAnalyzer:
    """
    Decompose audio into its constituent parts.
    
    Not theory. Not assumptions.
    Observation.
    """
    
    def __init__(self, audio_path: str, sr: int = 22050):
        """
        Load an audio file.
        
        Args:
            audio_path: Path to audio file (mp3, wav, flac, etc.)
            sr: Sample rate. 22050 is standard for music analysis.
        """
        self.audio_path = audio_path
        self.sr = sr
        self.y, self.sr = librosa.load(audio_path, sr=sr)
        self.duration = librosa.get_duration(y=self.y, sr=self.sr)
        
    def extract_tempo(self) -> Tuple[float, np.ndarray]:
        """
        What is the rhythm?
        
        Returns:
            (tempo_in_bpm, beat_frames)
        """
        onset_env = librosa.onset.onset_strength(y=self.y, sr=self.sr)
        tempo, beats = librosa.beat.beat_track(onset_envelope=onset_env, sr=self.sr)
        return float(tempo), beats
    
    def frequency_profile(self, n_fft: int = 2048) -> Dict[str, np.ndarray]:
        """
        What frequencies dominate?
        
        Returns a dictionary with:
            - frequencies: Frequency bins (Hz)
            - magnitude: Magnitude at each frequency (averaged over time)
            - power: Power spectrogram
        """
        D = librosa.stft(self.y, n_fft=n_fft)
        magnitude = np.abs(D)
        power = magnitude ** 2
        
        # Average magnitude across time
        avg_magnitude = np.mean(magnitude, axis=1)
        
        # Frequency bins
        frequencies = librosa.fft_frequencies(sr=self.sr, n_fft=n_fft)
        
        return {
            'frequencies': frequencies,
            'magnitude': avg_magnitude,
            'power': power
        }
    
    def detect_change_points(self, hop_length: int = 512) -> List[float]:
        """
        When does something change?
        
        Detects moments where the audio character shifts significantly.
        Could be drums entering, key change, texture shift, whatever.
        
        Returns:
            List of timestamps (in seconds) where changes occur.
        """
        # Compute chroma features (pitch content)
        chroma = librosa.feature.chroma_cqt(y=self.y, sr=self.sr, hop_length=hop_length)
        
        # Compute novelty (difference between consecutive frames)
        novelty = np.sqrt(np.sum(np.diff(chroma, axis=1) ** 2, axis=0))
        
        # Find peaks in novelty
        from scipy import signal
        peaks, _ = signal.find_peaks(novelty, height=np.median(novelty) * 1.5)
        
        # Convert frame indices to time
        times = librosa.frames_to_time(peaks, sr=self.sr, hop_length=hop_length)
        
        return sorted([float(t) for t in times if t < self.duration])
    
    def spectral_centroid(self, hop_length: int = 512) -> np.ndarray:
        """
        How does the timbral center of gravity move over time?
        
        High centroid = bright. Low centroid = dark.
        
        Returns:
            Array of spectral centroids (in Hz) over time.
        """
        return librosa.feature.spectral_centroid(y=self.y, sr=self.sr, hop_length=hop_length)[0]
    
    def zero_crossing_rate(self, hop_length: int = 512) -> np.ndarray:
        """
        How much high-frequency content?
        
        Zero crossings indicate presence of high frequencies.
        High ZCR = noisy/percussive. Low ZCR = smooth/sustained.
        
        Returns:
            Array of zero crossing rates over time.
        """
        return librosa.feature.zero_crossing_rate(self.y, hop_length=hop_length)[0]
    
    def extract_mfcc(self, n_mfcc: int = 13) -> np.ndarray:
        """
        What does this sound like, perceptually?
        
        MFCCs (Mel-Frequency Cepstral Coefficients) capture
        the aspects of sound that human ears actually care about.
        
        Returns:
            Array of shape (n_mfcc, time_steps)
        """
        return librosa.feature.mfcc(y=self.y, sr=self.sr, n_mfcc=n_mfcc)
    
    def harmonic_percussive_separation(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Separate harmonic (sustained) from percussive (rhythmic) content.
        
        Returns:
            (harmonic_waveform, percussive_waveform)
        """
        D = librosa.stft(self.y)
        H, P = librosa.decompose.hpss(D)
        
        harmonic = librosa.istft(H)
        percussive = librosa.istft(P)
        
        return harmonic, percussive
    
    def get_summary(self) -> Dict:
        """
        Quick snapshot of what is happening in this audio.
        
        Returns a dictionary with key observations.
        """
        tempo, beats = self.extract_tempo()
        freq_profile = self.frequency_profile()
        changes = self.detect_change_points()
        
        # Find dominant frequency
        dominant_freq_idx = np.argmax(freq_profile['magnitude'])
        dominant_freq = freq_profile['frequencies'][dominant_freq_idx]
        
        return {
            'duration_seconds': self.duration,
            'tempo_bpm': tempo,
            'number_of_beats': len(beats),
            'dominant_frequency_hz': float(dominant_freq),
            'number_of_detected_changes': len(changes),
            'change_points_seconds': [float(t) for t in changes],
        }


if __name__ == '__main__':
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        analyzer = AudioAnalyzer(audio_file)
        summary = analyzer.get_summary()
        
        print(f"\n=== Reverse Engineering: {audio_file} ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")
        print()
    else:
        print("Usage: python analyzer.py <audio_file>")
        print("Supported formats: mp3, wav, flac, ogg, etc.")

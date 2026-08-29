"""
example_full_workflow.py

A complete example of reverse engineering music.

This demonstrates the method:
1. Give me the thing
2. Let me touch it
3. Let me see what talks to what
4. Figure out what is supposed to happen vs. what actually happened
5. Experiment with recombination

Run this with:
    python example_full_workflow.py <audio_file>
"""

import sys
from analyzer import AudioAnalyzer
from midi_dissect import MIDIReverseEngineer
from recombiner import AudioRecombiner


def analyze_audio(audio_path: str):
    """
    Step 1: Load an audio file and understand what is happening.
    """
    print(f"\n{'='*60}")
    print(f"REVERSE ENGINEERING: {audio_path}")
    print(f"{'='*60}\n")
    
    print("STEP 1: AUDIO ANALYSIS")
    print("-" * 60)
    
    analyzer = AudioAnalyzer(audio_path)
    summary = analyzer.get_summary()
    
    print(f"Duration: {summary['duration_seconds']:.2f} seconds")
    print(f"Tempo: {summary['tempo_bpm']:.1f} BPM")
    print(f"Number of beats: {summary['number_of_beats']}")
    print(f"Dominant frequency: {summary['dominant_frequency_hz']:.1f} Hz")
    print(f"Detected change points: {summary['number_of_detected_changes']}")
    
    if summary['change_points_seconds']:
        print(f"\nMoments where something changed:")
        for moment in summary['change_points_seconds'][:5]:  # First 5
            print(f"  • {moment:.2f}s")
    
    print()
    
    # Deep dive: spectral content
    print("SPECTRAL ANALYSIS")
    print("-" * 60)
    
    freq_profile = analyzer.frequency_profile()
    
    # Find the dominant frequency band
    import numpy as np
    freq_bins = freq_profile['frequencies']
    magnitudes = freq_profile['magnitude']
    
    # What frequencies are most prominent?
    top_5_indices = np.argsort(magnitudes)[-5:][::-1]
    
    print("Top 5 frequency regions:")
    for i, idx in enumerate(top_5_indices, 1):
        freq = freq_bins[idx]
        mag = magnitudes[idx]
        
        # Categorize
        if freq < 250:
            category = "BASS"
        elif freq < 2000:
            category = "MIDS"
        elif freq < 8000:
            category = "HIGHS"
        else:
            category = "PRESENCE"
        
        print(f"  {i}. {freq:.1f} Hz ({category})")
    
    print()
    
    # HPSS decomposition
    print("HARMONIC vs PERCUSSIVE")
    print("-" * 60)
    
    harmonic, percussive = analyzer.harmonic_percussive_separation()
    
    harmonic_energy = np.sum(harmonic ** 2)
    percussive_energy = np.sum(percussive ** 2)
    total_energy = harmonic_energy + percussive_energy
    
    harmonic_pct = (harmonic_energy / total_energy) * 100
    percussive_pct = (percussive_energy / total_energy) * 100
    
    print(f"Harmonic content: {harmonic_pct:.1f}%")
    print(f"Percussive content: {percussive_pct:.1f}%")
    
    print()
    
    return analyzer


def analyze_midi(midi_path: str):
    """
    Step 2: If a MIDI file exists, understand the harmonic structure.
    """
    try:
        print("STEP 2: MIDI ANALYSIS")
        print("-" * 60)
        
        engineer = MIDIReverseEngineer(midi_path)
        summary = engineer.get_summary()
        
        print(f"Total tracks: {summary['total_tracks']}")
        print(f"Total notes: {summary['total_notes']}")
        print(f"Note range: {summary['note_range'][0]} to {summary['note_range'][1]}")
        print(f"Unique notes: {summary['unique_notes']}")
        print(f"Chords detected: {summary['number_of_chords']}")
        
        print(f"\nNote inventory:")
        notes = engineer.note_inventory()
        for note_num in sorted(notes.keys()):
            note_name = engineer.note_name(note_num)
            count = notes[note_num]
            print(f"  {note_name}: {count} times")
        
        print(f"\nFirst 10 chords:")
        chords = engineer.extract_chords()
        for time, chord_notes in chords[:10]:
            chord_str = " - ".join(chord_notes)
            print(f"  {time:.2f}s: {chord_str}")
        
        print()
        return engineer
        
    except Exception as e:
        print(f"(No MIDI file or error reading MIDI: {e})")
        print()
        return None


def experiment(audio_path: str):
    """
    Step 3: Experiment with what we learned.
    """
    print("STEP 3: EXPERIMENTAL RECOMBINATION")
    print("-" * 60)
    
    recombiner = AudioRecombiner()
    
    print("Extracting components...")
    try:
        harmonic = recombiner.isolate_harmonic(audio_path)
        percussive = recombiner.isolate_percussive(audio_path)
        bass = recombiner.isolate_frequency_range(audio_path, freq_min=0, freq_max=250)
        mids = recombiner.isolate_frequency_range(audio_path, freq_min=250, freq_max=4000)
        highs = recombiner.isolate_frequency_range(audio_path, freq_min=4000, freq_max=22050)
        
        print("  ✓ Harmonic content")
        print("  ✓ Percussive content")
        print("  ✓ Bass (0-250 Hz)")
        print("  ✓ Mids (250-4000 Hz)")
        print("  ✓ Highs (4000+ Hz)")
        
        print("\nNow you can:")
        print("  • Pitch shift the melody independently")
        print("  • Speed up the drums")
        print("  • Isolate and remix bass lines")
        print("  • Layer elements in new ways")
        print("  • Create variations of the original")
        
    except Exception as e:
        print(f"  (Error during extraction: {e})")
    
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python example_full_workflow.py <audio_file> [midi_file]")
        print("\nExample:")
        print("  python example_full_workflow.py track.mp3")
        print("  python example_full_workflow.py track.mp3 composition.mid")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    midi_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Run the reverse engineering workflow
    analyze_audio(audio_path)
    
    if midi_path:
        analyze_midi(midi_path)
    
    experiment(audio_path)
    
    print("="*60)
    print("THE REVERSE ENGINEER'S WORKBENCH")
    print("="*60)
    print("""
Now that you have decomposed the audio:

1. EXPLORE: Load the modules in Python and inspect deeper
   
   from analyzer import AudioAnalyzer
   a = AudioAnalyzer('track.mp3')
   mfcc = a.extract_mfcc()  # What does it sound like?
   
2. EXPERIMENT: Try transformations
   
   from recombiner import AudioRecombiner
   r = AudioRecombiner()
   bass = r.isolate_frequency_range('track.mp3', 0, 250)
   hi_bass = r.pitch_shift(bass, n_steps=12)  # Octave up
   
3. RECOMBINE: Layer new combinations
   
   new_track = r.layer([bass, harmonic_shifted, drums])
   r.export(new_track, 'experiment.wav')

The machine is always more interesting once you remove the cover.

Give it the thing. Touch it. See what talks to what.

That is enough to begin.
    """)


if __name__ == '__main__':
    main()

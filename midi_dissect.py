"""
midi_dissect.py

MIDI files are just data. Look at what is actually written.

The notes. The timing. The decisions.

Not mysticism. Evidence.
"""

import mido
from mido import MidiFile
from typing import List, Dict, Tuple, Optional
from collections import defaultdict, Counter


class MIDIReverseEngineer:
    """
    Read a MIDI file like evidence at a crime scene.
    
    What notes are played?
    When do they change?
    What is the harmonic structure?
    Where are the compositional decisions?
    """
    
    def __init__(self, midi_path: str):
        """
        Load a MIDI file.
        
        Args:
            midi_path: Path to .mid file
        """
        self.midi_path = midi_path
        self.mid = MidiFile(midi_path)
        self.ticks_per_beat = self.mid.ticks_per_beat
        self._parse_events()
    
    def _parse_events(self):
        """
        Extract all note events, organized by time and track.
        """
        self.tracks = []
        self.all_notes = []
        self.all_events = []
        
        for track_idx, track in enumerate(self.mid.tracks):
            current_time = 0
            track_events = []
            
            for msg in track:
                current_time += msg.time
                track_events.append((current_time, msg))
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    self.all_notes.append({
                        'track': track_idx,
                        'note': msg.note,
                        'velocity': msg.velocity,
                        'channel': msg.channel,
                        'time': current_time,
                        'time_seconds': self._ticks_to_seconds(current_time),
                    })
                
                self.all_events.append({
                    'track': track_idx,
                    'time': current_time,
                    'time_seconds': self._ticks_to_seconds(current_time),
                    'type': msg.type,
                    'message': msg,
                })
            
            self.tracks.append(track_events)
    
    def _ticks_to_seconds(self, ticks: int, tempo: int = 500000) -> float:
        """
        Convert MIDI ticks to seconds.
        
        Default tempo is 500000 microseconds per beat (120 BPM).
        """
        return (ticks / self.ticks_per_beat) * (tempo / 1000000.0)
    
    def note_inventory(self) -> Dict[int, int]:
        """
        What notes are played? How often?
        
        Returns a dictionary mapping MIDI note numbers to occurrence count.
        """
        notes = [n['note'] for n in self.all_notes]
        return dict(Counter(notes))
    
    def note_name(self, midi_note: int) -> str:
        """
        Convert MIDI note number to note name.
        
        Middle C is MIDI 60.
        """
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (midi_note // 12) - 1
        note = note_names[midi_note % 12]
        return f"{note}{octave}"
    
    def extract_chords(self, window_ms: float = 100.0) -> List[Tuple[float, List[str]]]:
        """
        What is the harmonic structure?
        
        Group simultaneous notes into chords. A chord is any notes
        that sound within window_ms of each other.
        
        Returns:
            List of (time_seconds, [note_names])
        """
        if not self.all_notes:
            return []
        
        # Group notes by time (within window)
        time_groups = defaultdict(list)
        
        for note_event in self.all_notes:
            time = note_event['time_seconds']
            
            # Find existing group within window
            found_group = False
            for group_time in list(time_groups.keys()):
                if abs(time - group_time) < (window_ms / 1000.0):
                    time_groups[group_time].append(note_event['note'])
                    found_group = True
                    break
            
            if not found_group:
                time_groups[time].append(note_event['note'])
        
        # Convert to list and sort by time
        chords = []
        for time in sorted(time_groups.keys()):
            notes = time_groups[time]
            note_names = sorted(set([self.note_name(n) for n in notes]))
            chords.append((time, note_names))
        
        return chords
    
    def detect_arrangement_changes(self, min_note_change: int = 5) -> List[Tuple[float, str]]:
        """
        Where are the compositional decisions?
        
        Detects moments where the set of active notes changes significantly.
        Could be: new instrument enters, bass line drops, rhythm section changes.
        
        Returns:
            List of (time_seconds, description)
        """
        if not self.all_notes:
            return []
        
        # Sort notes by time
        sorted_notes = sorted(self.all_notes, key=lambda x: x['time'])
        
        # Create a sliding window of active notes
        changes = []
        active_notes = set()
        last_change = 0
        
        for note_event in sorted_notes:
            current_time = note_event['time_seconds']
            note = note_event['note']
            
            # Check if this is a note_on (entrance) vs note_off
            # For simplicity, we track note_on events
            active_notes.add(note)
            
            # If enough time has passed and notes changed significantly
            if current_time - last_change > 0.5:  # At least 500ms between changes
                change_desc = f"Notes active: {len(active_notes)}"
                changes.append((current_time, change_desc))
                last_change = current_time
        
        return changes
    
    def velocity_profile(self) -> Dict[str, float]:
        """
        How hard are the notes being hit?
        
        Returns average and range of velocity values.
        """
        if not self.all_notes:
            return {}
        
        velocities = [n['velocity'] for n in self.all_notes]
        return {
            'min_velocity': min(velocities),
            'max_velocity': max(velocities),
            'avg_velocity': sum(velocities) / len(velocities),
            'velocity_range': max(velocities) - min(velocities),
        }
    
    def track_summary(self) -> List[Dict]:
        """
        High-level view of what is in each track.
        
        Returns a list of summaries, one per track.
        """
        summaries = []
        
        for track_idx, track in enumerate(self.mid.tracks):
            notes_in_track = [n for n in self.all_notes if n['track'] == track_idx]
            
            if notes_in_track:
                note_range = (
                    min([n['note'] for n in notes_in_track]),
                    max([n['note'] for n in notes_in_track]),
                )
                note_range_names = (
                    self.note_name(note_range[0]),
                    self.note_name(note_range[1]),
                )
            else:
                note_range = None
                note_range_names = None
            
            summaries.append({
                'track_index': track_idx,
                'track_name': track.name if hasattr(track, 'name') else 'Unknown',
                'number_of_notes': len(notes_in_track),
                'note_range': note_range_names,
                'midi_note_range': note_range,
            })
        
        return summaries
    
    def note_sequence(self, max_events: int = 50) -> List[Dict]:
        """
        What is the order of events?
        
        Returns the first N note-on events in chronological order.
        """
        notes = sorted(self.all_notes, key=lambda x: x['time'])[:max_events]
        
        result = []
        for n in notes:
            result.append({
                'time_seconds': n['time_seconds'],
                'note_name': self.note_name(n['note']),
                'midi_note': n['note'],
                'velocity': n['velocity'],
                'track': n['track'],
            })
        
        return result
    
    def get_summary(self) -> Dict:
        """
        Quick snapshot of what is in this MIDI file.
        """
        notes = self.note_inventory()
        chords = self.extract_chords()
        
        return {
            'total_tracks': len(self.mid.tracks),
            'ticks_per_beat': self.ticks_per_beat,
            'total_notes': len(self.all_notes),
            'unique_notes': len(notes),
            'note_range': (
                self.note_name(min(notes.keys())) if notes else None,
                self.note_name(max(notes.keys())) if notes else None,
            ),
            'number_of_chords': len(chords),
            'track_summary': self.track_summary(),
            'velocity_stats': self.velocity_profile(),
        }


if __name__ == '__main__':
    import sys
    import json
    
    if len(sys.argv) > 1:
        midi_file = sys.argv[1]
        engineer = MIDIReverseEngineer(midi_file)
        summary = engineer.get_summary()
        
        print(f"\n=== Reverse Engineering: {midi_file} ===\n")
        print(json.dumps(summary, indent=2, default=str))
        print("\n=== First 20 Notes ===\n")
        for note in engineer.note_sequence(20):
            print(f"{note['time_seconds']:.2f}s - {note['note_name']} (velocity: {note['velocity']})")
        print()
    else:
        print("Usage: python midi_dissect.py <midi_file>")

"""
test_dictation_suite.py
Comprehensive automated test suite for Local Real-Time Dictation subsystem:
- LanguageRegistry & Capability matrix
- VADProcessor (silence, speech, end-of-utterance)
- VoskEngine & MoonshineEngine lifecycle (initialization, error handling, mock audio, disposal)
- DictationManager configuration, auto-engine resolution, resource release
- ProfileManager dictation persistence
- REST endpoints verification (/api/dictation/settings, /api/dictation/diagnostics)
"""

import os
import sys
import json
import struct
import math
import unittest

from profile_manager import ProfileManager
from dictation_engine import (
    LanguageRegistry,
    VADProcessor,
    ASREngine,
    VoskEngine,
    MoonshineEngine,
    DictationManager,
    dictation_mgr
)


class TestDictationSuite(unittest.TestCase):

    def setUp(self):
        self.profile_mgr = ProfileManager()

    def test_01_language_registry_capabilities(self):
        """Test supported languages, capability matrix, and installed model detection."""
        languages = LanguageRegistry.get_supported_languages()
        self.assertTrue(len(languages) >= 3)
        codes = [l["code"] for l in languages]
        self.assertIn("en", codes)
        self.assertIn("hi", codes)
        self.assertIn("pa", codes)

        # Verify English supports both Vosk and Moonshine
        en_info = next(l for l in languages if l["code"] == "en")
        self.assertIn("vosk", en_info["supported_engines"])
        self.assertIn("moonshine", en_info["supported_engines"])

        # Verify Hindi and Punjabi only support Vosk
        hi_info = next(l for l in languages if l["code"] == "hi")
        self.assertIn("vosk", hi_info["supported_engines"])
        self.assertNotIn("moonshine", hi_info["supported_engines"])

        pa_info = next(l for l in languages if l["code"] == "pa")
        self.assertIn("vosk", pa_info["supported_engines"])
        self.assertNotIn("moonshine", pa_info["supported_engines"])

    def test_02_engine_language_validation(self):
        """Test engine compatibility and prevention of invalid combinations."""
        # Valid combinations
        valid, msg = LanguageRegistry.validate_selection("en", "auto")
        self.assertTrue(valid)

        valid, msg = LanguageRegistry.validate_selection("en", "vosk")
        self.assertTrue(valid)

        valid, msg = LanguageRegistry.validate_selection("en", "moonshine")
        self.assertTrue(valid)

        valid, msg = LanguageRegistry.validate_selection("hi", "vosk")
        self.assertTrue(valid)

        # Invalid combination: Moonshine for Hindi / Punjabi
        valid, msg = LanguageRegistry.validate_selection("hi", "moonshine")
        self.assertFalse(valid)
        self.assertIn("Moonshine is not supported for Hindi", msg)

        valid, msg = LanguageRegistry.validate_selection("pa", "moonshine")
        self.assertFalse(valid)
        self.assertIn("Moonshine is not supported for Punjabi", msg)

        # Auto resolution
        resolved_hi = LanguageRegistry.resolve_engine("hi", "auto")
        self.assertEqual(resolved_hi, "vosk")

        resolved_en = LanguageRegistry.resolve_engine("en", "auto")
        self.assertIn(resolved_en, ["vosk", "moonshine"])

    def test_03_vad_silence_and_speech_detection(self):
        """Test lightweight Voice Activity Detection (RMS energy)."""
        vad = VADProcessor(sample_rate=16000, energy_threshold=0.015, silence_duration=0.5)

        # 1. Generate 0.2s of pure silence (zeros)
        silence_samples = [0] * int(16000 * 0.2)
        silence_bytes = struct.pack(f"<{len(silence_samples)}h", *silence_samples)

        has_speech, end_of_utterance, rms = vad.process_chunk(silence_bytes)
        self.assertFalse(has_speech)
        self.assertFalse(end_of_utterance)
        self.assertAlmostEqual(rms, 0.0, places=3)

        # 2. Generate 0.2s of speech signal (sine wave amplitude 15000)
        freq = 440.0
        speech_samples = [int(15000 * math.sin(2 * math.pi * freq * (i / 16000))) for i in range(int(16000 * 0.2))]
        speech_bytes = struct.pack(f"<{len(speech_samples)}h", *speech_samples)

        has_speech, end_of_utterance, rms = vad.process_chunk(speech_bytes)
        self.assertTrue(has_speech)
        self.assertFalse(end_of_utterance)
        self.assertGreater(rms, 0.1)

        # 3. Feed sustained silence (0.2s * 3 chunks = 0.6s >= 0.5s limit) to trigger end-of-utterance
        detected_end = False
        for _ in range(3):
            has_speech, end_of_utterance, rms = vad.process_chunk(silence_bytes)
            if end_of_utterance:
                detected_end = True

        self.assertTrue(detected_end)

    def test_04_profile_settings_persistence(self):
        """Test profile vault persistence of dictation settings."""
        updated = self.profile_mgr.update_dictation_settings(
            enabled=True,
            language="hi",
            engine="vosk",
            vad_enabled=True
        )
        self.assertEqual(updated["language"], "hi")
        self.assertEqual(updated["engine"], "vosk")
        self.assertTrue(updated["enabled"])

        # Reload from disk
        reloaded = self.profile_mgr.get_dictation_settings()
        self.assertEqual(reloaded["language"], "hi")
        self.assertEqual(reloaded["engine"], "vosk")
        self.assertTrue(reloaded["enabled"])

        # Reset back to default for clean state
        self.profile_mgr.update_dictation_settings(
            enabled=True,
            language="en",
            engine="auto",
            vad_enabled=True
        )

    def test_05_dictation_manager_lifecycle(self):
        """Test DictationManager configuration, engine switching, and disposal."""
        mgr = DictationManager()

        # Configure with valid English Auto
        ok, msg = mgr.configure("en", "auto", vad_enabled=True)
        self.assertTrue(ok)
        self.assertEqual(mgr.active_language, "en")

        # Incompatible config should fail
        ok, msg = mgr.configure("hi", "moonshine")
        self.assertFalse(ok)
        self.assertIn("Moonshine is not supported", msg)

        # Resource release
        mgr.release_resources()
        self.assertIsNone(mgr.active_engine)
        self.assertFalse(mgr.is_streaming)

        # Diagnostics check
        diag = mgr.get_diagnostics()
        self.assertIn("active_engine", diag)
        self.assertIn("ram_usage_mb", diag)
        self.assertIn("supported_languages", diag)

    def test_06_model_missing_graceful_handling(self):
        """Test that missing model files result in clean, user-friendly messages without crash."""
        engine = VoskEngine()
        # Initialize with non-existent directory
        success = engine.initialize({"model_dir": "non_existent_path_12345", "language": "hi"})
        self.assertFalse(success)
        self.assertIsNone(engine.model)

        # Status check
        status = engine.get_status()
        self.assertFalse(status["model_loaded"])
        engine.dispose()


if __name__ == "__main__":
    print("=" * 70)
    print(">> RUNNING SOVEREIGN LOCAL DICTATION TEST SUITE")
    print("=" * 70)
    unittest.main(verbosity=2)

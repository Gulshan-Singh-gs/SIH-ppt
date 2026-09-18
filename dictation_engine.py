"""
dictation_engine.py
Local Real-Time Dictation / Speech-to-Text Subsystem for Sovereign AI Workbench.
100% On-Premise, Zero-Cloud, CPU-Optimized.
Supports Vosk and Moonshine ONNX engines behind a unified ASREngine abstraction.
"""

import os
import sys
import json
import time
import math
import struct
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("DictationEngine")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("[Dictation] %(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(ch)

# Base models directory path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")


class LanguageRegistry:
    """
    Capability matrix for Languages, Models, and Engines.
    Prevents invalid combinations (e.g. Moonshine + Hindi).
    Determines available models and validates user configuration.
    """
    
    # Supported language capabilities
    LANGUAGES = {
        "en": {
            "name": "English",
            "supported_engines": ["vosk", "moonshine"],
            "vosk_model_dir": os.path.join(MODELS_DIR, "vosk", "en"),
            "moonshine_model_dir": os.path.join(MODELS_DIR, "moonshine", "tiny")
        },
        "hi": {
            "name": "Hindi (हिन्दी)",
            "supported_engines": ["vosk"],
            "vosk_model_dir": os.path.join(MODELS_DIR, "vosk", "hi"),
            "moonshine_model_dir": None
        },
        "pa": {
            "name": "Punjabi (ਪੰਜਾਬੀ)",
            "supported_engines": ["vosk"],
            "vosk_model_dir": os.path.join(MODELS_DIR, "vosk", "pa"),
            "moonshine_model_dir": None
        }
    }

    @classmethod
    def get_supported_languages(cls) -> List[Dict[str, Any]]:
        result = []
        for code, details in cls.LANGUAGES.items():
            result.append({
                "code": code,
                "name": details["name"],
                "supported_engines": details["supported_engines"],
                "models_installed": cls.check_installed_models(code)
            })
        return result

    @classmethod
    def check_installed_models(cls, lang_code: str) -> Dict[str, bool]:
        if lang_code not in cls.LANGUAGES:
            return {"vosk": False, "moonshine": False}
        
        info = cls.LANGUAGES[lang_code]
        vosk_installed = False
        if info["vosk_model_dir"] and os.path.isdir(info["vosk_model_dir"]):
            # Check if directory is not empty
            vosk_installed = len(os.listdir(info["vosk_model_dir"])) > 0
            
        moonshine_installed = False
        if info["moonshine_model_dir"] and os.path.isdir(info["moonshine_model_dir"]):
            moonshine_installed = len(os.listdir(info["moonshine_model_dir"])) > 0
            
        return {
            "vosk": vosk_installed,
            "moonshine": moonshine_installed
        }

    @classmethod
    def validate_selection(cls, lang: str, engine: str) -> Tuple[bool, str]:
        """
        Validates if an engine selection is valid for the given language.
        Engine can be 'auto', 'vosk', or 'moonshine'.
        """
        if lang not in cls.LANGUAGES:
            return False, f"Unsupported language: {lang}"
            
        lang_info = cls.LANGUAGES[lang]
        
        if engine == "auto":
            return True, "Valid"
            
        if engine not in lang_info["supported_engines"]:
            engine_title = engine.capitalize()
            return False, f"{engine_title} is not supported for {lang_info['name']}. Please select another engine or use Auto."
            
        return True, "Valid"

    @classmethod
    def resolve_engine(cls, lang: str, requested_engine: str) -> str:
        """
        Resolves 'auto' to a compatible engine.
        Moonshine is preferred for English (real-time neural accuracy), Vosk for others.
        Falls back to available models.
        """
        if requested_engine in ["vosk", "moonshine"]:
            return requested_engine
            
        # 'auto' logic:
        if lang == "en":
            installed = cls.check_installed_models(lang)
            if installed.get("moonshine"):
                return "moonshine"
            return "vosk"
        return "vosk"


class VADProcessor:
    """
    Lightweight energy-based Voice Activity Detector (RMS thresholding).
    Identifies silence vs speech and end-of-utterance without heavy ML overhead.
    Allows low-end devices to conserve CPU during silent pauses.
    """
    def __init__(self, sample_rate: int = 16000, energy_threshold: float = 0.012, silence_duration: float = 0.8):
        self.sample_rate = sample_rate
        self.energy_threshold = energy_threshold
        self.silence_duration = silence_duration
        self.silence_samples_limit = int(sample_rate * silence_duration)
        self.consecutive_silence_samples = 0
        self.is_speaking = False

    def reset(self):
        self.consecutive_silence_samples = 0
        self.is_speaking = False

    def process_chunk(self, pcm_bytes: bytes) -> Tuple[bool, bool, float]:
        """
        Processes 16-bit Mono PCM raw bytes.
        Returns: (has_speech, is_end_of_utterance, rms_energy)
        """
        if not pcm_bytes:
            return False, False, 0.0

        # Unpack 16-bit signed integers
        num_samples = len(pcm_bytes) // 2
        if num_samples == 0:
            return False, False, 0.0

        try:
            samples = struct.unpack(f"<{num_samples}h", pcm_bytes[:num_samples*2])
        except Exception:
            return True, False, 1.0  # Fallback: treat as speech if unpack fails

        # Calculate Root Mean Square (RMS) energy normalized to [0.0, 1.0]
        sum_sq = sum(s * s for s in samples)
        rms = math.sqrt(sum_sq / num_samples) / 32768.0

        has_speech = rms >= self.energy_threshold

        end_of_utterance = False
        if has_speech:
            self.consecutive_silence_samples = 0
            self.is_speaking = True
        else:
            if self.is_speaking:
                self.consecutive_silence_samples += num_samples
                if self.consecutive_silence_samples >= self.silence_samples_limit:
                    end_of_utterance = True
                    self.is_speaking = False
                    self.consecutive_silence_samples = 0

        return has_speech, end_of_utterance, rms


class ASREngine(ABC):
    """
    Abstract Base Class for local interchangeable speech-to-text engines.
    """
    @abstractmethod
    def initialize(self, model_config: Dict[str, Any]) -> bool:
        """Loads and prepares the local model into memory."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Prepares session state for recording."""
        pass

    @abstractmethod
    def process_audio(self, pcm_chunk: bytes) -> Dict[str, Any]:
        """
        Accepts 16kHz 16-bit mono PCM bytes.
        Returns dict: {'type': 'partial'|'final'|'none', 'text': '...', 'latency_ms': float}
        """
        pass

    @abstractmethod
    def flush(self) -> Dict[str, Any]:
        """Flushes any remaining buffered audio and produces final transcript."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops active recording session."""
        pass

    @abstractmethod
    def dispose(self) -> None:
        """Unloads model weights from memory to free low-end CPU/RAM."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Returns engine diagnostics and state."""
        pass


class VoskEngine(ASREngine):
    """
    Vosk ASR Adapter.
    Ultra-lightweight Kaldi-based offline streaming ASR.
    Supports English, Hindi, Punjabi, etc.
    """
    def __init__(self):
        self.model = None
        self.recognizer = None
        self.model_path = None
        self.language = None
        self.is_active = False
        self.last_partial = ""
        self.last_latency = 0.0

    def initialize(self, model_config: Dict[str, Any]) -> bool:
        try:
            import vosk
            vosk.SetLogLevel(-1) # Suppress verbose Kaldi C++ output
        except ImportError:
            logger.error("Vosk library is not installed.")
            return False

        model_dir = model_config.get("model_dir")
        self.language = model_config.get("language", "en")

        if not model_dir or not os.path.exists(model_dir):
            logger.error(f"Vosk model directory does not exist: {model_dir}")
            return False

        try:
            t0 = time.perf_counter()
            logger.info(f"Loading Vosk model from: {model_dir}")
            self.model = vosk.Model(model_dir)
            self.model_path = model_dir
            load_time = (time.perf_counter() - t0) * 1000
            logger.info(f"Vosk model loaded successfully in {load_time:.1f}ms")
            return True
        except Exception as e:
            logger.error(f"Failed to load Vosk model: {e}")
            self.model = None
            return False

    def start(self) -> None:
        if not self.model:
            raise RuntimeError("Cannot start Vosk session: Model is not initialized.")
        import vosk
        self.recognizer = vosk.KaldiRecognizer(self.model, 16000.0)
        self.recognizer.SetWords(True)
        self.last_partial = ""
        self.is_active = True

    def process_audio(self, pcm_chunk: bytes) -> Dict[str, Any]:
        if not self.recognizer or not self.is_active:
            return {"type": "none", "text": "", "latency_ms": 0.0}

        t0 = time.perf_counter()
        
        # AcceptWaveform returns True when Kaldi hits silence or final sentence boundary
        if self.recognizer.AcceptWaveform(pcm_chunk):
            res_str = self.recognizer.Result()
            self.last_latency = (time.perf_counter() - t0) * 1000
            try:
                res_json = json.loads(res_str)
                text = res_json.get("text", "").strip()
                if text:
                    self.last_partial = ""
                    return {"type": "final", "text": text, "latency_ms": round(self.last_latency, 2)}
            except Exception:
                pass
        else:
            partial_str = self.recognizer.PartialResult()
            self.last_latency = (time.perf_counter() - t0) * 1000
            try:
                p_json = json.loads(partial_str)
                text = p_json.get("partial", "").strip()
                if text and text != self.last_partial:
                    self.last_partial = text
                    return {"type": "partial", "text": text, "latency_ms": round(self.last_latency, 2)}
            except Exception:
                pass

        return {"type": "none", "text": "", "latency_ms": round(self.last_latency, 2)}

    def flush(self) -> Dict[str, Any]:
        if not self.recognizer:
            return {"type": "none", "text": "", "latency_ms": 0.0}
            
        t0 = time.perf_counter()
        final_str = self.recognizer.FinalResult()
        lat = (time.perf_counter() - t0) * 1000
        self.last_partial = ""
        try:
            f_json = json.loads(final_str)
            text = f_json.get("text", "").strip()
            if text:
                return {"type": "final", "text": text, "latency_ms": round(lat, 2)}
        except Exception:
            pass
        return {"type": "none", "text": "", "latency_ms": round(lat, 2)}

    def stop(self) -> None:
        self.is_active = False
        self.recognizer = None

    def dispose(self) -> None:
        self.stop()
        self.model = None
        logger.info("Vosk engine disposed and memory released.")

    def get_status(self) -> Dict[str, Any]:
        return {
            "engine": "vosk",
            "model_loaded": self.model is not None,
            "language": self.language,
            "model_path": self.model_path,
            "last_latency_ms": self.last_latency
        }


class MoonshineEngine(ASREngine):
    """
    Moonshine ONNX Adapter.
    Ultra-lightweight real-time neural speech-to-text powered by ONNX Runtime.
    Processes audio segments using Moonshine Tiny/Base models.
    """
    def __init__(self):
        self.model = None
        self.model_path = None
        self.language = "en"
        self.audio_buffer = bytearray()
        self.last_transcribed_text = ""
        self.is_active = False
        self.last_latency = 0.0

    def initialize(self, model_config: Dict[str, Any]) -> bool:
        model_dir = model_config.get("model_dir")
        self.language = model_config.get("language", "en")

        try:
            import moonshine_onnx
        except ImportError:
            logger.error("useful-moonshine-onnx is not installed.")
            return False

        try:
            t0 = time.perf_counter()
            logger.info(f"Initializing Moonshine ONNX model from: {model_dir or 'huggingface cache / default tiny'}")
            
            # If local directory exists and contains model files, load from path
            if model_dir and os.path.isdir(model_dir) and os.path.exists(os.path.join(model_dir, "encoder_model.onnx")):
                self.model = moonshine_onnx.MoonshineOnnxModel(models_dir=model_dir)
                self.model_path = model_dir
            else:
                # Load default tiny model
                self.model = moonshine_onnx.MoonshineOnnxModel(model_name="moonshine/tiny")
                self.model_path = "moonshine/tiny"

            load_time = (time.perf_counter() - t0) * 1000
            logger.info(f"Moonshine ONNX model loaded successfully in {load_time:.1f}ms")
            return True
        except Exception as e:
            logger.error(f"Failed to load Moonshine model: {e}")
            self.model = None
            return False

    def start(self) -> None:
        if not self.model:
            raise RuntimeError("Cannot start Moonshine session: Model is not initialized.")
        self.audio_buffer.clear()
        self.last_transcribed_text = ""
        self.is_active = True

    def process_audio(self, pcm_chunk: bytes) -> Dict[str, Any]:
        if not self.is_active or not self.model:
            return {"type": "none", "text": "", "latency_ms": 0.0}

        self.audio_buffer.extend(pcm_chunk)
        
        # Moonshine expects audio slices. To provide real-time streaming partials,
        # we process when we accumulate at least 0.5s (8000 samples = 16000 bytes) of speech.
        if len(self.audio_buffer) >= 16000 * 2 * 0.75: # every 0.75s
            return self._run_inference(is_final=False)

        return {"type": "none", "text": "", "latency_ms": self.last_latency}

    def _run_inference(self, is_final: bool = False) -> Dict[str, Any]:
        if not self.audio_buffer or not self.model:
            return {"type": "none", "text": "", "latency_ms": 0.0}

        t0 = time.perf_counter()
        try:
            import numpy as np
            # Convert raw 16-bit PCM bytes to float32 normalized [-1.0, 1.0]
            num_samples = len(self.audio_buffer) // 2
            raw_ints = struct.unpack(f"<{num_samples}h", self.audio_buffer[:num_samples*2])
            float_audio = np.array(raw_ints, dtype=np.float32) / 32768.0
            
            # Generate transcript via Moonshine ONNX
            tokens = self.model.generate(float_audio[np.newaxis, :])
            text = self.model.tokenizer.decode_batch(tokens)[0].strip()

            self.last_latency = (time.perf_counter() - t0) * 1000

            if is_final:
                self.audio_buffer.clear()
                self.last_transcribed_text = ""
                return {"type": "final", "text": text, "latency_ms": round(self.last_latency, 2)}
            else:
                if text and text != self.last_transcribed_text:
                    self.last_transcribed_text = text
                    return {"type": "partial", "text": text, "latency_ms": round(self.last_latency, 2)}

        except Exception as e:
            logger.error(f"Moonshine inference error: {e}")

        return {"type": "none", "text": "", "latency_ms": round(self.last_latency, 2)}

    def flush(self) -> Dict[str, Any]:
        if not self.audio_buffer:
            return {"type": "none", "text": "", "latency_ms": 0.0}
        return self._run_inference(is_final=True)

    def stop(self) -> None:
        self.is_active = False
        self.audio_buffer.clear()

    def dispose(self) -> None:
        self.stop()
        self.model = None
        logger.info("Moonshine engine disposed and memory released.")

    def get_status(self) -> Dict[str, Any]:
        return {
            "engine": "moonshine",
            "model_loaded": self.model is not None,
            "language": self.language,
            "model_path": self.model_path,
            "last_latency_ms": self.last_latency
        }


class DictationManager:
    """
    Central Controller for Local Dictation.
    Coordinates settings, engine lifecycle, VAD, and audio streaming.
    Only loads requested models into memory and unloads them when idle to preserve low-end RAM.
    """
    def __init__(self):
        self.active_engine: Optional[ASREngine] = None
        self.active_engine_name: Optional[str] = None
        self.active_language: str = "en"
        self.vad = VADProcessor()
        self.is_streaming: bool = False
        self.vad_enabled: bool = True

    def configure(self, language: str, engine_preference: str, vad_enabled: bool = True) -> Tuple[bool, str]:
        """
        Validates and configures preferred language and engine.
        """
        valid, msg = LanguageRegistry.validate_selection(language, engine_preference)
        if not valid:
            return False, msg

        resolved_engine = LanguageRegistry.resolve_engine(language, engine_preference)
        self.active_language = language
        self.vad_enabled = vad_enabled

        # If switching engine or language, dispose old engine to conserve low-end memory
        if self.active_engine and (self.active_engine_name != resolved_engine or self.active_engine.get_status().get("language") != language):
            self.active_engine.dispose()
            self.active_engine = None
            self.active_engine_name = None

        self.active_engine_name = resolved_engine
        return True, f"Engine configured: {resolved_engine} ({language})"

    def prepare_engine(self) -> Tuple[bool, str]:
        """
        Ensures the resolved engine model is loaded into memory ready for dictation.
        """
        if self.active_engine and self.active_engine.get_status().get("model_loaded"):
            return True, "Ready"

        engine_name = self.active_engine_name or "vosk"
        lang_info = LanguageRegistry.LANGUAGES.get(self.active_language, LanguageRegistry.LANGUAGES["en"])

        if engine_name == "vosk":
            model_dir = lang_info.get("vosk_model_dir")
            engine = VoskEngine()
            loaded = engine.initialize({"model_dir": model_dir, "language": self.active_language})
            if not loaded:
                return False, f"The Vosk model for {lang_info['name']} is not installed in {model_dir}."
            self.active_engine = engine

        elif engine_name == "moonshine":
            model_dir = lang_info.get("moonshine_model_dir")
            engine = MoonshineEngine()
            loaded = engine.initialize({"model_dir": model_dir, "language": self.active_language})
            if not loaded:
                return False, f"The Moonshine model could not be loaded."
            self.active_engine = engine
        else:
            return False, f"Unsupported engine: {engine_name}"

        return True, "Engine ready"

    def start_session(self) -> Tuple[bool, str]:
        """Starts dictation session."""
        ready, msg = self.prepare_engine()
        if not ready:
            return False, msg

        try:
            self.vad.reset()
            self.active_engine.start()
            self.is_streaming = True
            return True, "Session started"
        except Exception as e:
            return False, f"Failed to start dictation session: {str(e)}"

    def process_chunk(self, pcm_chunk: bytes) -> Dict[str, Any]:
        """
        Feeds raw 16kHz PCM audio chunk from microphone through VAD and ASR engine.
        Returns transcription packet: {'type': 'partial'|'final'|'silence'|'none', 'text': '...', 'latency_ms': float}
        """
        if not self.is_streaming or not self.active_engine:
            return {"type": "none", "text": "", "latency_ms": 0.0}

        # VAD filtering
        if self.vad_enabled:
            has_speech, end_of_utterance, rms = self.vad.process_chunk(pcm_chunk)
            
            # If silence and end of utterance detected, flush active buffer
            if end_of_utterance:
                flush_res = self.active_engine.flush()
                if flush_res.get("text"):
                    return flush_res
            
            # If sustained silence and not speaking, skip ASR inference to conserve CPU
            if not has_speech and not self.vad.is_speaking:
                return {"type": "silence", "text": "", "latency_ms": 0.0, "rms": rms}

        # Process through ASR engine
        return self.active_engine.process_audio(pcm_chunk)

    def stop_session(self) -> Dict[str, Any]:
        """Stops recording session and returns any remaining final transcript."""
        if not self.active_engine:
            self.is_streaming = False
            return {"type": "none", "text": "", "latency_ms": 0.0}

        final_packet = self.active_engine.flush()
        self.active_engine.stop()
        self.is_streaming = False
        return final_packet

    def release_resources(self) -> None:
        """Fully unloads models to free memory on low-end hardware when dictation is turned off."""
        if self.active_engine:
            self.active_engine.dispose()
            self.active_engine = None
            self.active_engine_name = None
        self.is_streaming = False

    def get_diagnostics(self) -> Dict[str, Any]:
        """Lightweight diagnostic telemetry for low-end hardware verification."""
        status = {}
        if self.active_engine:
            status = self.active_engine.get_status()
        
        # Memory metrics
        ram_mb = 0.0
        try:
            import psutil
            process = psutil.Process(os.getpid())
            ram_mb = round(process.memory_info().rss / (1024 * 1024), 1)
        except Exception:
            pass

        return {
            "active_engine": self.active_engine_name or "None",
            "active_language": self.active_language,
            "is_streaming": self.is_streaming,
            "engine_status": status,
            "ram_usage_mb": ram_mb,
            "supported_languages": LanguageRegistry.get_supported_languages()
        }


# Global singleton instance
dictation_mgr = DictationManager()

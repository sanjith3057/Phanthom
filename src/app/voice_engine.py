import os
import asyncio
import edge_tts
import uuid
import re
import torch
import transformers.pytorch_utils as utils

# Monkeypatch for transformers compatibility with older TTS code
if not hasattr(utils, "isin_mps_friendly"):
    utils.isin_mps_friendly = lambda *args, **kwargs: torch.tensor([False])

# Agree to Coqui CPML license for cloning
os.environ["COQUI_TOS_AGREED"] = "1"

class VoiceEngine:
    """
    Multilingual voice engine for PHANTOM-3B.
    Persona: Pavi (Supports Fast Synth and Deep Cloning).
    """
    def __init__(self, output_dir="temp_audio"):
        self.output_dir = output_dir
        self.fast_voice = "ta-IN-PallaviNeural"
        self.clone_engine = None
        self.reference_wav = "assets/pavi_reference.wav"
        self._ensure_dir()

    def _ensure_dir(self):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _init_clone_engine(self):
        """Lazy load XTTS v2 on CPU to save VRAM."""
        if self.clone_engine is None:
            try:
                from TTS.api import TTS
                print("DEBUG: Loading XTTS-v2 Clone Engine on CPU...")
                # Force CPU to avoid 4GB VRAM OOM
                self.clone_engine = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
            except Exception as e:
                print(f"DEBUG: Failed to load Clone Engine: {e}")
                return False
        return True

    def _normalize_audio(self, wav_path):
        """Ensures the reference audio has enough volume and clarity."""
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(wav_path)
            # Normalize to -1.0 dB
            normalized_audio = audio.normalize(headroom=1.0)
            normalized_audio.export(wav_path, format="wav")
            print(f"DEBUG: Normalized reference audio at {wav_path}")
        except Exception as e:
            print(f"DEBUG: Audio normalization failed: {e}")

    def clean_text(self, text: str) -> str:
        """Removes markers like [USER], [PHANTOM] for speech."""
        text = re.sub(r"\[.*?\]", "", text)
        text = re.sub(r"> \*\*.*?\*\*", "", text)
        text = re.sub(r"`.*?`", "", text)
        return text.strip()

    async def _generate_fast(self, text: str, output_path: str):
        communicate = edge_tts.Communicate(text, self.fast_voice)
        await communicate.save(output_path)

    def synthesize(self, text: str, mode="fast") -> str:
        """
        Synthesizes text into an audio file.
        mode: 'fast' (Edge-TTS) or 'clone' (XTTS-v2)
        """
        cleaned = self.clean_text(text)
        if not cleaned:
            return ""

        filename = f"pavi_{mode}_{uuid.uuid4().hex}.mp3" if mode == "fast" else f"pavi_{mode}_{uuid.uuid4().hex}.wav"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            if mode == "clone" and os.path.exists(self.reference_wav):
                if self._init_clone_engine():
                    # Normalize before first cloning run
                    self._normalize_audio(self.reference_wav)
                    
                    # XTTS-v2 Optimized Parameters for local CPU inference
                    self.clone_engine.tts_to_file(
                        text=cleaned,
                        speaker_wav=self.reference_wav,
                        language="en", # 'en' handles Tanglish accents better than 'ta' in XTTS v2
                        file_path=filepath,
                        temperature=0.75,         # More variety, less robotic
                        length_penalty=1.0,
                        repetition_penalty=5.0,   # Avoid robotic loops
                        top_k=50,
                        top_p=0.85
                    )
                    return filepath
            
            # Fallback to Fast (Edge-TTS)
            asyncio.run(self._generate_fast(cleaned, filepath))
            return filepath
            
        except Exception as e:
            print(f"DEBUG: Voice Synthesis ({mode}) failed: {e}")
            return ""

    def cleanup(self):
        for f in os.listdir(self.output_dir):
            if f.endswith((".mp3", ".wav")):
                try:
                    os.remove(os.path.join(self.output_dir, f))
                except:
                    pass

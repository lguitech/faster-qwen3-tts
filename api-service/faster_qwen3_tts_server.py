#!/usr/bin/env python3
"""
Simple TTS API Service for Elderly Phone Platform
Based on faster-qwen3-tts with CustomVoice model

Usage:
    conda activate qwen3-tts
    cd /home/brookli/faster-qwen3-tts/api-service
    python simple_tts_server.py --port 8000
"""
import argparse
import io
import logging
import struct
import threading
from typing import Optional

import numpy as np
import soundfile as sf
import torch
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response

from faster_qwen3_tts import FasterQwen3TTS

# Configure logging (compatible with systemd journal)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
MAX_TEXT_LENGTH = 500
SUPPORTED_LANGUAGES = {"Chinese", "English"}

# Global state
app = FastAPI(title="Elderly Phone TTS Service")
tts_model: Optional[FasterQwen3TTS] = None
available_speakers: list = []
generation_lock = threading.Lock()


def convert_to_wav_bytes(audio: np.ndarray, sample_rate: int) -> bytes:
    """Convert numpy audio array to WAV format bytes."""
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)
    if audio.ndim > 1:
        audio = audio.squeeze()
    
    buf = io.BytesIO()
    sf.write(buf, audio, sample_rate, format='WAV', subtype='PCM_16')
    return buf.getvalue()


@app.on_event("startup")
async def startup_event():
    """Load TTS model on startup."""
    global tts_model, available_speakers
    
    logger.info(f"Loading TTS model: {MODEL_ID}")
    try:
        tts_model = FasterQwen3TTS.from_pretrained(
            MODEL_ID,
            device="cuda",
            dtype=torch.bfloat16,
        )
        
        # Get available speakers
        available_speakers = tts_model.model.get_supported_speakers() or []
        logger.info(f"Model loaded successfully. Available speakers: {available_speakers}")
        logger.info(f"Sample rate: {tts_model.sample_rate} Hz")
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}", exc_info=True)
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy" if tts_model is not None else "unhealthy",
        "model": MODEL_ID,
        "speakers": available_speakers
    }


@app.get("/speakers")
async def get_speakers():
    """Get list of available speakers."""
    if tts_model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    return {
        "speakers": available_speakers,
        "count": len(available_speakers)
    }


@app.get("/tts")
async def text_to_speech(
    text: str = Query(..., description="Text to synthesize (max 500 chars)"),
    speaker: str = Query(..., description="Speaker ID"),
    language: str = Query("Chinese", description="Language: Chinese or English")
):
    """
    Generate speech from text.
    
    Returns WAV audio file as binary response.
    """
    # Validate model is loaded
    if tts_model is None:
        raise HTTPException(status_code=503, detail="TTS model not loaded")
    
    # Validate text length
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Text too long ({len(text)} chars). Maximum is {MAX_TEXT_LENGTH} characters."
        )
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    # Validate language
    if language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language: {language}. Supported: {list(SUPPORTED_LANGUAGES)}"
        )
    
    # Validate speaker
    if speaker not in available_speakers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid speaker: {speaker}. Available: {available_speakers}"
        )
    
    # Generate speech with thread lock (single instance, serial processing)
    try:
        logger.info(f"Generating speech: text_len={len(text)}, speaker={speaker}, language={language}")
        
        with generation_lock:
            audio_list, sample_rate = tts_model.generate_custom_voice(
                text=text,
                speaker=speaker,
                language=language,
                max_new_tokens=2048,
            )
        
        # Convert to WAV bytes
        if not audio_list or len(audio_list[0]) == 0:
            raise RuntimeError("Generated audio is empty")
        
        wav_bytes = convert_to_wav_bytes(audio_list[0], sample_rate)
        
        logger.info(f"Speech generated successfully: {len(wav_bytes)} bytes, {sample_rate} Hz")
        
        return Response(
            content=wav_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": f"attachment; filename=tts_{speaker}.wav"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Elderly Phone TTS API Service")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8006, help="Bind port (default: 8006)")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers (default: 1)")
    args = parser.parse_args()
    
    logger.info(f"Starting TTS API service on {args.host}:{args.port}")
    logger.info(f"Model: {MODEL_ID}")
    logger.info(f"Max text length: {MAX_TEXT_LENGTH} chars")
    logger.info(f"Supported languages: {SUPPORTED_LANGUAGES}")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info"
    )


if __name__ == "__main__":
    main()

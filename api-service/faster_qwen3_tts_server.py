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
import torchaudio.functional as F
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response, StreamingResponse

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
TARGET_SAMPLE_RATE = 16000  # Target output sample rate (downsample from 24kHz)

# Global state
app = FastAPI(title="Elderly Phone TTS Service")
tts_model: Optional[FasterQwen3TTS] = None
available_speakers: list = []
generation_lock = threading.Lock()


def resample_audio(audio_24k: np.ndarray, src_sr: int = 24000, tgt_sr: int = TARGET_SAMPLE_RATE) -> np.ndarray:
    """Resample audio from source to target sample rate using torchaudio."""
    if src_sr == tgt_sr:
        return audio_24k
    
    # Convert to tensor and add batch dimension
    audio_tensor = torch.from_numpy(audio_24k).unsqueeze(0)  # Shape: [1, samples]
    
    # Resample using torchaudio (linear interpolation, fast and simple)
    audio_resampled = F.resample(audio_tensor, src_sr, tgt_sr)
    
    # Remove batch dimension and convert back to numpy
    return audio_resampled.squeeze(0).numpy()


def create_wav_header(sample_rate: int, channels: int = 1, bits_per_sample: int = 16) -> bytes:
    """Create WAV file header (44 bytes) for streaming."""
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF',                    # Chunk ID
        0xFFFFFFFF,                 # Chunk Size (unknown for streaming)
        b'WAVE',                    # Format
        b'fmt ',                    # Subchunk 1 ID
        16,                         # Subchunk 1 Size (PCM)
        1,                          # Audio Format (1 = PCM)
        channels,                   # Num Channels
        sample_rate,                # Sample Rate
        byte_rate,                  # Byte Rate
        block_align,                # Block Align
        bits_per_sample,            # Bits Per Sample
        b'data',                    # Subchunk 2 ID
        0xFFFFFFFF                  # Subchunk 2 Size (unknown for streaming)
    )
    return header


def convert_to_pcm_bytes(audio: np.ndarray) -> bytes:
    """Convert numpy audio array to 16-bit PCM bytes."""
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)
    if audio.ndim > 1:
        audio = audio.squeeze()
    
    # Convert float32 [-1.0, 1.0] to int16 [-32768, 32767]
    audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    return audio_int16.tobytes()


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
        
        # Downsample from 24kHz to 16kHz if needed
        audio_data = audio_list[0]
        if sample_rate != TARGET_SAMPLE_RATE:
            logger.debug(f"Resampling audio from {sample_rate} Hz to {TARGET_SAMPLE_RATE} Hz")
            audio_data = resample_audio(audio_data, sample_rate, TARGET_SAMPLE_RATE)
            sample_rate = TARGET_SAMPLE_RATE
        
        wav_bytes = convert_to_wav_bytes(audio_data, sample_rate)
        
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


@app.get("/tts/stream")
async def text_to_speech_streaming(
    text: str = Query(..., description="Text to synthesize (max 500 chars)"),
    speaker: str = Query(..., description="Speaker ID"),
    language: str = Query("Chinese", description="Language: Chinese or English"),
    chunk_size: int = Query(12, ge=1, le=48, description="Audio chunk size in frames (default: 12 ≈ 1s)")
):
    """
    Generate speech from text with streaming response.
    
    Returns WAV audio stream (header + PCM chunks) for real-time playback.
    Lower chunk_size = lower latency but more overhead.
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
    
    try:
        logger.info(f"Starting streaming TTS: text_len={len(text)}, speaker={speaker}, language={language}, chunk_size={chunk_size}")
        
        with generation_lock:
            # Create streaming generator
            stream_gen = tts_model.generate_custom_voice_streaming(
                text=text,
                speaker=speaker,
                language=language,
                chunk_size=chunk_size,
                max_new_tokens=2048,
            )
            
            # Get first chunk to determine sample rate and validate generation
            try:
                first_chunk, sample_rate, _ = next(stream_gen)
            except StopIteration:
                raise HTTPException(status_code=400, detail="Generation produced no output")
            
            # Downsample first chunk if needed
            if sample_rate != TARGET_SAMPLE_RATE:
                logger.debug(f"Resampling first chunk from {sample_rate} Hz to {TARGET_SAMPLE_RATE} Hz")
                first_chunk = resample_audio(first_chunk, sample_rate, TARGET_SAMPLE_RATE)
                sample_rate = TARGET_SAMPLE_RATE
            
            # Generate WAV file header with target sample rate
            wav_header = create_wav_header(sample_rate)
            
            logger.info(f"Streaming started: sample_rate={sample_rate} Hz, first_chunk_size={len(first_chunk)} samples")
            
            # Create async streaming generator
            async def audio_stream():
                # Send WAV header first
                yield wav_header
                
                # Send first audio chunk (already resampled)
                yield convert_to_pcm_bytes(first_chunk)
                
                # Send subsequent chunks
                chunk_count = 1
                for chunk, orig_sr, timing in stream_gen:
                    chunk_count += 1
                    
                    # Downsample chunk if needed
                    if orig_sr != TARGET_SAMPLE_RATE:
                        chunk = resample_audio(chunk, orig_sr, TARGET_SAMPLE_RATE)
                    
                    logger.debug(f"Streaming chunk {chunk_count}: {len(chunk)} samples")
                    yield convert_to_pcm_bytes(chunk)
                
                logger.info(f"Streaming completed: {chunk_count} chunks sent")
            
            return StreamingResponse(
                audio_stream(),
                media_type="audio/wav",
                headers={
                    "X-Sample-Rate": str(sample_rate),
                    "X-Chunk-Size": str(chunk_size),
                    "X-Content-Type-Options": "nosniff"
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Streaming TTS failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Streaming TTS failed: {str(e)}")


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

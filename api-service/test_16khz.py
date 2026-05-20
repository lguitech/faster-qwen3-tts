#!/usr/bin/env python3
"""
Test TTS API with 16kHz downsampled output.
Verifies both streaming and non-streaming endpoints.
"""
import requests
import time
import sys
import wave
import io

BASE_URL = "http://localhost:8006"


def test_non_streaming_tts(text, speaker="eric", language="Chinese", output_file=None):
    """Test non-streaming TTS and verify 16kHz output."""
    print(f"\n{'='*70}")
    print(f"Testing Non-Streaming TTS (16kHz)")
    print(f"Text: {text[:50]}..." if len(text) > 50 else f"Text: {text}")
    print(f"Speaker: {speaker}, Language: {language}")
    print(f"{'='*70}\n")
    
    start_time = time.time()
    
    try:
        response = requests.get(
            f"{BASE_URL}/tts",
            params={
                "text": text,
                "speaker": speaker,
                "language": language
            },
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            return False
        
        total_time = time.time() - start_time
        wav_bytes = response.content
        
        # Verify sample rate from WAV header
        wav_buffer = io.BytesIO(wav_bytes)
        with wave.open(wav_buffer, 'rb') as wf:
            actual_sr = wf.getframerate()
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            nframes = wf.getnframes()
            duration = nframes / actual_sr
        
        print(f"✅ Generation completed in {total_time:.3f}s")
        print(f"Audio size: {len(wav_bytes)/1024:.1f} KB")
        print(f"Sample rate: {actual_sr} Hz {'✅' if actual_sr == 16000 else '❌'}")
        print(f"Channels: {channels}")
        print(f"Duration: {duration:.2f}s")
        print(f"RTF: {duration/total_time:.2f}x")
        print(f"{'='*70}\n")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'wb') as f:
                f.write(wav_bytes)
            print(f"💾 Audio saved to: {output_file}")
        
        return actual_sr == 16000
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streaming_tts(text, speaker="eric", language="Chinese", chunk_size=12, output_file=None):
    """Test streaming TTS and verify 16kHz output."""
    print(f"\n{'='*70}")
    print(f"Testing Streaming TTS (16kHz)")
    print(f"Text: {text[:50]}..." if len(text) > 50 else f"Text: {text}")
    print(f"Speaker: {speaker}, Language: {language}, Chunk Size: {chunk_size}")
    print(f"{'='*70}\n")
    
    start_time = time.time()
    first_chunk_time = None
    
    try:
        # Make streaming request with proper headers
        response = requests.get(
            f"{BASE_URL}/tts/stream",
            params={
                "text": text,
                "speaker": speaker,
                "language": language,
                "chunk_size": chunk_size
            },
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            return False
        
        # Check sample rate from header
        sample_rate_header = response.headers.get("X-Sample-Rate")
        print(f"Response header X-Sample-Rate: {sample_rate_header} Hz")
        
        # Read WAV header (44 bytes)
        wav_header = response.raw.read(44)
        if len(wav_header) == 44:
            print(f"✅ Received WAV header ({len(wav_header)} bytes)")
            
            # Parse sample rate from WAV header (bytes 24-27)
            import struct
            wav_sr = struct.unpack('<I', wav_header[24:28])[0]
            print(f"WAV header sample rate: {wav_sr} Hz {'✅' if wav_sr == 16000 else '❌'}")
        else:
            print(f"⚠️  Unexpected header size: {len(wav_header)} bytes")
            return False
        
        # Stream and collect audio data using raw socket reading
        total_bytes = 0
        chunk_count = 0
        audio_data = wav_header  # Start with header
        
        # Use iter_lines or direct read to avoid chunked encoding issues
        while True:
            chunk = response.raw.read(4096)
            if not chunk:
                break
            
            # Record first chunk time (TTFA)
            if first_chunk_time is None:
                first_chunk_time = time.time() - start_time
                print(f"⏱️  Time to First Audio (TTFA): {first_chunk_time:.3f}s\n")
            
            audio_data += chunk
            total_bytes += len(chunk)
            chunk_count += 1
        
        # Calculate metrics
        total_time = time.time() - start_time
        audio_duration = (total_bytes - 44) / (2 * 16000)  # Subtract header, 16-bit mono at 16kHz
        
        print(f"\n{'='*70}")
        print(f"✅ Streaming completed!")
        print(f"Total time: {total_time:.3f}s")
        print(f"TTFA: {first_chunk_time:.3f}s")
        print(f"Audio duration: {audio_duration:.2f}s")
        print(f"RTF: {audio_duration/total_time:.2f}x")
        print(f"Data received: {total_bytes/1024:.1f} KB")
        print(f"Chunks received: {chunk_count}")
        print(f"{'='*70}\n")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'wb') as f:
                f.write(audio_data)
            print(f"💾 Audio saved to: {output_file}")
        
        return wav_sr == 16000
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Starting TTS 16kHz Downsample Tests\n")
    
    # Test 1: Non-streaming
    success1 = test_non_streaming_tts(
        text="您好，欢迎使用老人机语音服务。",
        speaker="eric",
        language="Chinese",
        output_file="/tmp/tts_16k_nonstream.wav"
    )
    
    # Test 2: Streaming
    success2 = test_streaming_tts(
        text="您好，欢迎使用老人机语音服务。今天天气很好。",
        speaker="eric",
        language="Chinese",
        chunk_size=12,
        output_file="/tmp/tts_16k_stream.wav"
    )
    
    # Summary
    print(f"\n{'='*70}")
    print(f"Test Summary:")
    print(f"Non-streaming 16kHz: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"Streaming 16kHz: {'✅ PASS' if success2 else '❌ FAIL'}")
    print(f"{'='*70}\n")
    
    sys.exit(0 if (success1 and success2) else 1)

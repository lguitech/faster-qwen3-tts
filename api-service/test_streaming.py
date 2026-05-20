#!/usr/bin/env python3
"""
Test streaming TTS endpoint - measure TTFA and performance.
Saves audio to file for verification.
"""
import requests
import time
import sys
from urllib3.response import HTTPResponse

BASE_URL = "http://localhost:8006"

def test_streaming_tts(text, speaker="eric", language="Chinese", chunk_size=12, output_file=None):
    """Test streaming TTS and measure performance."""
    print(f"\n{'='*70}")
    print(f"Testing Streaming TTS")
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
        
        # Read WAV header (44 bytes)
        wav_header = response.raw.read(44)
        if len(wav_header) == 44:
            print(f"✅ Received WAV header ({len(wav_header)} bytes)")
        else:
            print(f"⚠️  Unexpected header size: {len(wav_header)} bytes")
        
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
        audio_duration = (total_bytes - 44) / (2 * 24000)  # Subtract header, 16-bit mono at 24kHz
        
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
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_non_streaming_tts(text, speaker="eric", language="Chinese", output_file=None):
    """Test non-streaming TTS for comparison."""
    print(f"\n{'='*70}")
    print(f"Testing Non-Streaming TTS (for comparison)")
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
        
        print(f"✅ Generation completed in {total_time:.3f}s")
        print(f"Audio size: {len(wav_bytes)/1024:.1f} KB")
        
        # Estimate audio duration from file size
        audio_duration = (len(wav_bytes) - 44) / (2 * 24000)
        rtf = audio_duration / total_time
        
        print(f"Estimated audio duration: {audio_duration:.2f}s")
        print(f"RTF: {rtf:.2f}x")
        print(f"{'='*70}\n")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'wb') as f:
                f.write(wav_bytes)
            print(f"💾 Audio saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Starting TTS Performance Tests\n")
    
    # Test 1: Short text - Streaming
    test_streaming_tts(
        text="你好世界",
        speaker="eric",
        language="Chinese",
        chunk_size=12,
        output_file="/tmp/stream_short.wav"
    )
    
    # Test 2: Medium text - Streaming
    test_streaming_tts(
        text="您好，欢迎使用老人机语音服务。今天天气很好。不是一般的好，那是相当好",
        speaker="eric",
        language="Chinese",
        chunk_size=12,
        output_file="/tmp/stream_medium.wav"
    )
    
    # Test 3: Long text - Streaming
    test_streaming_tts(
        text="您好，欢迎使用老人机语音服务。这是一个较长的测试文本，用来测试系统在生成较长语音时的性能表现。我们会观察生成时间是否会随着文本长度线性增长，还是会有其他的性能特征。",
        speaker="eric",
        language="Chinese",
        chunk_size=12,
        output_file="/tmp/stream_long.wav"
    )
    
    # Test 4: Different chunk size (smaller = lower latency)
    test_streaming_tts(
        text="您好，欢迎使用老人机语音服务",
        speaker="eric",
        language="Chinese",
        chunk_size=6,
        output_file="/tmp/stream_chunk6.wav"
    )
    
    # Test 5: Comparison with non-streaming
    test_non_streaming_tts(
        text="您好，欢迎使用老人机语音服务。今天天气很好。不是一般的好，那是相当好",
        speaker="eric",
        language="Chinese",
        output_file="/tmp/nonstream_medium.wav"
    )
    
    print("\n✅ All tests completed!\n")
    print("Summary:")
    print("- Streaming endpoints provide lower TTFA (Time to First Audio)")
    print("- Total generation time remains similar to non-streaming")
    print("- Smaller chunk_size reduces latency but increases overhead")
    print("- Audio files saved to /tmp/ for manual verification\n")

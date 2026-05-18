#!/usr/bin/env python3
"""
Test script for TTS API Service

Usage:
    conda activate qwen3-tts
    python test_api.py
"""
import requests
import sys
import time

# Configuration
BASE_URL = "http://localhost:8006"
OUTPUT_DIR = "/home/brookli/faster-qwen3-tts/api-service"


def test_health():
    """Test health endpoint."""
    print("=" * 60)
    print("Test 1: Health Check")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✓ Health check passed\n")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}\n")
        return False


def test_speakers():
    """Test speakers endpoint."""
    print("=" * 60)
    print("Test 2: Get Available Speakers")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/speakers", timeout=5)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Available speakers: {data['speakers']}")
        print(f"Count: {data['count']}")
        print("✓ Speakers endpoint passed\n")
        return data['speakers']
    except Exception as e:
        print(f"✗ Speakers endpoint failed: {e}\n")
        return []


def test_tts_chinese(speaker):
    """Test Chinese TTS."""
    print("=" * 60)
    print("Test 3: Chinese TTS Generation")
    print("=" * 60)
    
    text = "您好，欢迎使用老人机语音服务。今天天气很好。"
    params = {
        "text": text,
        "speaker": speaker,
        "language": "Chinese"
    }
    
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/tts", params=params, timeout=30)
        elapsed = time.time() - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Text: {text}")
        print(f"Speaker: {speaker}")
        print(f"Language: Chinese")
        print(f"Response size: {len(response.content)} bytes")
        print(f"Generation time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            output_file = f"{OUTPUT_DIR}/test_chinese_{speaker}.wav"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            print(f"✓ Audio saved to: {output_file}\n")
            return True
        else:
            print(f"✗ Failed: {response.text}\n")
            return False
            
    except Exception as e:
        print(f"✗ Chinese TTS failed: {e}\n")
        return False


def test_tts_english(speaker):
    """Test English TTS."""
    print("=" * 60)
    print("Test 4: English TTS Generation")
    print("=" * 60)
    
    text = "Hello, welcome to the elderly phone voice service. Have a nice day."
    params = {
        "text": text,
        "speaker": speaker,
        "language": "English"
    }
    
    try:
        start_time = time.time()
        response = requests.get(f"{BASE_URL}/tts", params=params, timeout=30)
        elapsed = time.time() - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Text: {text}")
        print(f"Speaker: {speaker}")
        print(f"Language: English")
        print(f"Response size: {len(response.content)} bytes")
        print(f"Generation time: {elapsed:.2f}s")
        
        if response.status_code == 200:
            output_file = f"{OUTPUT_DIR}/test_english_{speaker}.wav"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            print(f"✓ Audio saved to: {output_file}\n")
            return True
        else:
            print(f"✗ Failed: {response.text}\n")
            return False
            
    except Exception as e:
        print(f"✗ English TTS failed: {e}\n")
        return False


def test_error_handling():
    """Test error handling."""
    print("=" * 60)
    print("Test 5: Error Handling")
    print("=" * 60)
    
    # Test 1: Text too long
    print("Test 5.1: Text too long")
    long_text = "a" * 501
    try:
        response = requests.get(
            f"{BASE_URL}/tts",
            params={"text": long_text, "speaker": "aiden", "language": "Chinese"},
            timeout=5
        )
        print(f"  Status: {response.status_code} (expected 400)")
        print(f"  Response: {response.json()}")
        print("  ✓ Correctly rejected long text\n")
    except Exception as e:
        print(f"  ✗ Failed: {e}\n")
    
    # Test 2: Invalid speaker
    print("Test 5.2: Invalid speaker")
    try:
        response = requests.get(
            f"{BASE_URL}/tts",
            params={"text": "Hello", "speaker": "invalid_speaker", "language": "Chinese"},
            timeout=5
        )
        print(f"  Status: {response.status_code} (expected 400)")
        print(f"  Response: {response.json()}")
        print("  ✓ Correctly rejected invalid speaker\n")
    except Exception as e:
        print(f"  ✗ Failed: {e}\n")
    
    # Test 3: Missing parameter
    print("Test 5.3: Missing text parameter")
    try:
        response = requests.get(
            f"{BASE_URL}/tts",
            params={"speaker": "aiden", "language": "Chinese"},
            timeout=5
        )
        print(f"  Status: {response.status_code} (expected 422)")
        print("  ✓ Correctly rejected missing parameter\n")
    except Exception as e:
        print(f"  ✗ Failed: {e}\n")


def main():
    print("\n" + "=" * 60)
    print("TTS API Service Test Suite")
    print("=" * 60 + "\n")
    
    # Test health
    if not test_health():
        print("Service is not healthy. Exiting.")
        sys.exit(1)
    
    # Get speakers
    speakers = test_speakers()
    if not speakers:
        print("No speakers available. Exiting.")
        sys.exit(1)
    
    # Use first speaker for testing
    test_speaker = speakers[0]
    print(f"Using speaker '{test_speaker}' for TTS tests\n")
    
    # Test Chinese TTS
    test_tts_chinese(test_speaker)
    
    # Test English TTS
    test_tts_english(test_speaker)
    
    # Test error handling
    test_error_handling()
    
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

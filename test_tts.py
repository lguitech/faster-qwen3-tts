from examples.audio import StreamPlayer  # helper from this repo's examples/
from faster_qwen3_tts import FasterQwen3TTS

model = FasterQwen3TTS.from_pretrained("Qwen/Qwen3-TTS-12Hz-0.6B-Base")
ref_audio = "ref_audio.wav"
ref_text = (
    "I'm confused why some people have super short timelines, yet at the same time are bullish on scaling up "
    "reinforcement learning atop LLMs. If we're actually close to a human-like learner, then this whole approach "
    "of training on verifiable outcomes is doomed."
)

# Streaming — yields audio chunks during generation
play = StreamPlayer()
try:
    for audio_chunk, sr, timing in model.generate_voice_clone_streaming(
        text="情况就是这么个情况，你说的什么意思？想打架吗？", language="Chinese",
        ref_audio=ref_audio, ref_text=ref_text,
        chunk_size=8,  # 8 steps ≈ 667ms of audio per chunk
    ):
        play(audio_chunk, sr)
finally:
    play.close()

# Non-streaming — returns all audio at once
audio_list, sr = model.generate_voice_clone(
    text="Hello world!", language="Chinese",
    ref_audio=ref_audio, ref_text=ref_text,
)

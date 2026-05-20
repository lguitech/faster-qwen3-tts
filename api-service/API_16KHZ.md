# TTS API 调用说明（16kHz 输出）

## 服务地址
- **URL**: `http://localhost:8006`
- **端口**: 8006

## 接口列表

### 1. 非流式合成 `/tts`
```bash
curl -o output.wav "http://localhost:8006/tts?text=你好世界&speaker=eric&language=Chinese"
```
**返回**: WAV 文件（16kHz, 16-bit PCM）

### 2. 流式合成 `/tts/stream`
```bash
curl -o output.wav "http://localhost:8006/tts/stream?text=你好世界&speaker=eric&language=Chinese&chunk_size=12"
```
**返回**: WAV 流（首块含 WAV 头，后续为 PCM 数据，16kHz）

### 3. 查询发音人 `/speakers`
```bash
curl http://localhost:8006/speakers
```

### 4. 健康检查 `/health`
```bash
curl http://localhost:8006/health
```

## 参数说明
- **text**: 待合成文本（≤500 字符）
- **speaker**: 发音人 ID（通过 `/speakers` 查询）
- **language**: Chinese 或 English
- **chunk_size**: 流式块大小（6-48，默认 12 ≈ 1秒）

## 注意事项
- 服务端自动将模型原生 24kHz 下采样至 16kHz
- 流式端点 TTFA 约 0.6-0.8 秒
- RTF 约 2.2-2.7x（生成速度是实时的 2-3 倍）

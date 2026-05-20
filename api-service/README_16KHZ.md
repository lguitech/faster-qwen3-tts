# TTS API 服务（16kHz 输出）

## 快速启动

### 1. 测试模式（开发/验证）
```bash
conda activate qwen3-tts
cd /home/brookli/faster-qwen3-tts/api-service
python faster_qwen3_tts_server.py --port 8006
```

### 2. 生产部署（systemd）
已配置 systemd 服务，使用以下命令管理：
```bash
sudo systemctl start qwen3-tts-api
sudo systemctl status qwen3-tts-api
journalctl -u qwen3-tts-api -f  # 查看实时日志
```

## 核心改动
- ✅ 服务端自动将 24kHz 下采样至 16kHz
- ✅ 同时支持流式和非流式端点
- ✅ 使用 torchaudio.functional.resample（简单高效）
- ✅ 不影响 TTFA 和 RTF 性能

## 验证测试
```bash
python test_16khz.py
```

## API 文档
详见 `API_16KHZ.md`

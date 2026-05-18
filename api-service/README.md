# TTS API Service for Elderly Phone Platform

## 启动服务
```bash
conda activate qwen3-tts
cd /home/brookli/faster-qwen3-tts/api-service
python simple_tts_server.py --port 8006
```

## API 接口
- **GET /tts?text=你好&speaker=aiden&language=Chinese** → WAV 音频
- **GET /speakers** → 可用发音人列表
- **GET /health** → 健康检查

## 参数说明
- `text`: 待合成文本（≤500字符）
- `speaker`: 发音人ID（通过 /speakers 获取）
- `language`: Chinese 或 English（默认 Chinese）

## 测试
```bash
python test_api.py
```

生成的音频保存在当前目录：`test_chinese_*.wav`, `test_english_*.wav`

## 快速调用示例
```bash
# Python
import requests
r = requests.get('http://localhost:8006/tts', params={'text':'你好','speaker':'aiden'})
open('output.wav','wb').write(r.content)

# curl
curl "http://localhost:8006/tts?text=你好&speaker=aiden" -o output.wav
```

## 可用发音人
aiden, dylan, eric, ono_anna, ryan, serena, sohee, uncle_fu, vivian

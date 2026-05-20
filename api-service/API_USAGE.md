# TTS API 调用说明

## 端点列表

### 1. 非流式端点 (原有)
```
GET /tts?text={文本}&speaker={发音人}&language={语言}
```
- **返回**: 完整 WAV 文件
- **适用**: 离线生成、简单场景
- **延迟**: 需等待全部生成完成

### 2. 流式端点 (新增) ⭐
```
GET /tts/stream?text={文本}&speaker={发音人}&language={语言}&chunk_size={块大小}
```
- **返回**: WAV 流 (文件头 + PCM 数据)
- **适用**: 实时播放、低延迟场景
- **TTFA**: ~0.6-0.8 秒 (降低 72%)
- **chunk_size**: 6(0.5s) 或 12(1s),默认 12

## 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| text | string | ✅ | - | 待合成文本 (≤500字) |
| speaker | string | ✅ | - | 发音人 ID |
| language | string | ❌ | Chinese | Chinese 或 English |
| chunk_size | int | ❌ | 12 | 流式块大小 (仅流式端点) |

## 可用发音人

`aiden`, `dylan`, `eric`, `ono_anna`, `ryan`, `serena`, `sohee`, `uncle_fu`, `vivian`

## Python 示例

### 非流式调用
```python
import requests
response = requests.get("http://localhost:8006/tts", 
    params={"text": "你好世界", "speaker": "eric"})
with open("output.wav", "wb") as f:
    f.write(response.content)
```

### 流式调用
```python
import requests
response = requests.get("http://localhost:8006/tts/stream",
    params={"text": "你好世界", "speaker": "eric", "chunk_size": 12},
    stream=True)

# 读取 WAV 头
wav_header = response.raw.read(44)

# 边接收边播放/保存
with open("output.wav", "wb") as f:
    f.write(wav_header)
    for chunk in response.raw.read(4096):
        if not chunk: break
        f.write(chunk)
```

## 性能参考

| 文本长度 | 非流式耗时 | 流式 TTFA | RTF |
|---------|-----------|----------|-----|
| 短 (4字) | ~0.6s | **0.62s** | 2.2x |
| 中 (34字) | ~2.8s | **0.77s** | 2.5x |
| 长 (82字) | ~7.6s | **0.77s** | 2.5x |

*RTF > 1 表示生成速度快于实时播放*

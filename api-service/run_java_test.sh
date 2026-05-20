#!/bin/bash
# 编译和运行 Java 流式 TTS 客户端

echo "========================================"
echo "Java 流式 TTS 客户端测试"
echo "========================================"

# 检查服务是否运行
echo -n "检查 TTS 服务状态... "
if curl -s http://localhost:8006/health | grep -q "healthy"; then
    echo "✅ 服务运行正常"
else
    echo "❌ 服务未运行，请先启动服务"
    exit 1
fi

# 编译 Java 代码
echo -e "\n📦 编译 Java 代码..."
cd /home/brookli/faster-qwen3-tts/api-service
javac StreamingTtsClient.java

if [ $? -eq 0 ]; then
    echo "✅ 编译成功"
else
    echo "❌ 编译失败"
    exit 1
fi

# 运行测试
echo -e "\n🚀 开始运行测试...\n"
java StreamingTtsClient

# 清理 class 文件
rm -f StreamingTtsClient.class

echo -e "\n✅ 测试完成!"

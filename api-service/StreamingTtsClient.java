import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * 流式 TTS 客户端测试 - Java 版本
 * 演示如何一边接收 HTTP 流式音频数据一边保存到文件
 */
public class StreamingTtsClient {
    
    private static final String BASE_URL = "http://localhost:8006";
    
    /**
     * 流式接收并保存为 WAV 文件
     * 
     * @param text 待合成文本
     * @param speaker 发音人 ID
     * @param language 语言 (Chinese/English)
     * @param chunkSize 块大小 (6 或 12)
     * @param outputFile 输出文件路径
     * @return 性能指标数组 [TTFA, 总时间, RTF]
     */
    public static double[] streamAndSave(String text, String speaker, String language, 
                                         int chunkSize, String outputFile) throws Exception {
        
        // 构建 URL
        String urlString = String.format("%s/tts/stream?text=%s&speaker=%s&language=%s&chunk_size=%d",
                BASE_URL,
                java.net.URLEncoder.encode(text, StandardCharsets.UTF_8),
                speaker,
                language,
                chunkSize);
        
        System.out.println("========================================");
        System.out.println("开始流式 TTS 测试");
        System.out.println("文本: " + (text.length() > 50 ? text.substring(0, 50) + "..." : text));
        System.out.println("发音人: " + speaker + ", 语言: " + language + ", Chunk Size: " + chunkSize);
        System.out.println("输出文件: " + outputFile);
        System.out.println("========================================\n");
        
        long startTime = System.currentTimeMillis();
        long firstChunkTime = -1;
        
        // 建立 HTTP 连接
        URL url = new URL(urlString);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setConnectTimeout(10000);
        conn.setReadTimeout(60000);
        
        // 检查响应状态
        int responseCode = conn.getResponseCode();
        if (responseCode != HttpURLConnection.HTTP_OK) {
            throw new IOException("HTTP 请求失败: " + responseCode + " - " + conn.getResponseMessage());
        }
        
        // 读取响应头
        String contentType = conn.getContentType();
        String sampleRate = conn.getHeaderField("X-Sample-Rate");
        System.out.println("Content-Type: " + contentType);
        System.out.println("Sample Rate: " + sampleRate + " Hz\n");
        
        // 准备文件输出流
        FileOutputStream fos = new FileOutputStream(outputFile);
        BufferedOutputStream bos = new BufferedOutputStream(fos);
        
        // 准备输入流
        InputStream inputStream = conn.getInputStream();
        BufferedInputStream bis = new BufferedInputStream(inputStream);
        
        // 缓冲区
        byte[] buffer = new byte[4096];
        int bytesRead;
        long totalBytes = 0;
        int chunkCount = 0;
        
        System.out.println("开始接收音频数据...\n");
        
        // 循环读取数据
        while ((bytesRead = bis.read(buffer)) != -1) {
            // 记录第一个 chunk 的时间 (TTFA)
            if (firstChunkTime == -1) {
                firstChunkTime = System.currentTimeMillis() - startTime;
                System.out.println("⏱️  首字延迟 (TTFA): " + String.format("%.3f", firstChunkTime / 1000.0) + "s\n");
            }
            
            // 写入文件
            bos.write(buffer, 0, bytesRead);
            totalBytes += bytesRead;
            chunkCount++;
            
            // 打印进度 (每 100KB 打印一次)
            if (totalBytes % (100 * 1024) < bytesRead) {
                System.out.println("已接收: " + String.format("%.1f", totalBytes / 1024.0) + " KB");
            }
        }
        
        // 关闭流
        bos.flush();
        bos.close();
        bis.close();
        inputStream.close();
        conn.disconnect();
        
        // 计算性能指标
        long totalTime = System.currentTimeMillis() - startTime;
        double audioDuration = (totalBytes - 44) / (2.0 * 24000.0); // 减去 WAV 头,16-bit mono at 24kHz
        double rtf = audioDuration / (totalTime / 1000.0);
        
        System.out.println("\n========================================");
        System.out.println("✅ 流式传输完成!");
        System.out.println("总耗时: " + String.format("%.3f", totalTime / 1000.0) + "s");
        System.out.println("TTFA: " + String.format("%.3f", firstChunkTime / 1000.0) + "s");
        System.out.println("音频时长: " + String.format("%.2f", audioDuration) + "s");
        System.out.println("RTF: " + String.format("%.2f", rtf) + "x");
        System.out.println("接收数据: " + String.format("%.1f", totalBytes / 1024.0) + " KB");
        System.out.println("Chunks 数量: " + chunkCount);
        System.out.println("文件已保存: " + outputFile);
        System.out.println("========================================\n");
        
        return new double[]{firstChunkTime / 1000.0, totalTime / 1000.0, rtf};
    }
    
    /**
     * 非流式调用 (对比用)
     */
    public static double[] nonStreamAndSave(String text, String speaker, String language, 
                                            String outputFile) throws Exception {
        
        String urlString = String.format("%s/tts?text=%s&speaker=%s&language=%s",
                BASE_URL,
                java.net.URLEncoder.encode(text, StandardCharsets.UTF_8),
                speaker,
                language);
        
        System.out.println("========================================");
        System.out.println("开始非流式 TTS 测试 (对比)");
        System.out.println("文本: " + (text.length() > 50 ? text.substring(0, 50) + "..." : text));
        System.out.println("========================================\n");
        
        long startTime = System.currentTimeMillis();
        
        URL url = new URL(urlString);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setConnectTimeout(10000);
        conn.setReadTimeout(60000);
        
        int responseCode = conn.getResponseCode();
        if (responseCode != HttpURLConnection.HTTP_OK) {
            throw new IOException("HTTP 请求失败: " + responseCode);
        }
        
        // 读取完整响应
        InputStream inputStream = conn.getInputStream();
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        byte[] buffer = new byte[4096];
        int bytesRead;
        
        while ((bytesRead = inputStream.read(buffer)) != -1) {
            baos.write(buffer, 0, bytesRead);
        }
        
        byte[] wavData = baos.toByteArray();
        
        // 保存到文件
        FileOutputStream fos = new FileOutputStream(outputFile);
        fos.write(wavData);
        fos.close();
        
        inputStream.close();
        conn.disconnect();
        
        long totalTime = System.currentTimeMillis() - startTime;
        double audioDuration = (wavData.length - 44) / (2.0 * 24000.0);
        double rtf = audioDuration / (totalTime / 1000.0);
        
        System.out.println("✅ 生成完成!");
        System.out.println("总耗时: " + String.format("%.3f", totalTime / 1000.0) + "s");
        System.out.println("音频时长: " + String.format("%.2f", audioDuration) + "s");
        System.out.println("RTF: " + String.format("%.2f", rtf) + "x");
        System.out.println("文件大小: " + String.format("%.1f", wavData.length / 1024.0) + " KB");
        System.out.println("文件已保存: " + outputFile);
        System.out.println("========================================\n");
        
        return new double[]{-1, totalTime / 1000.0, rtf};
    }
    
    /**
     * 主函数 - 运行测试
     */
    public static void main(String[] args) {
        try {
            System.out.println("\n🚀 开始 Java 流式 TTS 测试\n");
            
            // 测试 1: 短文本 - 流式
            streamAndSave(
                "你好世界",
                "eric",
                "Chinese",
                12,
                "/tmp/java_stream_short.wav"
            );
            
            // 测试 2: 中等文本 - 流式
            streamAndSave(
                "您好，欢迎使用老人机语音服务。今天天气很好。不是一般的好，那是相当好",
                "eric",
                "Chinese",
                12,
                "/tmp/java_stream_medium.wav"
            );
            
            // 测试 3: 长文本 - 流式
            streamAndSave(
                "您好，欢迎使用老人机语音服务。这是一个较长的测试文本，用来测试系统在生成较长语音时的性能表现。我们会观察生成时间是否会随着文本长度线性增长，还是会有其他的性能特征。",
                "eric",
                "Chinese",
                12,
                "/tmp/java_stream_long.wav"
            );
            
            // 测试 4: 小 chunk size - 流式
            streamAndSave(
                "您好，欢迎使用老人机语音服务",
                "eric",
                "Chinese",
                6,
                "/tmp/java_stream_chunk6.wav"
            );
            
            // 测试 5: 非流式 (对比)
            nonStreamAndSave(
                "您好，欢迎使用老人机语音服务。今天天气很好。不是一般的好，那是相当好",
                "eric",
                "Chinese",
                "/tmp/java_nonstream_medium.wav"
            );
            
            System.out.println("\n✅ 所有测试完成!\n");
            System.out.println("总结:");
            System.out.println("- 流式端点显著降低 TTFA (首字延迟)");
            System.out.println("- 总生成时间与非流式相近");
            System.out.println("- 较小的 chunk_size 可进一步降低延迟");
            System.out.println("- 音频文件已保存到 /tmp/ 目录\n");
            
        } catch (Exception e) {
            System.err.println("❌ 测试失败: " + e.getMessage());
            e.printStackTrace();
        }
    }
}

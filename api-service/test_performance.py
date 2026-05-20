#!/usr/bin/env python3
"""Performance test for TTS API"""
import requests
import time

BASE_URL = 'http://localhost:8006'

# 测试1: 短文本
print('测试1: 短文本 (10字)')
text1 = '你好世界'
start = time.time()
resp = requests.get(f'{BASE_URL}/tts', params={'text': text1, 'speaker': 'eric', 'language': 'Chinese'})
elapsed = time.time() - start
print(f'  生成时间: {elapsed:.2f}s')
print(f'  音频大小: {len(resp.content)} bytes\n')

# 测试2: 中等文本 (当前测试的文本)
print('测试2: 中等文本 (35字)')
text2 = '您好，欢迎使用老人机语音服务。今天天气很好。不是一般的好，那是相当好'
start = time.time()
resp = requests.get(f'{BASE_URL}/tts', params={'text': text2, 'speaker': 'eric', 'language': 'Chinese'})
elapsed = time.time() - start
print(f'  生成时间: {elapsed:.2f}s')
print(f'  音频大小: {len(resp.content)} bytes\n')

# 测试3: 长文本 (接近上限)
print('测试3: 长文本 (约100字)')
text3 = '您好，欢迎使用老人机语音服务。这是一个较长的测试文本，用来测试系统在生成较长语音时的性能表现。我们会观察生成时间是否会随着文本长度线性增长，还是会有其他的性能特征。'
start = time.time()
resp = requests.get(f'{BASE_URL}/tts', params={'text': text3, 'speaker': 'eric', 'language': 'Chinese'})
elapsed = time.time() - start
print(f'  生成时间: {elapsed:.2f}s')
print(f'  音频大小: {len(resp.content)} bytes\n')

# 测试4-6: 重复测试相同文本,看稳定性
for i in range(1, 4):
    print(f'测试{i+3}: 重复测试 (相同中等文本,第{i}次)')
    start = time.time()
    resp = requests.get(f'{BASE_URL}/tts', params={'text': text2, 'speaker': 'eric', 'language': 'Chinese'})
    elapsed = time.time() - start
    print(f'  生成时间: {elapsed:.2f}s\n')

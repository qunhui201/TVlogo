#!/usr/bin/env python3
import requests
import hashlib
import json
import os
import re
from datetime import datetime

# ========== 配置 ==========
REPO_OWNER = "qunhui201"
REPO_NAME = "TVlogo"
BRANCH = "main"
DIRECTORY = "history"
FILE_PATTERN = r'^(logo|tvbox_)\d{8}\.(m3u|txt)$'  # 匹配 logoMMDDHHMM.m3u 或 tvbox_MMDDHHMM.txt
OUTPUT_FILE = "duplicate_history_files.txt"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')  # 可选：设置环境变量 GITHUB_TOKEN=your_pat_token

HEADERS = {
    'Accept': 'application/vnd.github.v3+json',
    'User-Agent': 'DuplicateChecker/1.0'
}
if GITHUB_TOKEN:
    HEADERS['Authorization'] = f'token {GITHUB_TOKEN}'

def get_github_contents(repo_owner, repo_name, path, branch='main', recursive=False):
    """递归获取 GitHub 目录/文件内容"""
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}?ref={branch}"
    files = []
    try:
        response = requests.get(api_url, headers=HEADERS)
        response.raise_for_status()
        items = response.json()
        
        for item in items:
            if item['type'] == 'file' and re.match(FILE_PATTERN, item['name']):
                files.append(item)
            elif item['type'] == 'dir' and recursive:
                sub_files = get_github_contents(repo_owner, repo_name, item['path'], branch, recursive)
                files.extend(sub_files)
    except requests.exceptions.RequestException as e:
        print(f"❌ API 请求失败 {api_url}: {e}")
        return []
    return files

def get_file_content(item):
    """获取文件内容并计算 MD5 哈希"""
    try:
        content_url = item['download_url']
        response = requests.get(content_url, headers=HEADERS)
        response.raise_for_status()
        content = response.content
        md5_hash = hashlib.md5(content).hexdigest()
        preview = content.decode('utf-8', errors='ignore')[:200] + '...' if len(content) > 200 else content.decode('utf-8', errors='ignore')
        return md5_hash, preview
    except Exception as e:
        print(f"❌ 获取文件内容失败 {item['path']}: {e}")
        return None, None

def check_duplicates():
    """检查重复文件"""
    print(f"🔍 开始检查 {REPO_OWNER}/{REPO_NAME}/{DIRECTORY} 中的 logo*.m3u 和 tvbox_*.txt 重复文件...")
    start_time = datetime.now()
    
    # 获取文件列表
    files = get_github_contents(REPO_OWNER, REPO_NAME, DIRECTORY, BRANCH, recursive=True)
    if not files:
        print("❌ 未找到匹配模式的文件或目录不存在")
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(f"重复文件检查报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"仓库: {REPO_OWNER}/{REPO_NAME}/{DIRECTORY}\n")
            f.write("未找到匹配模式的文件或目录不存在\n")
        return
    
    print(f"📋 发现 {len(files)} 个目标文件")
    
    # 计算哈希并分组
    hash_map = {}
    for item in files:
        md5_hash, content_preview = get_file_content(item)
        if md5_hash:
            if md5_hash not in hash_map:
                hash_map[md5_hash] = []
            hash_map[md5_hash].append({
                'path': item['path'],
                'name': item['name'],
                'size': item['size'],
                'preview': content_preview
            })
    
    # 找出重复
    duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    count = sum(len(paths) - 1 for paths in duplicates.values())
    
    # 输出结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"重复文件检查报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"仓库: {REPO_OWNER}/{REPO_NAME}/{DIRECTORY}\n")
        f.write(f"总文件数: {len(files)}\n")
        f.write(f"重复文件数: {count}\n\n")
        
        if duplicates:
            for md5_hash, file_list in duplicates.items():
                f.write(f"哈希: {md5_hash}\n")
                f.write(f"重复文件数: {len(file_list)}\n")
                for file_info in file_list:
                    f.write(f"- 路径: {file_info['path']}\n")
                    f.write(f"  名称: {file_info['name']} (大小: {file_info['size']} bytes)\n")
                    f.write(f"  预览: {file_info['preview']}\n\n")
                f.write("---\n\n")
            print(f"✅ 发现 {count} 个重复文件，详情保存到 {OUTPUT_FILE}")
        else:
            f.write("🎉 未发现重复文件\n")
            print("🎉 未发现重复文件")
    
    end_time = datetime.now()
    print(f"⏱️ 完成，用时: {end_time - start_time}")

if __name__ == "__main__":
    check_duplicates()

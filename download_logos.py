import os
import re
import requests
from pathlib import Path
from time import sleep

# -------------------------
# 配置部分
# -------------------------
# GitHub 原始链接 md 文件夹
GITHUB_MD_RAW_URL = "https://raw.githubusercontent.com/qunhui201/TVlogo/main/md/"

# 输出根目录
output_root = Path("TVlogo_Images")
output_root.mkdir(exist_ok=True)

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"
}

# 最大重试次数
MAX_RETRY = 3

# -------------------------
# 函数部分
# -------------------------
def safe_filename(name):
    """生成安全的文件名"""
    return "".join(c if c.isalnum() or c in "_-" else "_" for c in name)

def download_image(url, save_path):
    """下载图片，失败自动重试"""
    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
            if resp.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(resp.content)
                print(f"下载成功: {save_path}")
                return True
            else:
                print(f"请求状态码 {resp.status_code}，重试 {attempt}/{MAX_RETRY}")
        except Exception as e:
            print(f"下载异常: {e}，重试 {attempt}/{MAX_RETRY}")
        sleep(1)
    print(f"下载失败: {save_path}")
    return False

# -------------------------
# 主程序
# -------------------------
# 1. 获取所有 md 文件名（这里直接列出，如果有新文件，需要更新）
md_files = [
    "01.md","02.md","03.md","04.md","05.md","06.md","07.md","08.md","09.md","10.md",
    "11.md","12.md","13.md","14.md","15.md","16.md","17.md","18.md","19.md","20.md",
    "21.md","22.md","23.md","24.md","25.md","26.md","27.md","28.md","29.md","30.md",
    "31.md","32.md","33.md","34.md","35.md","36.md","37.md","38.md","39.md","40.md",
    "41.md","42.md","43.md","44.md","45.md","46.md","47.md","48.md","49.md","50.md"
]

for md_file in md_files:
    url = GITHUB_MD_RAW_URL + md_file
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        content = resp.text
    except Exception as e:
        print(f"获取 {md_file} 失败: {e}")
        continue

    # 匹配 Markdown 标题作为子文件夹
    title_matches = re.findall(r"# 【(.+?)】", content)
    if title_matches:
        folder_title = title_matches[0]
    else:
        folder_title = md_file.replace(".md","")

    folder_path = output_root / safe_filename(folder_title)
    folder_path.mkdir(exist_ok=True)

    # 匹配所有图片链接和对应频道名
    pattern = re.compile(r"\|(.+?)\|<img src=\"(https?://.+?)\">")
    matches = pattern.findall(content)

    for channel_name, img_url in matches:
        img_name = safe_filename(channel_name) + Path(img_url).suffix
        save_path = folder_path / img_name
        if save_path.exists():
            print(f"已存在: {save_path}")
            continue
        download_image(img_url, save_path)

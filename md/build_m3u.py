#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import requests
from pathlib import Path
from collections import defaultdict

# IPTV m3u 网络文件
INPUT_URLS = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

# TVlogo 图片目录
LOGO_DIR = Path("TVlogo_Images")
OUTPUT_FILE = Path("output.m3u")

# 固定开头内容
FIXED_HEADER = '#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"'

# 分类顺序
CATEGORY_ORDER = [
    "央视频道",
    "卫视频道",
    "地方频道",
    "CIBN系列",
    "DOX系列",
    "NewTV系列",
    "iHOT系列",
    "数字频道",
    "台湾频道一",
    "台湾频道二",
    "台湾频道三",
    "其他频道"
]

# 地方频道关键词
LOCAL_KEYWORDS = ["新闻", "生活", "影视", "文体", "少儿", "都市", "公共", "教育", "剧场"]

# 下载网络 M3U 并保存到临时文件
def download_m3u(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text.splitlines()
    except Exception as e:
        print(f"⚠️ 下载失败 {url}: {e}")
        return []

# 扫描 TVlogo_Images 文件夹生成 logo_map：台标名 -> (分类, logo_path)
def build_logo_map():
    logo_map = {}
    for folder in LOGO_DIR.iterdir():
        if not folder.is_dir():
            continue
        # 分类规则
        if folder.name == "中央电视台":
            category = "央视频道"
        elif "卫视" in folder.name or folder.name == "全国卫视":
            category = "卫视频道"
        elif folder.name in ["CIBN", "DOX", "NewTV", "iHOT", "数字频道",
                             "台湾频道一", "台湾频道二", "台湾频道三"]:
            category = folder.name
        else:
            category = "地方频道"
        for file in folder.iterdir():
            if file.suffix.lower() == ".png":
                name = file.stem
                logo_map[name] = (category, file)
    return logo_map

# 解析 M3U 频道
def parse_m3u(lines):
    channels = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF"):
            name = line.split(",")[-1].strip()
            i += 1
            if i < len(lines):
                url = lines[i].strip()
                channels.append((name, url))
        i += 1
    return channels

# 根据 logo_map 判断频道分类
def classify_channel(name, logo_map):
    # 优先 logo 匹配
    if name in logo_map:
        return logo_map[name][0]

    # CCTV/央视频道
    if "CCTV" in name or "CETV" in name or "CGTN" in name:
        return "央视频道"

    # 卫视频道
    if "卫视" in name:
        return "卫视频道"

    # 地方频道规则：地名 + LOCAL_KEYWORDS
    for keyword in LOCAL_KEYWORDS:
        if keyword in name:
            return "地方频道"

    # 第三方系列匹配
    series = ["CIBN", "DOX", "NewTV", "iHOT", "数字频道", "台湾频道一", "台湾频道二", "台湾频道三"]
    for s in series:
        if s in name:
            return s

    # 默认其他频道
    return "其他频道"

# 生成 EXTINF 条目
def build_entry(name, url, category, logo_map):
    logo_file = None
    if name in logo_map:
        logo_file = logo_map[name][1]
    if logo_file:
        logo_url = f"https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/{logo_file.relative_to(LOGO_DIR)}".replace("\\", "/")
    else:
        logo_url = f"https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/其他/{name}.png"
    return f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_url}" group-title="{category}",{name}\n{url}'

# ---------- 主程序 ----------
logo_map = build_logo_map()

all_channels = []
for url in INPUT_URLS:
    lines = download_m3u(url)
    all_channels.extend(parse_m3u(lines))

# 合并重复频道 URL
channel_dict = defaultdict(list)  # name -> list of (name, url, category)
for name, url in all_channels:
    category = classify_channel(name, logo_map)
    channel_dict[name].append((name, url, category))

# 按分类顺序整理输出
output_entries = []
for cat in CATEGORY_ORDER:
    for name, entries in channel_dict.items():
        if entries[0][2] == cat:
            for _, url, category in entries:
                output_entries.append(build_entry(name, url, category, logo_map))

# 输出到文件
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(FIXED_HEADER + "\n")
    f.write(f'#EXTINF:-1 🕘️更新时间, {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
    for line in output_entries:
        f.write(line + "\n")

print(f"✅ 已生成 {OUTPUT_FILE}")

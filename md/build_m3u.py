#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import requests
from pathlib import Path
from collections import defaultdict

# IPTV m3u URL 列表
INPUT_FILES = [
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

# 扫描 TVlogo_Images 文件夹生成 folder -> 分类映射
def build_folder_map():
    folder_map = {}
    for folder in LOGO_DIR.iterdir():
        if not folder.is_dir():
            continue
        name = folder.name
        if name == "中央电视台":
            folder_map[name] = "央视频道"
        elif name == "全国卫视" or "卫视" in name:
            folder_map[name] = "卫视频道"
        elif name in ["CIBN", "DOX", "NewTV", "iHOT", "数字频道",
                      "台湾频道一", "台湾频道二", "台湾频道三"]:
            folder_map[name] = name
        else:
            folder_map[name] = "地方频道"
    return folder_map

# 解析 m3u 文件或 URL
def parse_m3u(files):
    channels = []
    for file in files:
        if file.startswith("http://") or file.startswith("https://"):
            r = requests.get(file)
            r.encoding = 'utf-8'
            lines = r.text.splitlines()
        else:
            with open(file, encoding="utf-8") as f:
                lines = f.read().splitlines()
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

# 根据 logo 文件夹判断分类
def classify_channel(name, folder_map):
    for folder_name, category in folder_map.items():
        logo_path = LOGO_DIR / folder_name / f"{name}.png"
        if logo_path.exists():
            return category
    # 地名+卫视组合归卫视频道
    if "卫视" in name:
        return "卫视频道"
    # CCTV 系列归央视频道
    if any(x in name for x in ["CCTV", "CETV", "CGTN"]):
        return "央视频道"
    # 其他未匹配的归其他频道
    return "其他频道"

# 生成 m3u 条目
def build_entry(name, url, category, folder_map):
    logo_file = None
    for folder_name, cat in folder_map.items():
        if cat == category:
            candidate = LOGO_DIR / folder_name / f"{name}.png"
            if candidate.exists():
                logo_file = candidate
                break
    if logo_file:
        logo_url = f"https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/{logo_file.relative_to(LOGO_DIR)}".replace("\\", "/")
    else:
        logo_url = f"https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/其他/{name}.png"
    return f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_url}" group-title="{category}",{name}\n{url}'

# ---------- 主程序 ----------
if __name__ == "__main__":
    folder_map = build_folder_map()
    channels = parse_m3u(INPUT_FILES)

    # 合并重复频道 URL
    channel_dict = defaultdict(list)  # name -> list of (name, url, category)
    for name, url in channels:
        category = classify_channel(name, folder_map)
        channel_dict[name].append((name, url, category))

    # 按分类顺序整理输出
    output_entries = []
    for cat in CATEGORY_ORDER:
        for name, entries in channel_dict.items():
            if entries[0][2] == cat:
                for _, url, category in entries:
                    output_entries.append(build_entry(name, url, category, folder_map))

    # 输出到文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(FIXED_HEADER + "\n")
        f.write(f'#EXTINF:-1 🕘️更新时间, {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        for line in output_entries:
            f.write(line + "\n")

    print(f"✅ 已生成 {OUTPUT_FILE}")

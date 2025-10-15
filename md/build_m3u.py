#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import time
from pathlib import Path
from collections import defaultdict

# ---------- 配置 ----------
INPUT_URLS = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

LOGO_DIR = Path("TVlogo_Images")
OUTPUT_FILE = Path("output.m3u")
ALIAS_FILE = Path("md/mohupidao.txt")

FIXED_HEADER = '#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"'

CATEGORY_ORDER = [
    "央视频道",
    "卫视频道",
    "地方频道",
    "CIBN系列",
    "DOX系列",
    "NewTV系列",
    "iHOT系列",
    "其他频道"
]

LOCAL_KEYWORDS = ["新闻", "生活", "影视", "文体", "少儿", "都市", "公共", "教育", "剧场"]

SERIES_CATEGORIES = ["CIBN", "DOX", "NewTV", "iHOT"]

# ---------- 读取别名表 ----------
def load_aliases(alias_file):
    alias_map = {}
    with open(alias_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",") if p.strip()]
            main_name = parts[0]
            for alias in parts[1:]:
                if alias.startswith("re:"):
                    pattern = alias[3:]
                    alias_map[pattern] = main_name
                else:
                    alias_map[alias] = main_name
    return alias_map

# ---------- M3U 下载 ----------
import requests
def download_m3u(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text.splitlines()
    except Exception as e:
        print(f"⚠️ 下载失败 {url}: {e}")
        return []

# ---------- 解析 M3U ----------
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

# ---------- 应用别名 ----------
def apply_alias(name, alias_map):
    # 先直接匹配
    if name in alias_map:
        return alias_map[name]
    # 再匹配正则
    for pattern, main_name in alias_map.items():
        if re.match(pattern, name):
            return main_name
    return name

# ---------- 构建 logo_map ----------
def build_logo_map():
    logo_map = {}
    for folder in LOGO_DIR.iterdir():
        if not folder.is_dir():
            continue
        for file in folder.iterdir():
            if file.suffix.lower() == ".png":
                logo_map[file.stem] = file
    return logo_map

# ---------- 判断分类 ----------
def classify_channel(name, regions):
    # CCTV/CETV/CGTN/中央新影等直接归央视频道
    if any(x in name for x in ["CCTV", "CETV", "CGTN", "中央新影"]):
        return "央视频道"
    # 卫视频道
    if "卫视" in name:
        return "卫视频道"
    # 地方频道：包含地名且不是卫视
    for region in regions:
        if region in name:
            return "地方频道"
    # 系列频道
    for s in SERIES_CATEGORIES:
        if s in name:
            return f"{s}系列"
    # 默认其他
    return "其他频道"

# ---------- 获取地方地名 ----------
def get_regions():
    regions = []
    for folder in LOGO_DIR.iterdir():
        if folder.is_dir() and folder.name not in ["中央电视台", "全国卫视"] + SERIES_CATEGORIES:
            regions.append(folder.name)
    return regions

# ---------- 生成 EXTINF 条目 ----------
def build_entry(name, url, category, logo_map, regions):
    logo_file = logo_map.get(name)
    if not logo_file:
        for region in regions:
            candidate = LOGO_DIR / region / f"{name}.png"
            if candidate.exists():
                logo_file = candidate
                break
    if logo_file:
        logo_url = f"https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/{logo_file.relative_to(LOGO_DIR)}".replace("\\", "/")
    else:
        logo_url = f"https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/其他/{name}.png"
    return f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_url}" group-title="{category}",{name}\n{url}'

# ---------- 主程序 ----------
def main():
    alias_map = load_aliases(ALIAS_FILE)
    logo_map = build_logo_map()
    regions = get_regions()

    all_channels = []
    for url in INPUT_URLS:
        lines = download_m3u(url)
        all_channels.extend(parse_m3u(lines))

    # 应用别名
    all_channels = [(apply_alias(name, alias_map), url) for name, url in all_channels]

    # 分类
    channel_dict = defaultdict(list)
    for name, url in all_channels:
        category = classify_channel(name, regions)
        channel_dict[name].append((name, url, category))

    # 按分类顺序整理输出
    output_entries = []
    for cat in CATEGORY_ORDER:
        for name, entries in channel_dict.items():
            if entries[0][2] == cat:
                for _, url, category in entries:
                    output_entries.append(build_entry(name, url, category, logo_map, regions))

    # 输出到文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(FIXED_HEADER + "\n")
        f.write(f'#EXTINF:-1,🕘 更新时间 {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        for line in output_entries:
            f.write(line + "\n")

    print(f"✅ 已生成 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

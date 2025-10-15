#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import re
import requests
from pathlib import Path
from collections import defaultdict

# ---------- 配置 ----------
INPUT_URLS = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

LOGO_DIR = Path("TVlogo_Images")
ALIAS_FILE = Path("md/mohupidao.txt")
OUTPUT_FILE = Path("output.m3u")

FIXED_HEADER = '#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"'

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

LOCAL_KEYWORDS = ["新闻", "生活", "影视", "文体", "少儿", "都市", "公共", "教育", "剧场"]

SERIES_CATEGORIES = ["CIBN", "DOX", "NewTV", "iHOT", "数字频道",
                     "台湾频道一", "台湾频道二", "台湾频道三"]

# ---------- 工具函数 ----------
def download_m3u(url):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return resp.text.splitlines()
    except Exception as e:
        print(f"⚠️ 下载失败 {url}: {e}")
        return []

def build_logo_map():
    logo_map = {}
    for folder in LOGO_DIR.iterdir():
        if not folder.is_dir():
            continue

        if folder.name == "中央电视台":
            category = "央视频道"
        elif "卫视" in folder.name or folder.name == "全国卫视":
            category = "卫视频道"
        elif folder.name in SERIES_CATEGORIES:
            category = folder.name
        else:
            category = "地方频道"

        for file in folder.iterdir():
            if file.suffix.lower() == ".png":
                logo_map[file.stem] = (category, file)
    return logo_map

def get_region_names():
    regions = []
    for folder in LOGO_DIR.iterdir():
        if folder.is_dir() and folder.name not in ["中央电视台", "全国卫视"] + SERIES_CATEGORIES + ["其他"]:
            regions.append(folder.name)
    return regions

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

def classify_channel(name, logo_map, regions):
    if name in logo_map:
        return logo_map[name][0]

    # CCTV/央视频道
    if "CCTV" in name or "CETV" in name or "CGTN" in name:
        return "央视频道"

    # 卫视频道
    if "卫视" in name:
        return "卫视频道"

    # 地方频道判断
    for region in regions:
        if region in name and "卫视" not in name:
            return "地方频道"
    for keyword in LOCAL_KEYWORDS:
        if keyword in name:
            return "地方频道"

    # 系列频道
    for s in SERIES_CATEGORIES:
        if s in name:
            return s

    return "其他频道"

def build_entry(name, url, category, logo_map, regions):
    logo_file = None
    if name in logo_map:
        logo_file = logo_map[name][1]
    else:
        for region in regions:
            if region in name:
                candidate = LOGO_DIR / region / f"{name}.png"
                if candidate.exists():
                    logo_file = candidate
                    break

    if logo_file:
        logo_url = f"https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/{logo_file.relative_to(LOGO_DIR)}".replace("\\", "/")
    else:
        logo_url = f"https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/其他/{name}.png"

    return f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_url}" group-title="{category}",{name}\n{url}'

# ---------- 别名处理 ----------
def load_aliases(alias_file):
    alias_map = {}
    regex_map = {}
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
                    try:
                        regex_map[re.compile(pattern)] = main_name
                    except re.error:
                        print(f"⚠️ 无效正则，已跳过: {pattern}")
                else:
                    alias_map[alias] = main_name
    return alias_map, regex_map

def apply_alias(name, alias_map, regex_map):
    if name in alias_map:
        return alias_map[name]
    for pattern, main_name in regex_map.items():
        if pattern.match(name):
            return main_name
    return name

# ---------- 主程序 ----------
def main():
    logo_map = build_logo_map()
    regions = get_region_names()
    alias_map, regex_map = load_aliases(ALIAS_FILE)

    all_channels = []
    for url in INPUT_URLS:
        lines = download_m3u(url)
        all_channels.extend(parse_m3u(lines))

    # 默认分类
    channel_dict = defaultdict(list)
    for name, url in all_channels:
        name = apply_alias(name, alias_map, regex_map)
        category = classify_channel(name, logo_map, regions)
        channel_dict[name].append((name, url, category))

    # 按分类顺序输出
    output_entries = []
    for cat in CATEGORY_ORDER:
        for name, entries in channel_dict.items():
            if entries[0][2] == cat:
                for _, url, category in entries:
                    output_entries.append(build_entry(name, url, category, logo_map, regions))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(FIXED_HEADER + "\n")
        f.write(f'#EXTINF:-1,🕘 更新时间 {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        for line in output_entries:
            f.write(line + "\n")

    print(f"✅ 已生成 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

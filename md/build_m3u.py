#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_m3u.py
从远程 M3U 列表抓取频道，基于仓库 TVlogo_Images 目录匹配台标与分类，
生成符合 tvbox / 普通播放器识别的 output.m3u
"""

import re
import time
from pathlib import Path
from collections import defaultdict, OrderedDict
import requests

# ---------- 配置 ----------
INPUT_URLS = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

LOGO_DIR = Path("TVlogo_Images")    # 仓库内台标根目录
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

LOCAL_KEYWORDS = ["新闻", "生活", "影视", "文体", "少儿", "都市", "公共", "教育", "剧场", "纪实", "电影", "电影频道", "综艺"]

SERIES_FOLDERS = ["CIBN", "DOX", "NewTV", "iHOT", "数字频道", "台湾频道一", "台湾频道二", "台湾频道三"]

# ---------- 工具函数 ----------
def fetch_m3u_lines(url, timeout=15):
    try:
        r = requests.get(url, timeout=timeout)
        r.encoding = "utf-8"
        r.raise_for_status()
        return r.text.splitlines()
    except Exception as e:
        print(f"⚠️ 下载失败 {url}: {e}")
        return []

def parse_m3u_lines(lines):
    channels = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("#EXTINF"):
            # 取最后一个逗号后面的显示名（保守）
            try:
                name = line.split(",", 1)[1].strip()
            except Exception:
                name = line
            # 如果有 tvg-name 属性优先使用
            m = re.search(r'tvg-name="([^"]+)"', line)
            if m:
                name = m.group(1).strip()
            # 取下一行 URL（通常）
            i += 1
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            url = lines[i].strip() if i < len(lines) else ""
            channels.append((name, url))
        i += 1
    return channels

def build_logo_index(logo_dir: Path):
    """
    扫描 TVlogo_Images/*/*.png
    返回：
      logo_map: {logo_stem: (folder_name, full_path)}
      folder_names: [folder_name, ...]  用于地域匹配
    """
    logo_map = {}
    folder_names = []
    if not logo_dir.exists():
        print(f"⚠️ 台标目录 {logo_dir} 不存在")
        return logo_map, folder_names

    for folder in sorted(logo_dir.iterdir()):
        if not folder.is_dir():
            continue
        folder_name = folder.name
        folder_names.append(folder_name)
        for file in folder.iterdir():
            if not file.is_file():
                continue
            if file.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
                continue
            stem = file.stem
            logo_map.setdefault(stem, (folder_name, file))
            # also store lowercase variant for fuzzy matching
            logo_map.setdefault(stem.lower(), (folder_name, file))
    return logo_map, folder_names

def is_numeric_name(name: str):
    # 纯数字（允许前后空格）
    return re.fullmatch(r"\d+", name.strip()) is not None

def extract_first_digits(name: str):
    m = re.search(r"(\d+)", name)
    return int(m.group(1)) if m else None

def jsdelivr_logo_url(logo_path: Path):
    # 相对 LOGO_DIR 的路径部分
    rel = logo_path.relative_to(LOGO_DIR).as_posix()
    return f"https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/{rel}"

# ---------- 分类与查找台标的主逻辑 ----------
def classify_channel(name: str, logo_map: dict, regions: list):
    nm = name.strip()
    low = nm.lower()

    # 1) 精确台标名匹配（优先）
    if nm in logo_map:
        return logo_map[nm][0]
    if low in logo_map:
        return logo_map[low][0]

    # 2) 系列文件夹内是否存在同名台标（优先系列判断）
    for s in SERIES_FOLDERS:
        folder = LOGO_DIR / s
        if folder.exists() and folder.is_dir():
            candidate = folder / f"{nm}.png"
            if candidate.exists():
                return s  # 返回系列文件夹名作为分类
            # 也试试小写/存在片段匹配
            candidate_lower = folder / f"{nm.lower()}.png"
            if candidate_lower.exists():
                return s

            # 遍历 folder 寻找包含 name 的文件
            for f in folder.iterdir():
                if f.is_file():
                    if nm == f.stem or nm.lower() == f.stem.lower():
                        return s

    # 3) CCTV / CETV / CGTN -> 央视频道
    if "cctv" in low or "cetv" in low or "cgtn" in low or "中央电视台" in nm:
        return "央视频道"

    # 4) 卫视关键字 -> 卫视频道
    if "卫视" in nm:
        return "卫视频道"

    # 5) 地区文件夹名匹配（如果频道名包含区域名且不是卫视 -> 地方频道）
    for region in regions:
        if region and region in nm and "卫视" not in nm:
            return "地方频道"

    # 6) 地方关键词匹配 -> 地方频道
    for kw in LOCAL_KEYWORDS:
        if kw in nm:
            return "地方频道"

    # 7) 纯数字 -> 其他频道
    if is_numeric_name(nm):
        return "其他频道"

    # 8) 最后默认 -> 其他频道
    return "其他频道"

def find_logo_for_channel(name: str, logo_map: dict, regions: list):
    nm = name.strip()
    low = nm.lower()

    # 1) 精确匹配（优先）
    if nm in logo_map:
        return logo_map[nm][1]
    if low in logo_map:
        return logo_map[low][1]

    # 2) 在系列文件夹中寻找同名图
    for s in SERIES_FOLDERS:
        folder = LOGO_DIR / s
        if folder.exists() and folder.is_dir():
            candidate = folder / f"{nm}.png"
            if candidate.exists():
                return candidate
            # try case-insensitive scan in folder
            for f in folder.iterdir():
                if f.is_file() and f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
                    if nm.lower() == f.stem.lower() or f.stem.lower() in nm.lower() or nm.lower() in f.stem.lower():
                        return f

    # 3) 如果名字包含地区名，优先在该地区文件夹中找
    for region in regions:
        if region and region in nm:
            region_folder = LOGO_DIR / region
            if region_folder.exists() and region_folder.is_dir():
                candidate = region_folder / f"{nm}.png"
                if candidate.exists():
                    return candidate
                # try fuzzy match inside region folder
                for f in region_folder.iterdir():
                    if f.is_file() and f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
                        if nm.lower() == f.stem.lower() or f.stem.lower() in nm.lower() or nm.lower() in f.stem.lower():
                            return f

    # 4) 全库模糊查找：名字片段匹配（最后手段）
    for stem, (folder_name, path) in logo_map.items():
        if stem and (stem == nm or stem.lower() in low or low in stem.lower()):
            return path

    # 5) 找不到则返回 None
    return None

# ---------- 主流程 ----------
def main():
    logo_map, regions = build_logo_index(LOGO_DIR)
    # regions contains all folder names; filter out series and special ones if desired
    # keep regions as-is so region matching works (including province/city folder names)
    # print("Regions:", regions)

    all_channels = []
    for url in INPUT_URLS:
        lines = fetch_m3u_lines(url)
        parsed = parse_m3u_lines(lines)
        all_channels.extend(parsed)

    # build channel dict: name -> list of urls
    channel_dict = defaultdict(list)
    for name, url in all_channels:
        if not name:
            continue
        # normalize display name whitespace
        name = name.strip()
        channel_dict[name].append(url)

    # group channels by classification
    categorized = OrderedDict((cat, {}) for cat in CATEGORY_ORDER)

    for name, urls in channel_dict.items():
        category = classify_channel(name, logo_map, regions)
        # place under category
        categorized.setdefault(category, {})[name] = urls

    # prepare final ordered entries:
    entries = []

    # 1) timestamp header entry (per your required format)
    timestamp_line = f'#EXTINF:-1 🕘️更新时间, {time.strftime("%Y-%m-%d %H:%M:%S")}'
    # we'll write FIXED_HEADER + timestamp then entries

    # 2) For 央视频道, sort numerically by first found digits if possible
    def cctv_sort_key(name):
        d = extract_first_digits(name or "")
        return (d if d is not None else 9999, name.lower())

    for cat in CATEGORY_ORDER:
        group = categorized.get(cat, {})
        if not group:
            continue
        # special sorting for 央视频道
        names = list(group.keys())
        if cat == "央视频道":
            names.sort(key=cctv_sort_key)
        else:
            # For other categories: keep discovered order (insertion) but place numeric-only at end
            numeric_names = [n for n in names if is_numeric_name(n)]
            non_numeric = [n for n in names if not is_numeric_name(n)]
            names = sorted(non_numeric, key=lambda s: s.lower()) + sorted(numeric_names, key=lambda s: int(s))
        for name in names:
            urls = group[name]
            # build entries for each url (keep order found)
            # find logo once
            logo_path = find_logo_for_channel(name, logo_map, regions)
            if logo_path:
                logo_url = jsdelivr_logo_url(logo_path)
            else:
                logo_url = f"https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/其他/{name}.png"
            for url in urls:
                ext = f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_url}" group-title="{cat}",{name}'
                entries.append((cat, ext, url))

    # Write output file
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(FIXED_HEADER + "\n")
        f.write(timestamp_line + "\n")
        for _, ext, url in entries:
            f.write(ext + "\n")
            f.write(url + "\n")

    print(f"✅ 已生成 {OUTPUT_FILE}  （{len(entries)} 条）")

if __name__ == "__main__":
    main()

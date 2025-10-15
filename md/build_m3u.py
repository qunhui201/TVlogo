#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from datetime import datetime
from pathlib import Path
import re

# IPTV 源
iptv_sources = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

# 台标根路径（CDN 可访问）
logo_base = "https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img"

# 分类对应文件夹
FOLDER_RULES = {
    "央视频道": "中央电视台",
    "央视付费频道": "CGTN、中国教育电视台、新华社、中央新影",
    "卫视频道": "全国卫视",
    "广东频道": "广东",
    "默认": "其他"
}

# 合并频道字典
channels = {}

# 数字频道单独存储
numeric_channels = []

def get_folder_and_logo(name):
    """根据台标文件夹判断分类和logo路径"""
    for group, folder in FOLDER_RULES.items():
        folders = [f.strip() for f in folder.split("、")]
        for f in folders:
            # 如果频道名包含文件夹名（或完全匹配），归类
            if f in name:
                # logo 文件名替换空格
                logo_name = name.replace(" ", "%20") + ".png"
                logo_url = f"{logo_base}/{f}/{logo_name}"
                return group, logo_url
    # 默认归类
    logo_name = name.replace(" ", "%20") + ".png"
    logo_url = f"{logo_base}/{FOLDER_RULES['默认']}/{logo_name}"
    return FOLDER_RULES['默认'], logo_url

def parse_m3u(url):
    """下载并解析 IPTV m3u"""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except:
        print(f"无法获取 {url}")
        return

    lines = r.text.splitlines()
    name = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#EXTM3U"):
            continue
        if line.startswith("#EXTINF"):
            # 提取频道名称
            m = re.search(r",(.+)$", line)
            if m:
                name = m.group(1).strip()
            else:
                name = None
        elif line.startswith("http"):
            if not name:
                # 没有标题直接用 URL 最后部分
                name = line.split("/")[-2] if line.split("/")[-2] else line.split("/")[-1]
            # 判断是否纯数字频道
            if name.isdigit():
                numeric_channels.append((name, line))
            else:
                group, logo = get_folder_and_logo(name)
                if name not in channels:
                    channels[name] = {"group": group, "logo": logo, "urls": []}
                channels[name]["urls"].append(line)
            name = None

# 下载并解析所有源
for url in iptv_sources:
    parse_m3u(url)

# 输出文件
output_file = Path("output.m3u")
with output_file.open("w", encoding="utf-8") as f:
    # 写固定开头和更新时间
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write('#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"\n')
    f.write(f"#EXTINF:-1 🕘️更新时间, {now}\n")
    f.write("https://rthktv33-live.akamaized.net/hls/live/2101641/RTHKTV33/stream05/streamPlaylist.m3u8\n")

    # 先输出央视频道，按数字顺序
    for name in sorted([n for n in channels if channels[n]["group"] == "央视频道"], key=lambda x: [int(s) if s.isdigit() else s for s in re.findall(r'\d+|\D+', x)]):
        data = channels[name]
        for url in data["urls"]:
            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{data["logo"]}" group-title="央视频道",{name}\n')
            f.write(f"{url}\n")

    # 输出卫视频道
    for name in channels:
        if channels[name]["group"] == "卫视频道":
            data = channels[name]
            for url in data["urls"]:
                f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{data["logo"]}" group-title="卫视频道",{name}\n')
                f.write(f"{url}\n")

    # 输出其他地方频道
    for name in channels:
        if channels[name]["group"] not in ["央视频道", "卫视频道"]:
            data = channels[name]
            for url in data["urls"]:
                f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{data["logo"]}" group-title="{data["group"]}",{name}\n')
                f.write(f"{url}\n")

    # 输出纯数字频道放末尾
    for name, url in numeric_channels:
        logo = f"{logo_base}/{FOLDER_RULES['默认']}/{name}.png"
        f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="其他频道",{name}\n')
        f.write(f"{url}\n")

print("✅ 已生成 output.m3u")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from datetime import datetime
from pathlib import Path
import re

iptv_sources = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

logo_base = "https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img"

# 合并频道字典
channels = {}
numeric_channels = []

# 识别频道分组
def classify_channel(name):
    name_lower = name.lower()
    # 央视频道
    if "cctv" in name_lower or "cetv" in name_lower or "cgtn" in name_lower or "中央电视台" in name:
        group = "央视频道"
        folder = "中央电视台"
    # 卫视频道
    elif "卫视" in name:
        group = "卫视频道"
        # 取地名或全国卫视作为台标文件夹
        m = re.match(r"(全国|北京|上海|广东|广州|深圳|湖南|湖北|重庆|四川|浙江|江苏|福建|山东|海南|青海)?", name)
        folder = m.group(0) if m and m.group(0) else "全国卫视"
    # 地方频道
    elif re.search(r"(北京|上海|广东|广州|深圳|湖南|湖北|重庆|四川|浙江|江苏|福建|山东|海南|青海)", name):
        group = "地方频道"
        folder = re.search(r"(北京|上海|广东|广州|深圳|湖南|湖北|重庆|四川|浙江|江苏|福建|山东|海南|青海)", name).group(0)
    else:
        group = "其他频道"
        folder = "其他"
    logo_name = name.replace(" ", "%20") + ".png"
    logo_url = f"{logo_base}/{folder}/{logo_name}"
    return group, logo_url

def parse_m3u(url):
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
            m = re.search(r",(.+)$", line)
            name = m.group(1).strip() if m else None
        elif line.startswith("http"):
            if not name:
                name = line.split("/")[-2] if line.split("/")[-2] else line.split("/")[-1]
            if name.isdigit():
                numeric_channels.append((name, line))
            else:
                group, logo = classify_channel(name)
                if name not in channels:
                    channels[name] = {"group": group, "logo": logo, "urls": []}
                channels[name]["urls"].append(line)
            name = None

# 解析所有源
for url in iptv_sources:
    parse_m3u(url)

# 输出
output_file = Path("output.m3u")
with output_file.open("w", encoding="utf-8") as f:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write('#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"\n')
    f.write(f"#EXTINF:-1 🕘️更新时间, {now}\n")
    f.write("https://rthktv33-live.akamaized.net/hls/live/2101641/RTHKTV33/stream05/streamPlaylist.m3u8\n")

    # 央视频道排序
    for name in sorted([n for n in channels if channels[n]["group"]=="央视频道"],
                       key=lambda x: [int(s) if s.isdigit() else s for s in re.findall(r'\d+|\D+', x)]):
        data = channels[name]
        for url in data["urls"]:
            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{data["logo"]}" group-title="央视频道",{name}\n')
            f.write(f"{url}\n")

    # 卫视频道
    for name in channels:
        if channels[name]["group"]=="卫视频道":
            data = channels[name]
            for url in data["urls"]:
                f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{data["logo"]}" group-title="卫视频道",{name}\n')
                f.write(f"{url}\n")

    # 地方频道
    for name in channels:
        if channels[name]["group"]=="地方频道":
            data = channels[name]
            for url in data["urls"]:
                f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{data["logo"]}" group-title="地方频道",{name}\n')
                f.write(f"{url}\n")

    # 其他频道
    for name in channels:
        if channels[name]["group"]=="其他频道":
            data = channels[name]
            for url in data["urls"]:
                f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{data["logo"]}" group-title="其他频道",{name}\n')
                f.write(f"{url}\n")

    # 纯数字频道
    for name, url in numeric_channels:
        logo = f"{logo_base}/其他/{name}.png"
        f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="其他频道",{name}\n')
        f.write(f"{url}\n")

print("✅ 已生成 output.m3u")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from urllib.parse import quote
from datetime import datetime

# IPTV源
iptv_sources = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

# 台标文件夹映射为 group-title
FOLDER_TO_GROUP = {
    "中央电视台": "央视频道",
    "全国卫视": "卫视频道"
}

# logo 基础 URL
LOGO_BASE = "https://raw.githubusercontent.com/qunhui201/TVlogo/main/TVlogo_Images"

# 存储频道
channels_by_group = {}
other_channels = {}

# 下载并解析 IPTV 文件
for source_url in iptv_sources:
    r = requests.get(source_url, timeout=15)
    r.encoding = 'utf-8'
    lines = r.text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # 频道名取 URL 文件名
        name = line.split('/')[-1].split('.')[0]
        # 纯数字放到其他频道
        if name.isdigit():
            other_channels[name] = line
            continue

        # 生成 logo 文件夹和路径
        folder = "其他"  # 默认
        if "CCTV" in name or "CETV" in name or "CGTN" in name:
            folder = "中央电视台"
        elif "卫视" in name:
            folder = "全国卫视"
        else:
            folder = "其他"  # 其他地方频道默认归为其他

        group_name = FOLDER_TO_GROUP.get(folder, folder)

        # 合并重复频道
        channels_by_group.setdefault(group_name, {}).setdefault(name, []).append(line)

# 写入 output.m3u
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open("output.m3u", "w", encoding="utf-8") as f:
    f.write('#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"\n')
    f.write(f'#EXTINF:-1 🕘️更新时间, {now}\n')
    f.write('https://rthktv33-live.akamaized.net/hls/live/2101641/RTHKTV33/stream05/streamPlaylist.m3u8\n')

    for group, items in channels_by_group.items():
        # 央视频道按数字顺序
        if group == "央视频道":
            sorted_items = sorted(items.items(), key=lambda x: int(''.join(filter(str.isdigit, x[0]))))
        else:
            sorted_items = items.items()
        for name, urls in sorted_items:
            logo_path = f"{LOGO_BASE}/{quote(folder)}/{quote(name)}.png"
            for url in urls:
                f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="{group}",{name}\n')
                f.write(f'{url}\n')

    # 写入其他频道（纯数字或无法识别）
    for name, url in other_channels.items():
        logo_path = f"{LOGO_BASE}/其他/{quote(name)}.png"
        f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="其他频道",{name}\n')
        f.write(f'{url}\n')

print("✅ 已生成 output.m3u")

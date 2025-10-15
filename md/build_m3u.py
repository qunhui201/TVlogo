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

# 频道分类规则
GROUP_RULES = {
    "央视频道": ["CCTV", "CETV", "CGTN"],
    "央视付费频道": ["风云", "怀旧", "第一剧场", "兵器", "世界地理", "女性时尚", "高尔夫", "电视指南"],
    "卫视频道": ["卫视"],
    "广东频道": ["广东", "广州", "深圳", "珠江"],
}

# 台标文件夹规则
FOLDER_RULES = {
    "央视频道": "中央电视台",
    "央视付费频道": "CGTN、中国教育电视台、新华社、中央新影",
    "卫视频道": "全国卫视",
    "广东频道": "广东",
    "默认": "其他",
}

# base URL for logos
LOGO_BASE = "https://raw.githubusercontent.com/qunhui201/TVlogo/main/TVlogo_Images"

# 用于存储分类后的频道
channels_by_group = {}
other_channels = {}

# 下载并解析所有 m3u 链接
for source_url in iptv_sources:
    r = requests.get(source_url, timeout=15)
    r.encoding = 'utf-8'
    lines = r.text.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # 提取频道名
        name = line.split('/')[-1].split('.')[0]  # 默认用 URL 文件名做名字
        # 纯数字放到其他频道
        if name.isdigit():
            other_channels[name] = line
            continue
        # 判定分组
        group_name = "其他频道"
        for grp, keywords in GROUP_RULES.items():
            if any(k in name for k in keywords):
                group_name = grp
                break
        # 合并重复频道
        if group_name == "其他频道":
            other_channels[name] = line
        else:
            channels_by_group.setdefault(group_name, {}).setdefault(name, []).append(line)

# 生成 output.m3u
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open("output.m3u", "w", encoding="utf-8") as f:
    # 文件头固定格式 + 更新时间
    f.write('#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"\n')
    f.write(f'#EXTINF:-1 🕘️更新时间, {now}\n')
    f.write('https://rthktv33-live.akamaized.net/hls/live/2101641/RTHKTV33/stream05/streamPlaylist.m3u8\n')

    # 输出各组频道
    for group, items in channels_by_group.items():
        # 央视频道按数字顺序
        if group == "央视频道":
            sorted_items = sorted(items.items(), key=lambda x: int(''.join(filter(str.isdigit, x[0]))))
        else:
            sorted_items = items.items()
        for name, urls in sorted_items:
            # 根据 FOLDER_RULES 生成台标
            folder = FOLDER_RULES.get(group, FOLDER_RULES["默认"])
            for url in urls:
                logo_path = f"{LOGO_BASE}/{quote(folder)}/{quote(name)}.png"
                f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="{group}",{name}\n')
                f.write(f'{url}\n')

    # 输出其他频道（纯数字或者无法识别）
    for name, url in other_channels.items():
        logo_path = f"{LOGO_BASE}/其他/{quote(name)}.png"
        f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="其他频道",{name}\n')
        f.write(f'{url}\n')

print("✅ 已生成 output.m3u")

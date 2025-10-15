#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import re
from collections import defaultdict
from datetime import datetime

# IPTV 源
iptv_sources = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

# 分组规则
GROUP_RULES = {
    "央视频道": ["CCTV", "CETV", "CGTN"],
    "央视付费频道": ["风云", "怀旧", "第一剧场", "兵器", "世界地理", "女性时尚", "高尔夫", "电视指南"],
    "卫视频道": ["卫视"],
    "广东频道": ["广东", "广州", "深圳", "珠江"],
}

# 台标文件夹
FOLDER_RULES = {
    "央视频道": "中央电视台",
    "央视付费频道": "CGTN、中国教育电视台、新华社、中央新影",
    "卫视频道": "全国卫视",
    "广东频道": "广东",
    "默认": "其他",
}

# 输出文件
output_file = "output.m3u"

# 读取 channels.txt 生成频道列表
channel_categories = defaultdict(list)
with open("channels.txt", "r", encoding="utf-8") as f:
    current_group = "其他频道"
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            current_group = line[1:].strip()
        else:
            channel_categories[current_group].append(line)

# 用于存储最终频道数据
channels = defaultdict(list)
numeric_channels = []

# 获取 IPTV 源内容
for url in iptv_sources:
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        for line in r.text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            link = line

            # 尝试提取简单名称
            match = re.search(r'/((CCTV|CETV|CGTN)?[\d\+\w\-]+)', link, re.I)
            if match:
                name = match.group(1)
            else:
                # 无法提取名称，生成频道名数字序号
                name = f"频道{len(numeric_channels)+1}"

            # 判断是否纯数字或临时频道名
            if re.fullmatch(r"\d+", name) or name.startswith("频道"):
                numeric_channels.append((name, link))
                continue

            # 分组匹配
            group = "其他频道"
            for g, keywords in GROUP_RULES.items():
                if any(k in name for k in keywords):
                    group = g
                    break

            channels[(group, name)].append(link)
    except Exception as e:
        print(f"⚠️ 获取 {url} 出错: {e}")

# 写入 M3U 文件
with open(output_file, "w", encoding="utf-8") as f:
    # 文件头
    f.write('#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"\n')
    # 更新时间
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write(f'#EXTINF:-1 🕘️更新时间, {now}\n')
    f.write('https://rthktv33-live.akamaized.net/hls/live/2101641/RTHKTV33/stream05/streamPlaylist.m3u8\n\n')

    # 写入分类频道（央视频道优先按 1~17 排序）
    def sort_cctv(name):
        match = re.search(r'\d+', name)
        return int(match.group()) if match else 999

    sorted_keys = sorted(channels.keys(), key=lambda x: sort_cctv(x[1]) if x[0]=="央视频道" else x[1])

    for (group, name) in sorted_keys:
        folder = FOLDER_RULES.get(group, FOLDER_RULES["默认"])
        logo_base = "https://raw.githubusercontent.com/qunhui201/TVlogo/main/TVlogo_Images"
        logo_path = f"{logo_base}/{folder}/{name}.png"
        for link in channels[(group, name)]:
            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="{group}",{name}\n')
            f.write(f'{link}\n')

    # 写入纯数字频道，放到最后
    for name, link in numeric_channels:
        logo_path = f"{logo_base}/其他/{name}.png"
        f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="其他频道",{name}\n')
        f.write(f'{link}\n')

print(f"✅ 已生成 {output_file}")

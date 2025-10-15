#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from datetime import datetime
import re

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

# 台标文件夹规则
FOLDER_RULES = {
    "央视频道": "中央电视台",
    "央视付费频道": "CGTN、中国教育电视台、新华社、中央新影",
    "卫视频道": "全国卫视",
    "广东频道": "广东",
    "默认": "其他",
}

# 输出文件
output_file = "output.m3u"

# 存储频道
channels = {}           # key=(group, name), value=list of links
numeric_channels = []   # 纯数字频道放最后

# 全局台标路径
logo_base = "https://raw.githubusercontent.com/qunhui201/TVlogo/main/TVlogo_Images"

# 获取 IPTV 内容
for url in iptv_sources:
    print(f"Fetching {url} ...")
    resp = requests.get(url, timeout=10)
    content = resp.text.splitlines()
    for line in content:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # 判断纯数字
        if re.fullmatch(r"\d+", line.split(",")[0]):
            numeric_channels.append((line, line))
            continue
        # 分组匹配
        group_found = "其他频道"
        for group, keywords in GROUP_RULES.items():
            if any(kw in line for kw in keywords):
                group_found = group
                break
        # 提取频道名称
        name = line.split(",")[0]
        key = (group_found, name)
        channels.setdefault(key, []).append(line)

# 排序央视频道
def sort_cctv(name):
    match = re.search(r'\d+', name)
    return int(match.group()) if match else 999

sorted_keys = sorted(
    channels.keys(),
    key=lambda x: sort_cctv(x[1]) if x[0]=="央视频道" else x[1]
)

# 写入 M3U 文件
with open(output_file, "w", encoding="utf-8") as f:
    # 文件头
    f.write('#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"\n')
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write(f'#EXTINF:-1 🕘️更新时间, {now}\n')
    f.write('https://rthktv33-live.akamaized.net/hls/live/2101641/RTHKTV33/stream05/streamPlaylist.m3u8\n\n')

    # 写入分类频道
    for (group, name) in sorted_keys:
        folder = FOLDER_RULES.get(group, FOLDER_RULES["默认"])
        logo_path = f"{logo_base}/{folder}/{name}.png"
        for link in channels[(group, name)]:
            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="{group}",{name}\n')
            f.write(f'{link}\n')

    # 写入纯数字频道
    for name, link in numeric_channels:
        logo_path = f"{logo_base}/其他/{name}.png"
        f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="其他频道",{name}\n')
        f.write(f'{link}\n')

print(f"✅ 已生成 {output_file}")

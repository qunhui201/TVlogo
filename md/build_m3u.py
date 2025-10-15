import requests
import datetime
import re
from collections import defaultdict

# IPTV 源
iptv_sources = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

# 分类文件
channels_file = "channels.txt"

# 台标 URL 根
logo_base = "https://raw.githubusercontent.com/qunhui201/TVlogo/main/TVlogo_Images/"

# 输出文件
output_file = "output.m3u"

# 读取分类
categories = defaultdict(list)
current_category = "其他频道"
with open(channels_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            current_category = line[1:].strip()
        else:
            categories[line] = current_category

# 下载并解析 IPTV 列表
channels = defaultdict(list)
numeric_channels = []  # 纯数字频道归类到其他频道末尾

for url in iptv_sources:
    r = requests.get(url, timeout=10)
    r.encoding = r.apparent_encoding
    for line in r.text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # 提取名称和链接
        parts = line.split(None, 1)
        if len(parts) == 2:
            name, link = parts
        else:
            name = parts[0]
            link = parts[0]
        # 判断频道分类
        category = categories.get(name, "其他频道")
        # 数字标题归到 numeric_channels
        if re.fullmatch(r"\d+", name):
            numeric_channels.append((name, link))
        else:
            channels[(category, name)].append(link)

# 央视频道自然数字排序
def cctv_key(name):
    match = re.search(r"\d+", name)
    return int(match.group()) if match else float('inf')

# 输出
with open(output_file, "w", encoding="utf-8") as f:
    # 文件开头固定格式
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f.write('#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"\n')
    f.write(f'#EXTINF:-1 🕘️更新时间, {now}\n')
    f.write('https://rthktv33-live.akamaized.net/hls/live/2101641/RTHKTV33/stream05/streamPlaylist.m3u8\n')

    # 按分类输出
    # 先输出央视频道，按自然数字顺序
    for key in sorted(channels.keys(), key=lambda x: cctv_key(x[1]) if x[0] == "央视频道" else 1000):
        category, name = key
        for link in channels[key]:
            # 构建台标路径
            logo_path = f"{logo_base}{category}/{name}.png"
            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="{category}",{name}\n')
            f.write(f'{link}\n')

    # 其他频道
    for key in channels.keys():
        category, name = key
        if category != "央视频道":
            for link in channels[key]:
                logo_path = f"{logo_base}{category}/{name}.png"
                f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="{category}",{name}\n')
                f.write(f'{link}\n')

    # 数字标题放文件末尾
    for name, link in numeric_channels:
        category = "其他频道"
        logo_path = f"{logo_base}{category}/{name}.png"
        f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="{category}",{name}\n')
        f.write(f'{link}\n')

print(f"✅ 已生成 {output_file}")

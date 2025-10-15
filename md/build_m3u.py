import requests
import datetime
import re
from collections import defaultdict

# IPTV 源
iptv_sources = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

# 分组规则关键字
GROUP_RULES = {
    "央视频道": ["CCTV", "CETV", "CGTN"],
    "央视付费频道": ["风云", "怀旧", "第一剧场", "兵器", "世界地理", "女性时尚", "高尔夫", "电视指南"],
    "卫视频道": ["卫视"],
    "广东频道": ["广东", "广州", "深圳", "珠江"],
}

# 台标文件夹映射
FOLDER_RULES = {
    "央视频道": "中央电视台",
    "央视付费频道": "CGTN、中国教育电视台、新华社、中央新影",
    "卫视频道": "全国卫视",
    "广东频道": "广东",
    "默认": "其他",
}

# 台标 URL 根
logo_base = "https://raw.githubusercontent.com/qunhui201/TVlogo/main/TVlogo_Images/"

# 输出文件
output_file = "output.m3u"

# 存储频道
channels = defaultdict(list)
numeric_channels = []  # 纯数字频道归类到其他频道末尾

# 下载 IPTV 源
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

        # 数字标题归到 numeric_channels
        if re.fullmatch(r"\d+", name):
            numeric_channels.append((name, link))
            continue

        # 分组匹配
        group = "其他频道"
        for g, keywords in GROUP_RULES.items():
            if any(k in name for k in keywords):
                group = g
                break

        channels[(group, name)].append(link)

# 央视频道自然数字排序
def cctv_key(name):
    match = re.search(r"\d+", name)
    return int(match.group()) if match else float('inf')

# 输出
with open(output_file, "w", encoding="utf-8") as f:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 文件开头固定格式
    f.write('#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"\n')
    f.write(f'#EXTINF:-1 🕘️更新时间, {now}\n')
    f.write('https://rthktv33-live.akamaized.net/hls/live/2101641/RTHKTV33/stream05/streamPlaylist.m3u8\n')

    # 输出央视频道（自然排序）
    for key in sorted(channels.keys(), key=lambda x: cctv_key(x[1]) if x[0]=="央视频道" else 1000):
        group, name = key
        folder = FOLDER_RULES.get(group, FOLDER_RULES["默认"])
        for link in channels[key]:
            logo_path = f"{logo_base}{folder}/{name}.png"
            f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="{group}",{name}\n')
            f.write(f'{link}\n')

    # 输出其他分类
    for key in channels.keys():
        group, name = key
        if group != "央视频道":
            folder = FOLDER_RULES.get(group, FOLDER_RULES["默认"])
            for link in channels[key]:
                logo_path = f"{logo_base}{folder}/{name}.png"
                f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_path}" group-title="{group}",{name}\n')
                f.write(f'{link}\n')

    # 数字标题归类到“其他频道”末尾
    for name, link in numeric_channels:
        folder = FOLDER_RULES["默认"]
        f.write(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_base}{folder}/{name}.png" group-title="其他频道",{name}\n')
        f.write(f'{link}\n')

print(f"✅ 已生成 {output_file}")

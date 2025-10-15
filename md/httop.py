import re
import requests
from collections import defaultdict
from datetime import datetime

# IPTV 源列表
iptv_sources = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

# 输出文件名
output_file = "output.m3u"

# 台标主路径
logo_base = "https://raw.githubusercontent.com/qunhui201/TVlogo/main/TVlogo_Images"

# 匹配央视频道的正则
cctv_pattern = re.compile(r'^(CCTV|CETV)[\-\d]+')

# 存储所有频道
channels = defaultdict(list)

def fetch_m3u(url):
    """从远程URL获取m3u内容"""
    try:
        print(f"📡 正在下载 {url} ...")
        resp = requests.get(url, timeout=15)
        resp.encoding = 'utf-8'
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"⚠️ 下载失败: {url} ({resp.status_code})")
            return ""
    except Exception as e:
        print(f"❌ 获取失败: {url} -> {e}")
        return ""

# 从多个源合并
merged_content = ""
for src in iptv_sources:
    merged_content += fetch_m3u(src) + "\n"

# 按行解析
lines = merged_content.splitlines()
current_name = None

for line in lines:
    if line.startswith("#EXTINF"):
        match = re.search(r',(.+)$', line)
        if match:
            current_name = match.group(1).strip()
    elif line.startswith("http") and current_name:
        channels[current_name].append(line.strip())
        current_name = None

print(f"✅ 共解析到 {len(channels)} 个频道。")

# 生成输出内容
output_lines = [
    '#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"\n'
]

for name, urls in sorted(channels.items()):
    # 判断频道分类与台标路径
    if cctv_pattern.match(name):
        group = "央视频道"
        logo_folder = "中央电视台"
    else:
        group = "其他频道"
        logo_folder = "其他"

    # 台标URL（例如：https://.../中央电视台/CCTV-1 综合.png）
    logo_url = f"{logo_base}/{logo_folder}/{name}.png"

    # 为同频道输出多条链接
    for url in urls:
        output_lines.append(
            f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_url}" group-title="{group}",{name}\n{url}\n'
        )

# 添加更新时间
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
output_lines.append(f'#EXTINF:-1 🕘️更新时间, {now}\n')
output_lines.append("https://rthktv33-live.akamaized.net/hls/live/2101641/RTHKTV33/stream05/streamPlaylist.m3u8\n")

# 写入文件
with open(output_file, "w", encoding="utf-8") as f:
    f.writelines(output_lines)

print(f"🎉 已生成 {output_file}，总计 {len(channels)} 个频道。")

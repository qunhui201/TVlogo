import requests
from collections import defaultdict
from pathlib import Path
import re

# ------------- 配置 -------------
# 输入频道模板
channels_file = Path("channels.txt")

# 输出文件
output_file = Path("output.m3u")

# GitHub 台标路径
logo_base = "https://raw.githubusercontent.com/qunhui201/TVlogo/main/TVlogo_Images"

# M3U源
sources = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u",
]

# ----------- 解析频道模板 -----------
channels_group = {}
current_group = "其他频道"

for line in channels_file.read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line:
        continue
    if line.startswith("#"):
        current_group = line.lstrip("#").strip()
        continue
    channels_group[line] = current_group

# ----------- 抓取 M3U 数据 -----------
channels_data = defaultdict(list)

for src in sources:
    try:
        print(f"Fetching {src} ...")
        r = requests.get(src, timeout=10)
        r.encoding = r.apparent_encoding
        lines = r.text.splitlines()
        name = None
        for line in lines:
            line = line.strip()
            if line.startswith("#EXTINF"):
                m = re.search(r",(.+)$", line)
                if m:
                    name = m.group(1).strip()
            elif line.startswith("http") and name:
                channels_data[name].append(line)
                name = None
    except Exception as e:
        print(f"⚠️ Error loading {src}: {e}")

# ----------- 生成 output.m3u -----------
with output_file.open("w", encoding="utf-8") as f:
    f.write('#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"\n')
    for ch, urls in channels_data.items():
        # 查找所属分组
        group = channels_group.get(ch, "其他频道")
        # 构造台标路径（搜索所有文件夹，优先按频道名）
        logo_url = f"{logo_base}/{group.replace('频道', '')}/{ch}.png"
        tvg_name = ch.replace(" ", "").replace("-", "")
        for url in urls:
            f.write(f'#EXTINF:-1 tvg-name="{tvg_name}" tvg-logo="{logo_url}" group-title="{group}",{ch}\n')
            f.write(f"{url}\n")

print(f"✅ 已生成 {output_file}")

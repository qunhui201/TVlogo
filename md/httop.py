import requests
import re
from pathlib import Path

# ---- 配置 ----
iptv_sources = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]
channels_txt = Path("channels.txt")
output_file = Path("output.m3u")

# GitHub 图标路径前缀
LOGO_BASE = "https://raw.githubusercontent.com/qunhui201/TVlogo/main/TVlogo_Images"

# EPG 地址
EPG_URL = "https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"

# ---- 读取频道分类 ----
channel_groups = {}
current_group = None
with channels_txt.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            current_group = line.strip("#").strip()
        else:
            channel_groups[line] = current_group or "其他频道"

# ---- 抓取 IPTV 内容 ----
m3u_lines = []
for url in iptv_sources:
    try:
        print(f"Fetching {url} ...")
        res = requests.get(url, timeout=10)
        res.encoding = "utf-8"
        m3u_lines.extend(res.text.splitlines())
    except Exception as e:
        print(f"⚠️ Failed to fetch {url}: {e}")

# ---- 解析频道 ----
pattern = re.compile(r"^(?!#EXTM3U|#EXTINF)(https?://[^\s]+)$")
channels = []  # [(name, url)]

current_name = None
for line in m3u_lines:
    line = line.strip()
    if line.startswith("#EXTINF"):
        # 提取频道名
        name_match = re.search(r",([^,]+)$", line)
        if name_match:
            current_name = name_match.group(1).strip()
    elif pattern.match(line):
        if current_name:
            channels.append((current_name, line))
            current_name = None

# ---- 生成 output.m3u ----
lines = [f'#EXTM3U x-tvg-url="{EPG_URL}"\n']

for name, url in channels:
    # 匹配分类
    group = channel_groups.get(name.split()[0], "其他频道")

    # 猜测 logo 路径（优先匹配对应文件夹）
    # 央视频道示例路径：https://.../中央电视台/CCTV-1 综合.png
    logo_folder = {
        "央视频道": "中央电视台",
        "央视付费频道": "中央新影",
        "卫视频道": "全国卫视",
        "广东频道": "广东",
    }.get(group, "其他")

    logo_name = f"{name}.png"
    tvg_logo = f"{LOGO_BASE}/{logo_folder}/{logo_name}"
    tvg_name = re.sub(r"\s+", "", name)  # 去掉空格防止TVBox识别错误

    lines.append(
        f'#EXTINF:-1 tvg-name="{tvg_name}" tvg-logo="{tvg_logo}" group-title="{group}",{name}'
    )
    lines.append(url)

# ---- 写入文件 ----
output_file.write_text("\n".join(lines), encoding="utf-8")
print(f"✅ 已生成 {output_file}")

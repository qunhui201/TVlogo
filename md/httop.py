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

# 分类规则
GROUP_RULES = {
    "央视频道": ["CCTV", "CETV", "CGTN"],
    "央视付费频道": ["风云", "怀旧", "第一剧场", "兵器", "世界地理", "女性时尚", "高尔夫", "电视指南"],
    "卫视频道": ["卫视"],
    "广东频道": ["广东", "广州", "深圳", "珠江"],
}

# 匹配台标文件夹（顺序重要）
FOLDER_RULES = {
    "央视频道": "中央电视台",
    "央视付费频道": "CGTN、中国教育电视台、新华社、中央新影",
    "卫视频道": "全国卫视",
    "广东频道": "广东",
    "默认": "其他",
}

# -------------------------------
# 工具函数
# -------------------------------

def fetch_m3u(url):
    """从远程URL获取m3u内容"""
    try:
        print(f"📡 正在下载 {url} ...")
        resp = requests.get(url, timeout=15)
        resp.encoding = 'utf-8'
        if resp.status_code == 200:
            return resp.text
        print(f"⚠️ 下载失败: {url} ({resp.status_code})")
    except Exception as e:
        print(f"❌ 获取失败: {url} -> {e}")
    return ""

def detect_group(name: str):
    """根据频道名识别分类"""
    for group, keywords in GROUP_RULES.items():
        for kw in keywords:
            if kw in name:
                return group
    return "其他频道"

def detect_folder(group: str):
    """根据分类名确定台标所在文件夹"""
    return FOLDER_RULES.get(group, FOLDER_RULES["默认"])

# -------------------------------
# 主流程
# -------------------------------

# 下载并合并所有源
merged_content = ""
for src in iptv_sources:
    merged_content += fetch_m3u(src) + "\n"

lines = merged_content.splitlines()
channels = defaultdict(list)
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

# -------------------------------
# 生成输出
# -------------------------------

output_lines = []
output_lines.append('#EXTM3U x-tvg-url="https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"\n')

# 添加更新时间（紧跟在头部）
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
output_lines.append(f'#EXTINF:-1 🕘️更新时间, {now}\n')
output_lines.append("https://rthktv33-live.akamaized.net/hls/live/2101641/RTHKTV33/stream05/streamPlaylist.m3u8\n\n")

for name, urls in sorted(channels.items()):
    group = detect_group(name)
    folder = detect_folder(group)
    logo_url = f"{logo_base}/{folder}/{name}.png"

    for url in urls:
        output_lines.append(
            f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_url}" group-title="{group}",{name}\n{url}\n'
        )

# -------------------------------
# 写入文件
# -------------------------------
with open(output_file, "w", encoding="utf-8") as f:
    f.writelines(output_lines)

print(f"🎉 已生成 {output_file}，总计 {len(channels)} 个频道。")

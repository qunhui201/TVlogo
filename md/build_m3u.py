import re
import requests
from pathlib import Path

# -------- 配置 ---------
REMOTE_FILES = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

TVLOGO_DIR = Path("TVlogo_Images")  # 台标根目录

PROVINCES = [
    "北京","上海","天津","重庆","辽宁","吉林","黑龙江","江苏","浙江","安徽","福建","江西",
    "山东","河南","湖北","湖南","广东","广西","海南","四川","贵州","云南","陕西","甘肃",
    "青海","宁夏","新疆","内蒙","西藏","香港","澳门","台湾","延边","大湾区"
]

SPECIAL_CHANNELS = {
    "CCTV17": "央视频道",  # 特例处理
    "4K": "4K频道"  # 明确指定4K频道
}

OUTPUT_FILE = "output.m3u"
TVBOX_OUTPUT_FILE = "tvbox_output.txt"

# -------- 函数 ---------
def download_m3u(url):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.text

def parse_m3u(content):
    """解析 m3u 文件内容"""
    lines = content.splitlines()
    result = []
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            info = lines[i]
            url = lines[i+1] if i+1 < len(lines) else ""
            tvg_name = re.search(r'tvg-name="([^"]+)"', info)
            group_title = re.search(r'group-title="([^"]+)"', info)
            tvg_logo = re.search(r'tvg-logo="([^"]+)"', info)
            name = tvg_name.group(1) if tvg_name else ""
            grp = group_title.group(1) if group_title else ""
            logo = tvg_logo.group(1) if tvg_logo else ""
            result.append((name, url, grp, logo))
    return result

def classify_channel(name, original_group, tvlogo_dir):
    """分类逻辑"""
    # 4K频道专门分类
    if "4K" in name:
        return "4K频道"

    # 特殊频道直接归类
    for key, val in SPECIAL_CHANNELS.items():
        if key in name:
            return val

    # 保留原分组
    if original_group in ["央视频道", "卫视频道", "地方频道"]:
        return original_group

    # 卫视频道：只要包含“卫视”
    if "卫视" in name:
        return "卫视频道"

    # 地方频道：包含地名且不是卫视
    for province in PROVINCES:
        if province in name and "卫视" not in name:
            return "地方频道"

    # 第三方系列匹配（忽略英文前缀）
    for folder in tvlogo_dir.iterdir():
        if not folder.is_dir():
            continue
        folder_name = folder.name
        if folder_name in ["央视频道", "卫视频道", "地方频道"]:
            continue
        for logo_file in folder.iterdir():
            if not logo_file.is_file():
                continue
            filename = logo_file.stem
            ch_name = re.sub(r'^[A-Za-z0-9\+\-]+', '', filename)  # 忽略英文前缀
            if ch_name and ch_name in name:
                return folder_name

    # 数字或未知
    if name.isdigit() or not name:
        return "其他频道"

    # 默认
    return "其他频道"

# -------- 主逻辑 ---------
def main():
    all_channels = []
    tvbox_channels = []  # 用于存储 TVBox 格式的频道

    # 下载远程 M3U 文件
    for url in REMOTE_FILES:
        content = download_m3u(url)
        channels = parse_m3u(content)
        all_channels.extend(channels)

    # 处理固定的 4K 频道
    content_4k = download_m3u("https://raw.githubusercontent.com/qunhui201/TVlogo/refs/heads/main/md/4K.m3u")
    channels_4k = parse_m3u(content_4k)
    all_channels.extend(channels_4k)

    # 写入输出文件
    output_lines = ["#EXTM3U"]
    tvbox_lines = []

    # 处理每个频道
    grouped_channels = {}

    for name, url, grp, logo in all_channels:
        final_group = classify_channel(name, grp, TVLOGO_DIR)
        
        # 将频道按分类分组
        if final_group not in grouped_channels:
            grouped_channels[final_group] = []
        
        grouped_channels[final_group].append((name, url))

    # 遍历分类
    for group, channels in grouped_channels.items():
        output_lines.append(f"#EXTINF:-1 group-title=\"{group}\", {group}")
        for name, url in channels:
            output_lines.append(url)
            tvbox_lines.append(f"📺{group},#genre#\n{name},{url}")

    # 生成 M3U 文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    # 生成 TVBox 格式的文件
    with open(TVBOX_OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(tvbox_lines))

    print(f"已生成 {OUTPUT_FILE}，共 {len(all_channels)} 个频道")
    print(f"已生成 {TVBOX_OUTPUT_FILE}，共 {len(tvbox_lines)} 个频道")

if __name__ == "__main__":
    main()

import os
import re
import requests
from pathlib import Path
from collections import defaultdict

# -------- 配置 ---------
REMOTE_FILES = [
    "http://iptv.catvod.com/tv.m3u",
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

TVLOGO_DIR = Path("TVlogo_Images")  # 台标根目录

PROVINCES = [
    "北京","上海","天津","重庆","辽宁","吉林","黑龙江","江苏","浙江","安徽",
    "福建","江西","山东","河南","湖北","湖南","广东","广西","海南","四川",
    "贵州","云南","陕西","甘肃","青海","宁夏","新疆","内蒙","西藏","香港",
    "澳门","台湾","延边","大湾区"
]

SPECIAL_CHANNELS = {"CCTV17": "央视频道"}

OUTPUT_FILE = "output.m3u"
TVBOX_TXT_FILE = "tvbox_output.txt"
OUTPUT_WITH_LOGO_FILE = "output_with_logo.m3u"
MISSING_LOGOS_FILE = "missing_logos.txt"

# -------- 函数 ---------
# 判断文件内容是否变化
def is_content_changed(file_path, new_content):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            old_content = f.read()
            return old_content != new_content
    return True  # 文件不存在时视为内容变化

# 下载 M3U 文件
def download_m3u(url):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.text

# 解析 M3U 文件内容
def parse_m3u(content):
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

# 分类频道
def classify_channel(name, original_group, tvlogo_dir):
    for key, val in SPECIAL_CHANNELS.items():
        if key in name:
            return val
    if original_group in ["央视频道", "卫视频道", "地方频道"]:
        return original_group
    if "卫视" in name:
        return "卫视频道"
    for province in PROVINCES:
        if province in name and "卫视" not in name:
            return "地方频道"
    for folder in tvlogo_dir.iterdir():
        if not folder.is_dir(): continue
        folder_name = folder.name
        if folder_name in ["央视频道", "卫视频道", "地方频道"]: continue
        for logo_file in folder.iterdir():
            if not logo_file.is_file(): continue
            filename = logo_file.stem
            ch_name = re.sub(r'^[A-Za-z0-9\+\-]+', '', filename)
            if ch_name and ch_name in name:
                return folder_name
    if name.isdigit() or not name:
        return "其他频道"
    return "其他频道"

# 生成 TVBox 格式文本文件
def generate_tvbox_txt(channels):
    grouped = defaultdict(list)
    for name, url, grp, logo in channels:
        final_group = classify_channel(name, grp, TVLOGO_DIR)
        grouped[final_group].append((name, url))

    lines = []
    for group in grouped:
        lines.append(f"📺{group},#genre#")
        for name, url in grouped[group]:
            lines.append(f"{name},{url}")

    new_tvbox_content = "\n".join(lines)
    if is_content_changed(TVBOX_TXT_FILE, new_tvbox_content):
        with open(TVBOX_TXT_FILE, "w", encoding="utf-8") as f:
            f.write(new_tvbox_content)
        print(f"✅ 已生成 {TVBOX_TXT_FILE}, 共 {len(channels)} 个频道")
    else:
        print(f"⚠️ 文件内容无变化，未生成 {TVBOX_TXT_FILE}")

# 生成 output_with_logo.m3u
def generate_output_with_logo(channels):
    out_lines = ["#EXTM3U"]
    missing_logos = []
    for name, url, grp, logo in channels:
        final_group = classify_channel(name, grp, TVLOGO_DIR)
        if not logo:
            missing_logos.append(f"{name}: {url}")
            out_lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="{final_group}",{name}')
        else:
            out_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{final_group}",{name}')
        out_lines.append(url)

    new_output_with_logo_content = "\n".join(out_lines)
    if is_content_changed(OUTPUT_WITH_LOGO_FILE, new_output_with_logo_content):
        with open(OUTPUT_WITH_LOGO_FILE, "w", encoding="utf-8") as f:
            f.write(new_output_with_logo_content)
        print(f"✅ 已生成 {OUTPUT_WITH_LOGO_FILE}, 共 {len(channels)} 个频道")
    else:
        print(f"⚠️ 文件内容无变化，未生成 {OUTPUT_WITH_LOGO_FILE}")

    if missing_logos:
        with open(MISSING_LOGOS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(missing_logos))
        print(f"⚠️ 未匹配台标的频道已保存至 {MISSING_LOGOS_FILE}，共 {len(missing_logos)} 个频道")

# -------- 主逻辑 ---------
def main():
    all_channels = []
    for url in REMOTE_FILES:
        content = download_m3u(url)
        channels = parse_m3u(content)
        all_channels.extend(channels)

    # 生成 output.m3u
    out_lines = ["#EXTM3U"]
    for name, url, grp, logo in all_channels:
        final_group = classify_channel(name, grp, TVLOGO_DIR)
        out_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{final_group}",{name}')
        out_lines.append(url)

    new_output_content = "\n".join(out_lines)
    if is_content_changed(OUTPUT_FILE, new_output_content):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(new_output_content)
        print(f"✅ 已生成 {OUTPUT_FILE}, 共 {len(all_channels)} 个频道")
    else:
        print(f"⚠️ 文件内容无变化，未生成 {OUTPUT_FILE}")

    # 生成 output_with_logo.m3u 和 tvbox_output.txt
    generate_output_with_logo(all_channels)
    generate_tvbox_txt(all_channels)

if __name__ == "__main__":
    main()

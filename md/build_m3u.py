import re
from pathlib import Path
from datetime import datetime
import requests

# -------- 配置 ---------
REMOTE_FILES = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

TVLOGO_DIR = Path("TVlogo_Images")
PROVINCES = [
    "北京", "上海", "天津", "重庆", "辽宁", "吉林", "黑龙江", "江苏", "浙江", "安徽", "福建", "江西",
    "山东", "河南", "湖北", "湖南", "广东", "广西", "海南", "四川", "贵州", "云南", "陕西", "甘肃",
    "青海", "宁夏", "新疆", "内蒙", "西藏", "香港", "澳门", "台湾", "延边", "大湾区"
]

SPECIAL_CHANNELS = {
    "CCTV17": "央视频道"
}

OUTPUT_FILE = "output.m3u"
TVBOX_FILE = "tvbox_output.txt"

# 固定 4K 频道文件（已有的文件）
FIXED_4K_URL = "https://raw.githubusercontent.com/qunhui201/TVlogo/refs/heads/main/md/4K.m3u"
FIXED_4K_GROUP = "4K频道"

# -------- 函数 ---------
def download_m3u(url):
    """下载 m3u 文件"""
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
            url = lines[i + 1] if i + 1 < len(lines) else ""
            tvg_name = re.search(r'tvg-name="([^"]+)"', info)
            group_title = re.search(r'group-title="([^"]+)"', info)
            tvg_logo = re.search(r'tvg-logo="([^"]+)"', info)
            name = tvg_name.group(1) if tvg_name else ""
            grp = group_title.group(1) if group_title else ""
            logo = tvg_logo.group(1) if tvg_logo else ""
            result.append((name, url, grp, logo))
    return result

def classify_channel(name, original_group, tvlogo_dir):
    """分类频道"""
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
        if not folder.is_dir():
            continue
        folder_name = folder.name
        if folder_name in ["央视频道", "卫视频道", "地方频道"]:
            continue
        for logo_file in folder.iterdir():
            if not logo_file.is_file():
                continue
            filename = logo_file.stem
            ch_name = re.sub(r'^[A-Za-z0-9\+\-]+', '', filename)
            if ch_name and ch_name in name:
                return folder_name
    if name.isdigit() or not name:
        return "其他频道"
    return "其他频道"

# -------- 主逻辑 ---------
def main():
    all_channels = []

    # 下载远程 M3U 文件
    for url in REMOTE_FILES:
        try:
            content = download_m3u(url)
            all_channels.extend(parse_m3u(content))
        except Exception as e:
            print(f"⚠️ 下载 {url} 失败: {e}")

    # 获取并合并固定 4K 频道（从 GitHub 上）
    try:
        content = download_m3u(FIXED_4K_URL)
        all_channels.extend([(name, url, FIXED_4K_GROUP, logo) 
                             for name, url, _, logo in parse_m3u(content)])
    except Exception as e:
        print(f"⚠️ 下载固定 4K 频道失败: {e}")

    # 写 output.m3u
    output_lines = ["#EXTM3U"]
    for name, url, grp, logo in all_channels:
        final_group = classify_channel(name, grp, TVLOGO_DIR)
        output_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{final_group}",{name}')
        output_lines.append(url)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print(f"✅ 已生成 {OUTPUT_FILE}, 共 {len(all_channels)} 个频道")

    # 写 tvbox_output.txt
    tvbox_lines = []
    current_group = None
    for name, url, grp, logo in all_channels:
        final_group = classify_channel(name, grp, TVLOGO_DIR)
        if current_group != final_group:
            current_group = final_group
            tvbox_lines.append(f"📺{current_group},#genre#")
        tvbox_lines.append(f"{name},{url}")
    with open(TVBOX_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(tvbox_lines))
    print(f"✅ 已生成 {TVBOX_FILE}, 共 {len(all_channels)} 个频道")

if __name__ == "__main__":
    main()

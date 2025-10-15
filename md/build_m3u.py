# build_m3u_safe.py
import re
import requests
from pathlib import Path

# --------- 配置 ---------
REMOTE_FILES = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

ALIAS_FILE = "md/mohupidao.txt"  # 可保留非央视/卫视频道别名映射
OUTPUT_FILE = "output_safe.m3u"

# 台标路径配置
LOGO_DIRS = [
    "TVlogo_Images/中央电视台",
    "TVlogo_Images/全国卫视",
    "TVlogo_Images/CGTN、中国教育电视台、新华社、中央新影",
    "TVlogo_Images/CIBN系列",
    "TVlogo_Images/DOX系列",
    "TVlogo_Images/NewTV系列",
    "TVlogo_Images/iHOT系列",
    "TVlogo_Images/地方频道"
]

# 备用 GitHub 图片路径
GITHUB_LOGO = "https://github.com/qunhui201/TVlogo/tree/main/img"

# --------- 函数 ---------
def load_alias_map(alias_file):
    alias_map = {}
    if not Path(alias_file).exists():
        return alias_map
    with open(alias_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            main_name = parts[0]
            for alias in parts[1:]:
                if alias.startswith("re:"):
                    alias_map[alias[3:]] = main_name
                else:
                    alias_map[re.escape(alias)] = main_name
    return alias_map

def download_m3u(url):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.text

def parse_m3u(content):
    """解析 m3u，返回列表 (tvg-name, url, group-title, tvg-logo, line_info)"""
    lines = content.splitlines()
    result = []
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            info = lines[i]
            url = lines[i+1] if i+1 < len(lines) else ""
            tvg_name = re.search(r'tvg-name="([^"]+)"', info)
            group_title = re.search(r'group-title="([^"]+)"', info)
            tvg_logo = re.search(r'tvg-logo="([^"]*)"', info)
            name = tvg_name.group(1) if tvg_name else ""
            grp = group_title.group(1) if group_title else ""
            logo = tvg_logo.group(1) if tvg_logo else ""
            result.append((name, url, grp, logo, info))
    return result

def find_logo(name):
    """
    尝试在本地台标路径匹配，找不到则返回 GitHub URL
    """
    for dir_path in LOGO_DIRS:
        path = Path(dir_path) / f"{name}.png"
        if path.exists():
            return str(path)
    return GITHUB_LOGO

# --------- 主逻辑 ---------
def main():
    alias_map = load_alias_map(ALIAS_FILE)
    all_channels = []

    # 下载远程 m3u
    for url in REMOTE_FILES:
        content = download_m3u(url)
        channels = parse_m3u(content)
        all_channels.extend(channels)

    # 按 tvg-name 聚合线路
    channel_dict = {}
    for name, url, grp, logo, info in all_channels:
        if name not in channel_dict:
            channel_dict[name] = {
                "group": grp,
                "logo": find_logo(name) if not logo else logo,
                "urls": []
            }
        channel_dict[name]["urls"].append(url)

    # 排序 tvg-name（央视频道按数字排序，其余按字母排序）
    def cctv_sort_key(name):
        m = re.match(r"CCTV[-]?(\d+)", name, re.IGNORECASE)
        if m:
            return int(m.group(1))
        return 1000 + hash(name) % 1000  # 保证非央视在后面按原顺序
    sorted_names = sorted(channel_dict.keys(), key=cctv_sort_key)

    # 输出 m3u
    output_lines = ["#EXTM3U"]
    for name in sorted_names:
        data = channel_dict[name]
        grp_final = data["group"]
        logo_final = data["logo"]
        for url in data["urls"]:
            output_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo_final}" group-title="{grp_final}",{name}')
            output_lines.append(url)

    # 写入输出文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"已生成 {OUTPUT_FILE}，共 {len(all_channels)} 条线路，{len(sorted_names)} 个频道")

if __name__ == "__main__":
    main()

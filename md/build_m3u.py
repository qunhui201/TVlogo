# build_m3u_logo.py
import re
import requests
from pathlib import Path

# --------- 配置 ---------
REMOTE_FILES = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

ALIAS_FILE = "md/mohupidao.txt"
OUTPUT_FILE = "output.m3u"

PROVINCES = [
    "北京", "上海", "天津", "重庆", "辽宁", "吉林", "黑龙江",
    "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南",
    "湖北", "湖南", "广东", "广西", "海南", "四川", "贵州",
    "云南", "陕西", "甘肃", "青海", "宁夏", "新疆", "内蒙",
    "西藏", "香港", "澳门", "台湾"
]

SERIES_LIST = ["CIBN", "DOX", "NewTV", "iHOT"]

GITHUB_LOGO_BASE = "https://raw.githubusercontent.com/qunhui201/TVlogo/main/img"

LOCAL_LOGO_PATH = Path("TVlogo_Images")

SPECIAL_GITHUB_NAMES = ["CGTN", "中国教育电视台", "新华社", "中央新影"]

# --------- 函数 ---------
def load_alias_map(alias_file):
    alias_map = {}
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

def apply_alias(name, alias_map):
    for pattern, main_name in alias_map.items():
        if re.match(pattern, name):
            return main_name
    return name

def download_m3u(url):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.text

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

def classify_channel(name, group):
    if group in ["央视", "卫视", "CCTV", "央视频道", "央视卫视", "卫视频道"]:
        return group
    for p in PROVINCES:
        if p in name and "卫视" not in name:
            return "地方频道"
    for s in SERIES_LIST:
        if s in name:
            return s
    return "其他频道"

def find_logo(name):
    # 特殊 GitHub 台标
    for special in SPECIAL_GITHUB_NAMES:
        if special in name:
            # 假设图片名和频道名相近
            return f"{GITHUB_LOGO_BASE}/{name}.png"

    # 优先在本地分类文件夹找台标
    for folder in LOCAL_LOGO_PATH.glob("**/*"):
        if folder.is_file() and name in folder.stem:
            return str(folder.resolve())
    
    # 本地找不到再去 GitHub
    return f"{GITHUB_LOGO_BASE}/{name}.png"

def main():
    alias_map = load_alias_map(ALIAS_FILE)
    all_channels = []

    for url in REMOTE_FILES:
        content = download_m3u(url)
        channels = parse_m3u(content)
        all_channels.extend(channels)

    # 应用别名
    processed = []
    seen_urls = set()
    for name, url, grp, _ in all_channels:
        if url in seen_urls:
            continue  # 去重
        seen_urls.add(url)
        name = apply_alias(name, alias_map)
        grp_final = classify_channel(name, grp)
        logo = find_logo(name)
        processed.append((name, url, grp_final, logo))

    # 对央视频道按数字排序
    cctv_channels = [x for x in processed if x[2] == "央视频道"]
    other_channels = [x for x in processed if x[2] != "央视频道"]

    def cctv_sort_key(item):
        m = re.search(r"CCTV[-]?(\d+)", item[0])
        return int(m.group(1)) if m else 0

    cctv_channels.sort(key=cctv_sort_key)
    final_list = cctv_channels + other_channels

    # 输出 M3U
    output_lines = ["#EXTM3U"]
    for name, url, grp, logo in final_list:
        output_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{grp}",{name}')
        output_lines.append(url)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"已生成 {OUTPUT_FILE}，共 {len(final_list)} 个频道")

if __name__ == "__main__":
    main()

# build_m3u.py
import re
import requests
from collections import defaultdict

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

# --------- 函数 ---------
def load_alias_map(alias_file):
    alias_map = {}
    try:
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
    except FileNotFoundError:
        print(f"别名文件 {alias_file} 不存在，跳过别名映射")
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
            group = group_title.group(1) if group_title else ""
            logo = tvg_logo.group(1) if tvg_logo else ""
            result.append((name, url, group, logo))
    return result

def classify_channel(name, group):
    if group in ["央视频道", "卫视频道"]:
        return group
    for p in PROVINCES:
        if p in name and "卫视" not in name:
            return "地方频道"
    for s in SERIES_LIST:
        if s in name:
            return s
    return "其他频道"

# 提取 CCTV 数字用于排序
def cctv_sort_key(name):
    match = re.match(r"CCTV[- ]?(\d+)", name)
    return int(match.group(1)) if match else 1000  # 非 CCTV 放后面

# --------- 主逻辑 ---------
def main():
    alias_map = load_alias_map(ALIAS_FILE)
    all_channels = []

    for url in REMOTE_FILES:
        try:
            content = download_m3u(url)
            channels = parse_m3u(content)
            all_channels.extend(channels)
        except Exception as e:
            print(f"下载 {url} 失败：{e}")

    # 应用别名并分类
    grouped = defaultdict(list)  # key: name, value: [(url, group, logo)]
    channel_info = {}            # name -> final group-title

    for name, url, group, logo in all_channels:
        name = apply_alias(name, alias_map)
        grp_final = classify_channel(name, group)
        grouped[name].append((url, logo))
        channel_info[name] = grp_final

    # 生成输出 M3U
    output_lines = ["#EXTM3U"]

    # 先输出央视频道，按数字排序
    cctv_names = [name for name in grouped if channel_info[name] == "央视频道"]
    for name in sorted(cctv_names, key=cctv_sort_key):
        for url, logo in grouped[name]:
            output_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="央视频道",{name}')
            output_lines.append(url)

    # 再输出卫视频道
    for name in grouped:
        if channel_info[name] == "卫视频道":
            for url, logo in grouped[name]:
                output_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="卫视频道",{name}')
                output_lines.append(url)

    # 再输出其他频道（地方、系列、其他）
    for name in grouped:
        if channel_info[name] not in ["央视频道", "卫视频道"]:
            for url, logo in grouped[name]:
                output_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{channel_info[name]}",{name}')
                output_lines.append(url)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"已生成 {OUTPUT_FILE}，共 {len(all_channels)} 个频道")

if __name__ == "__main__":
    main()

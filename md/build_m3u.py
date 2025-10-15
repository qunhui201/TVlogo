# build_m3u.py
import re
import requests

# --------- 配置 ---------
REMOTE_FILES = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

ALIAS_FILE = "md/mohupidao.txt"
OUTPUT_FILE = "output.m3u"

# 地方频道关键字（可以根据需要扩展）
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
    # 如果原文件就是央视或卫视，就直接返回原分组
    if group in ["央视", "卫视", "CCTV", "央视卫视", "卫视频道"]:
        return group
    # 判断地方频道
    for p in PROVINCES:
        if p in name and "卫视" not in name:
            return "地方频道"
    # 判断系列频道
    for s in SERIES_LIST:
        if s in name:
            return s
    # 其他
    return "其他频道"

# --------- 主逻辑 ---------
def main():
    alias_map = load_alias_map(ALIAS_FILE)
    all_channels = []

    # 下载远程 m3u
    for url in REMOTE_FILES:
        content = download_m3u(url)
        channels = parse_m3u(content)
        all_channels.extend(channels)

    # 应用别名并分类
    output_lines = ["#EXTM3U"]
    for name, url, grp, logo in all_channels:
        name = apply_alias(name, alias_map)
        grp_final = classify_channel(name, grp)
        output_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{grp_final}",{name}')
        output_lines.append(url)

    # 写入输出文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"已生成 {OUTPUT_FILE}，共 {len(all_channels)} 个频道")

if __name__ == "__main__":
    main()

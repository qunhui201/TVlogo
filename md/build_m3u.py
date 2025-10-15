# build_m3u.py
import re
import requests
import os

# --------- 配置 ---------
REMOTE_FILES = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

ALIAS_FILE = "md/mohupidao.txt"
OUTPUT_FILE = "output.m3u"

# 台标目录
LOGO_BASE = "TVlogo_Images"
LOGO_BACKUP = "https://github.com/qunhui201/TVlogo/tree/main/img"

# 地方频道关键字
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
    if not os.path.exists(alias_file):
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
            result.append({"name": name, "url": url, "group": grp, "logo": logo})
    return result

def classify_channel(name, group):
    if group in ["央视", "卫视", "CCTV", "央视卫视", "卫视频道", "央视频道"]:
        return "央视频道" if "CCTV" in name else group
    for p in PROVINCES:
        if p in name and "卫视" not in name:
            return "地方频道"
    for s in SERIES_LIST:
        if s in name:
            return s
    return "其他频道"

def find_logo(name):
    """
    台标查找逻辑：
    1. 本地分类目录优先
    2. CGTN、中国教育电视台、新华社、中央新影 -> GitHub 备用路径
    3. 其他地方频道 -> 本地文件夹找
    """
    special_folder = "CGTN、中国教育电视台、新华社、中央新影"
    cctv_folder = "中央电视台"
    weishi_folder = "全国卫视"

    # 央视台标
    if name.startswith("CCTV"):
        path = os.path.join(LOGO_BASE, cctv_folder, f"{name}.png")
        if os.path.exists(path):
            return path
        return os.path.join(LOGO_BACKUP, f"{name}.png")
    
    # 全国卫视
    for p in PROVINCES:
        if p in name and "卫视" in name:
            path = os.path.join(LOGO_BASE, weishi_folder, f"{name}.png")
            if os.path.exists(path):
                return path
            return os.path.join(LOGO_BACKUP, f"{name}.png")
    
    # 特殊台标
    if any(x in name for x in ["CGTN", "中国教育电视台", "新华社", "中央新影"]):
        path = os.path.join(LOGO_BACKUP, f"{name}.png")
        return path
    
    # 其他频道
    path = os.path.join(LOGO_BASE, name, f"{name}.png")
    if os.path.exists(path):
        return path
    return os.path.join(LOGO_BACKUP, f"{name}.png")

def cctv_sort_key(item):
    """
    CCTV 排序：
    先按数字，再按后缀，比如 CCTV5 < CCTV5+ < CCTV6
    """
    m = re.match(r"CCTV(\d+)(\+?)", item["name"])
    if m:
        num = int(m.group(1))
        suffix = m.group(2)
        return (num, suffix)
    else:
        return (100, item["name"])

# --------- 主逻辑 ---------
def main():
    alias_map = load_alias_map(ALIAS_FILE)
    all_channels = []

    for url in REMOTE_FILES:
        content = download_m3u(url)
        channels = parse_m3u(content)
        all_channels.extend(channels)

    # 应用别名、分类、台标
    for ch in all_channels:
        ch["name"] = apply_alias(ch["name"], alias_map)
        ch["group"] = classify_channel(ch["name"], ch["group"])
        ch["logo"] = find_logo(ch["name"])

    # CCTV 单独排序
    cctv_channels = [c for c in all_channels if c["group"] == "央视频道"]
    other_channels = [c for c in all_channels if c["group"] != "央视频道"]

    cctv_channels.sort(key=cctv_sort_key)

    # 生成输出
    output_lines = ["#EXTM3U"]
    for ch in cctv_channels + other_channels:
        output_lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}" tvg-logo="{ch["logo"]}" group-title="{ch["group"]}",{ch["name"]}')
        output_lines.append(ch["url"])

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"已生成 {OUTPUT_FILE}，共 {len(all_channels)} 个频道")

if __name__ == "__main__":
    main()

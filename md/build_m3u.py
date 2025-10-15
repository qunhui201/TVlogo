# build_m3u_no_sort.py
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

# 台标文件夹路径
LOGO_PATHS = {
    "中央电视台": "TVlogo_Images/中央电视台",
    "全国卫视": "TVlogo_Images/全国卫视",
    "CGTN、中国教育电视台、新华社、中央新影": "TVlogo_Images/CGTN、中国教育电视台、新华社、中央新影",
    "CIBN系列": "TVlogo_Images/CIBN系列",
    "DOX系列": "TVlogo_Images/DOX系列",
    "NewTV系列": "TVlogo_Images/NewTV系列",
    "iHOT系列": "TVlogo_Images/iHOT系列",
}

# 备用台标路径（GitHub）
FALLBACK_LOGO = "https://github.com/qunhui201/TVlogo/tree/main/img"

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

def find_logo(name):
    # 按分类台标查找
    for folder, path in LOGO_PATHS.items():
        if folder in name or name in folder:
            # 假设 logo 文件名与频道名相同
            logo_file = f"{path}/{name}.png"
            return logo_file
    # fallback
    return FALLBACK_LOGO

# --------- 主逻辑 ---------
def main():
    alias_map = load_alias_map(ALIAS_FILE)
    all_channels = []

    # 下载远程 m3u
    for url in REMOTE_FILES:
        content = download_m3u(url)
        channels = parse_m3u(content)
        all_channels.extend(channels)

    # 应用别名并匹配台标
    output_lines = ["#EXTM3U"]
    for name, url, grp, logo in all_channels:
        name = apply_alias(name, alias_map)
        if not logo:
            logo = find_logo(name)
        output_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{grp}",{name}')
        output_lines.append(url)

    # 写入输出文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"已生成 {OUTPUT_FILE}，共 {len(all_channels)} 个频道")

if __name__ == "__main__":
    main()

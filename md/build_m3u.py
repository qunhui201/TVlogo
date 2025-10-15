# build_m3u_classify_full_v3.py
import re
import requests
from pathlib import Path

# -------- 配置 ---------
REMOTE_FILES = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

TVLOGO_DIR = Path("TVlogo_Images")  # 台标根目录
OUTPUT_FILE = "output.m3u"

FIXED_EPG_URL = "https://gh.catmak.name/https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"

PROVINCES = [
    "北京","上海","天津","重庆","辽宁","吉林","黑龙江","江苏","浙江","安徽","福建","江西",
    "山东","河南","湖北","湖南","广东","广西","海南","四川","贵州","云南","陕西","甘肃",
    "青海","宁夏","新疆","内蒙","西藏","香港","澳门","台湾"
]

SPECIAL_CHANNELS = {
    "CCTV17": "央视频道"  # 特例处理
}

LOCAL_SUFFIX = ["新闻","生活","影视","都市","文体","少儿"]
THIRD_PARTY = ["CIBN","DOX","NewTV","iHOT","数字频道","台湾频道一","台湾频道二","台湾频道三"]

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

def match_logo(name, group, tvlogo_dir):
    """根据分类和频道名反向匹配台标"""
    # 特殊分类不匹配，直接返回空或已有 logo
    if group in ["央视频道", "卫视频道", "地方频道"]:
        search_dirs = [tvlogo_dir / group]
    else:
        # 其他分类
        search_dirs = [tvlogo_dir / group]

    for folder in search_dirs:
        if not folder.exists() or not folder.is_dir():
            continue
        for file in folder.iterdir():
            if file.is_file():
                # 忽略英文前缀，匹配中文频道名
                ch_name = re.sub(r'^[A-Za-z0-9\+\-]+', '', file.stem)
                if ch_name and ch_name in name:
                    return str(file.resolve())
    return ""  # 未匹配到返回空

def classify_channel(name, original_group, tvlogo_dir):
    """分类逻辑"""
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
    for suffix in LOCAL_SUFFIX:
        if name.endswith(suffix):
            return "地方频道"

    # 第三方系列匹配
    for series in THIRD_PARTY:
        if series in name:
            return series

    # 数字或未知
    if name.isdigit() or not name:
        return "其他频道"

    return "其他频道"

# -------- 主逻辑 ---------
def main():
    all_channels = []

    # 下载远程 M3U 文件
    for url in REMOTE_FILES:
        content = download_m3u(url)
        channels = parse_m3u(content)
        all_channels.extend(channels)

    # 写入输出文件
    output_lines = [f'#EXTM3U x-tvg-url="{FIXED_EPG_URL}"']

    for name, url, grp, logo in all_channels:
        final_group = classify_channel(name, grp, TVLOGO_DIR)
        if not logo:
            logo = match_logo(name, final_group, TVLOGO_DIR)
        output_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{final_group}",{name}')
        output_lines.append(url)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"已生成 {OUTPUT_FILE}，共 {len(all_channels)} 个频道")

if __name__ == "__main__":
    main()

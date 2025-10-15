# build_m3u_classify_ignore_prefix.py
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

PROVINCES = [
    "北京","上海","天津","重庆","辽宁","吉林","黑龙江","江苏","浙江","安徽","福建","江西",
    "山东","河南","湖北","湖南","广东","广西","海南","四川","贵州","云南","陕西","甘肃",
    "青海","宁夏","新疆","内蒙","西藏","香港","澳门","台湾"
]

LOCAL_SUFFIX = ["新闻","生活","影视","都市","文体","少儿"]

# -------- 函数 ---------
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

def classify_channel(name, original_group, tvlogo_dir):
    """分类逻辑"""
    # 保留央视、卫视、地方频道原分组
    if original_group in ["央视频道", "卫视频道", "地方频道"]:
        return original_group

    # 第三方系列匹配，忽略英文前缀
    for folder in tvlogo_dir.iterdir():
        if not folder.is_dir():
            continue
        for logo_file in folder.iterdir():
            if not logo_file.is_file():
                continue
            # 去掉英文前缀匹配中文名字
            filename = logo_file.stem  # 不带扩展名
            # 移除英文前缀，比如 NewTV东北热剧 -> 东北热剧
            ch_name = re.sub(r'^[A-Za-z0-9\+\-]+', '', filename)
            if ch_name in name:
                return folder.name

    # 数字或未知
    if name.isdigit() or not name:
        return "其他频道"

    return "其他频道"

# -------- 主逻辑 ---------
def main():
    all_channels = []

    # 下载远程 m3u
    for url in REMOTE_FILES:
        content = download_m3u(url)
        channels = parse_m3u(content)
        all_channels.extend(channels)

    output_lines = ["#EXTM3U"]
    for name, url, grp, logo in all_channels:
        final_group = classify_channel(name, grp, TVLOGO_DIR)
        output_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{final_group}",{name}')
        output_lines.append(url)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"已生成 {OUTPUT_FILE}，共 {len(all_channels)} 个频道")

if __name__ == "__main__":
    main()

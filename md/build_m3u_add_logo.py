# build_m3u_add_logo.py
import re
from pathlib import Path

INPUT_FILE = "output.m3u"  # 分类完成后的 M3U
OUTPUT_FILE = "output_with_logo.m3u"
TVLOGO_DIR = Path("TVlogo_Images")

PROVINCES = [
    "北京","上海","天津","重庆","辽宁","吉林","黑龙江","江苏","浙江","安徽","福建","江西",
    "山东","河南","湖北","湖南","广东","广西","海南","四川","贵州","云南","陕西","甘肃",
    "青海","宁夏","新疆","内蒙","西藏","香港","澳门","台湾","延边","大湾区"
]

def match_logo(channel_name, group_title):
    """根据频道类别和台标目录匹配台标"""
    logo_path = ""

    if group_title == "央视频道":
        folder = TVLOGO_DIR / "中央电视台"
        file_path = folder / f"{channel_name}.png"
        if file_path.exists():
            logo_path = str(file_path)
    elif group_title == "卫视频道":
        folder = TVLOGO_DIR / "全国卫视"
        file_path = folder / f"{channel_name}.png"
        if file_path.exists():
            logo_path = str(file_path)
    elif group_title == "地方频道":
        matched = False
        for province in PROVINCES:
            if province in channel_name:
                folder = TVLOGO_DIR / province
                file_path = folder / f"{channel_name}.png"
                if file_path.exists():
                    logo_path = str(file_path)
                    matched = True
                    break
        if not matched:
            logo_path = ""
    else:
        # 第三方系列/其他频道
        for folder in TVLOGO_DIR.iterdir():
            if not folder.is_dir():
                continue
            if folder.name in ["中央电视台", "全国卫视"] + PROVINCES:
                continue
            for file in folder.iterdir():
                if not file.is_file():
                    continue
                filename = file.stem
                # 忽略英文前缀
                ch_name = re.sub(r'^[A-Za-z0-9\+\-]+', '', filename)
                if ch_name and ch_name in channel_name:
                    logo_path = str(file)
                    break
            if logo_path:
                break

    return logo_path

def main():
    output_lines = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF"):
            info = line
            url = lines[i+1] if i+1 < len(lines) else ""
            tvg_name = re.search(r'tvg-name="([^"]+)"', info)
            group_title = re.search(r'group-title="([^"]+)"', info)
            name = tvg_name.group(1) if tvg_name else ""
            group = group_title.group(1) if group_title else ""
            logo = match_logo(name, group)
            output_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}')
            output_lines.append(url)
            i += 2
        else:
            output_lines.append(line)
            i += 1

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"已生成 {OUTPUT_FILE}，共 {sum(1 for l in output_lines if l.startswith('#EXTINF'))} 个频道")

if __name__ == "__main__":
    main()

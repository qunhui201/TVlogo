# build_m3u_add_logo.py
import re
from pathlib import Path

# -------- 配置 ---------
INPUT_FILE = "output.m3u"          # 已生成的 M3U 文件
TVLOGO_DIR = Path("TVlogo_Images")  # 台标根目录
OUTPUT_FILE = "output_with_logo.m3u"

# -------- 函数 ---------
def parse_m3u_lines(lines):
    """解析 M3U 内容，返回 [(info_line, url_line)]"""
    result = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            info = lines[i]
            url = lines[i+1] if i+1 < len(lines) else ""
            result.append([info, url])
            i += 2
        else:
            i += 1
    return result

def match_logo(name, group, tvlogo_dir):
    """根据分类和频道名反向匹配台标"""
    search_dir = tvlogo_dir / group
    if not search_dir.exists() or not search_dir.is_dir():
        return ""
    for file in search_dir.iterdir():
        if not file.is_file():
            continue
        filename = file.stem
        ch_name = re.sub(r'^[A-Za-z0-9\+\-]+', '', filename)  # 忽略英文前缀
        if ch_name and ch_name in name:
            return str(file.resolve())
    return ""

# -------- 主逻辑 ---------
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    channel_entries = parse_m3u_lines(lines)
    output_lines = []
    
    # 保留 #EXTM3U 行开头
    if lines and lines[0].startswith("#EXTM3U"):
        output_lines.append(lines[0])

    for info, url in channel_entries:
        tvg_name_match = re.search(r'tvg-name="([^"]+)"', info)
        group_match = re.search(r'group-title="([^"]+)"', info)
        name = tvg_name_match.group(1) if tvg_name_match else ""
        group = group_match.group(1) if group_match else ""
        
        logo = match_logo(name, group, TVLOGO_DIR)
        # 替换或添加 tvg-logo
        if 'tvg-logo="' in info:
            info = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{logo}"', info)
        else:
            info = info.replace('group-title="', f'tvg-logo="{logo}" group-title="')
        
        output_lines.append(info)
        output_lines.append(url)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"已生成 {OUTPUT_FILE}，共 {len(channel_entries)} 个频道")

if __name__ == "__main__":
    main()

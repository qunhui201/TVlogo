# build_m3u_add_logo.py
import re
from pathlib import Path

# -------- 配置 ---------
INPUT_FILE = "output.m3u"         # 原 M3U 文件（分类完成）
TVLOGO_DIR = Path("TVlogo_Images")  # 台标根目录
OUTPUT_FILE = "output_with_logo.m3u"

# 保留原有三类
RESERVED_GROUPS = ["央视频道", "卫视频道", "地方频道"]

# -------- 函数 ---------
def parse_m3u(file_path):
    """解析 M3U 文件"""
    lines = Path(file_path).read_text(encoding="utf-8").splitlines()
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
            result.append({"name": name, "url": url, "group": grp, "logo": logo})
    return result

def match_logo(channel_name):
    """根据 TVlogo 文件夹匹配台标，只针对非央视/卫视/地方"""
    for folder in TVLOGO_DIR.iterdir():
        if not folder.is_dir():
            continue
        folder_name = folder.name
        if folder_name in RESERVED_GROUPS:
            continue
        # 遍历文件夹内所有图片文件
        for file in folder.iterdir():
            if not file.is_file():
                continue
            stem = file.stem
            # 忽略英文前缀、数字、下划线、加号等
            clean_name = re.sub(r'^[A-Za-z0-9_\+\-]+', '', stem)
            if clean_name and clean_name in channel_name:
                # 构造台标 URL
                return f"{TVLOGO_DIR}/{folder_name}/{file.name}"
    return ""

# -------- 主逻辑 ---------
def main():
    channels = parse_m3u(INPUT_FILE)
    output_lines = ["#EXTM3U x-tvg-url=\"https://gh.catmak.name/https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz\""]

    for ch in channels:
        final_logo = ch["logo"]
        if ch["group"] not in RESERVED_GROUPS:
            # 尝试匹配台标
            logo_path = match_logo(ch["name"])
            if logo_path:
                final_logo = logo_path
        # 写入
        output_lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}" tvg-logo="{final_logo}" group-title="{ch["group"]}",{ch["name"]}')
        output_lines.append(ch["url"])

    Path(OUTPUT_FILE).write_text("\n".join(output_lines), encoding="utf-8")
    print(f"已生成 {OUTPUT_FILE}，共 {len(channels)} 个频道")

if __name__ == "__main__":
    main()

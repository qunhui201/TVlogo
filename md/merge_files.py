import os
import re
from pathlib import Path

# ===== 配置部分 =====
folder = Path("history")  # 存放生成文件的文件夹
output_m3u = folder / "merged.m3u"
output_txt = folder / "merged.txt"

tvg_header = '#EXTM3U x-tvg-url="https://epg.v1.mk/fy.xml"\n'

# 匹配 #EXTINF 与其下链接
pattern = re.compile(r'(#EXTINF[^\n]*\n)(http[^\n]+)', re.MULTILINE)

# ===== 提取函数 =====
def extract_entries(file_path):
    entries = []
    if not file_path.exists():
        return entries

    text = file_path.read_text(encoding="utf-8", errors="ignore")

    for match in pattern.finditer(text):
        extinf, url = match.groups()
        entries.append((extinf.strip(), url.strip()))
    return entries


# ===== 合并去重 + 分类排序 =====
def merge_files(extension):
    all_entries = []
    for file in folder.glob(f"*.{extension}"):
        if file.name.startswith("merged."):
            continue
        all_entries.extend(extract_entries(file))

    # 按 URL 去重
    seen_urls = set()
    unique_entries = []
    for extinf, url in all_entries:
        if url not in seen_urls:
            seen_urls.add(url)
            unique_entries.append((extinf, url))

    # 分类分组
    yangshi = []   # 央视频道
    weishi = []    # 卫视频道
    others = []    # 其他频道

    for extinf, url in unique_entries:
        if '央视频道' in extinf:
            yangshi.append((extinf, url))
        elif '卫视频道' in extinf:
            weishi.append((extinf, url))
        else:
            others.append((extinf, url))

    # 按顺序组合
    ordered = yangshi + weishi + others

    # 生成内容
    lines = [tvg_header]
    for extinf, url in ordered:
        lines.append(extinf)
        lines.append(url)

    return "\n".join(lines) + "\n"


# ===== 主函数 =====
def main():
    print("📺 正在合并去重 M3U 文件...")
    merged_m3u_content = merge_files("m3u")
    output_m3u.write_text(merged_m3u_content, encoding="utf-8")

    print("📄 正在合并去重 TXT 文件...")
    merged_txt_content = merge_files("txt")
    output_txt.write_text(merged_txt_content, encoding="utf-8")

    print("✅ 合并完成！输出文件：")
    print(f" - {output_m3u}")
    print(f" - {output_txt}")


if __name__ == "__main__":
    main()

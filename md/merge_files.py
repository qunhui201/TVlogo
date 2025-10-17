import os
import re
from pathlib import Path

folder = Path("history")
output_m3u = folder / "merged.m3u"
output_txt = folder / "merged.txt"

tvg_header = '#EXTM3U x-tvg-url="https://epg.v1.mk/fy.xml"\n'

# 匹配 #EXTINF 与后面可能的链接
extinf_pattern = re.compile(r'(#EXTINF[^\n]*\n)?(http[^\n]+)', re.MULTILINE)

def extract_entries(file_path):
    entries = []
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    matches = extinf_pattern.findall(text)

    for extinf, url in matches:
        # 如果没有EXTINF，则用默认信息占位
        if not extinf.strip():
            extinf = f'#EXTINF:-1 tvg-name="" tvg-logo="" group-title="未知频道",未知频道'
        entries.append((extinf.strip(), url.strip()))
    return entries

def merge_files(extension):
    all_entries = []
    for file in folder.glob(f"*.{extension}"):
        if file.name.startswith("merged."):
            continue
        all_entries.extend(extract_entries(file))

    # 去重（按链接）
    seen = set()
    unique_entries = []
    for extinf, url in all_entries:
        if url not in seen:
            seen.add(url)
            unique_entries.append((extinf, url))

    # 分类排序
    cctv, weishi, others = [], [], []
    for extinf, url in unique_entries:
        if "央视频道" in extinf:
            cctv.append((extinf, url))
        elif "卫视频道" in extinf:
            weishi.append((extinf, url))
        else:
            others.append((extinf, url))

    ordered = cctv + weishi + others

    lines = [tvg_header]
    for extinf, url in ordered:
        lines.append(extinf)
        lines.append(url)
    return "\n".join(lines) + "\n"

def main():
    print("📺 合并 M3U 文件中...")
    m3u_content = merge_files("m3u")
    output_m3u.write_text(m3u_content, encoding="utf-8")

    print("📄 合并 TXT 文件中...")
    txt_content = merge_files("txt")
    output_txt.write_text(txt_content, encoding="utf-8")

    print("✅ 合并完成！")
    print(f" - {output_m3u}")
    print(f" - {output_txt}")

if __name__ == "__main__":
    main()

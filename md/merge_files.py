#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 功能：合并 history/ 下的 .m3u 和 .txt 文件
# 去重逻辑：
#   - 以链接(URL)为唯一判断标准
#   - 每个链接对应的 #EXTINF + URL 对只保留一次
#   - 输出文件首行自动添加 #EXTM3U 头部，便于播放器识别

import os

FOLDER = "history"
ENCODING = "utf-8"

# 标准 M3U 文件头（可自定义）
HEADER_LINE = '#EXTM3U x-tvg-url="https://epg.v1.mk/fy.xml"'


def merge_pair_files(folder: str, extension: str, output_filename: str):
    """合并 .m3u 或 .txt 文件：只按链接去重"""
    seen_urls = set()
    merged_pairs = []

    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith(extension):
            continue
        path = os.path.join(folder, fname)
        try:
            with open(path, "r", encoding=ENCODING, errors="ignore") as f:
                lines = [line.strip() for line in f if line.strip()]
                i = 0
                while i < len(lines):
                    line = lines[i]
                    # 跳过文件头 #EXTM3U
                    if line.startswith("#EXTM3U"):
                        i += 1
                        continue
                    # 匹配频道标题
                    if line.startswith("#EXTINF"):
                        if i + 1 < len(lines):
                            url = lines[i + 1]
                            if url not in seen_urls:
                                seen_urls.add(url)
                                merged_pairs.append((line, url))
                        i += 2
                    else:
                        i += 1
        except Exception as e:
            print(f"⚠️ 读取文件出错: {path} -> {e}")

    out_path = os.path.join(folder, output_filename)
    with open(out_path, "w", encoding=ENCODING) as out:
        out.write(f"{HEADER_LINE}\n")
        for title, url in merged_pairs:
            out.write(f"{title}\n{url}\n")

    print(f"✅ 合并完成: {out_path}，共 {len(merged_pairs)} 条频道链接")


if __name__ == "__main__":
    if not os.path.isdir(FOLDER):
        print(f"❌ 未找到目录: {FOLDER}")
        raise SystemExit(1)

    merge_pair_files(FOLDER, ".m3u", "merged.m3u")
    merge_pair_files(FOLDER, ".txt", "merged.txt")

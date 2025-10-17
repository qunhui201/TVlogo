#!/usr/bin/env python3
# merge_files.py
# 合并 history/ 下的 .m3u 和 .txt 文件
# 去重规则：
#  - .m3u: 保留相同标题下不同的链接；只在 (标题, 链接) 完全相同的情况下去重
#  - .txt: 完全相同行去重

import os
from collections import OrderedDict

FOLDER = "history"
OUTPUT_M3U = "merged.m3u"
OUTPUT_TXT = "merged.txt"
ENCODING = "utf-8"

def merge_m3u(folder, output_filename):
    # 用 OrderedDict 保持标题插入顺序，值为按顺序出现的链接列表
    title_to_urls = OrderedDict()
    seen_pairs = set()  # (title, url) 去重标记

    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith(".m3u"):
            continue
        path = os.path.join(folder, fname)
        try:
            with open(path, "r", encoding=ENCODING, errors="ignore") as f:
                current_title = None
                for raw in f:
                    line = raw.rstrip("\n")
                    if not line:
                        continue
                    if line.startswith("#EXTINF"):
                        current_title = line
                        # 确保 dict 有此标题（但不立刻写入文件）
                        if current_title not in title_to_urls:
                            title_to_urls[current_title] = []
                    else:
                        # 非 #EXTINF 行当作 URL（或者其他信息），以第一个非空非注释行视为链接
                        if current_title is None:
                            # 没有标题就跳过（防止文件格式异常）
                            continue
                        url = line.strip()
                        pair = (current_title, url)
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            title_to_urls[current_title].append(url)
        except Exception as e:
            print(f"⚠️ 读取文件出错: {path} -> {e}")

    # 写入合并文件：每个标题写一次，紧接着写其所有 URL（每行一条）
    out_path = os.path.join(folder, output_filename)
    total_pairs = 0
    with open(out_path, "w", encoding=ENCODING) as out:
        for title, urls in title_to_urls.items():
            if not urls:
                continue
            out.write(f"{title}\n")
            for u in urls:
                out.write(f"{u}\n")
                total_pairs += 1

    print(f"✅ 合并 .m3u 完成 -> {out_path} （标题数: {len(title_to_urls)}, 链接对数: {total_pairs}）")


def merge_txt(folder, output_filename):
    seen = set()
    merged_lines = []
    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith(".txt"):
            continue
        path = os.path.join(folder, fname)
        try:
            with open(path, "r", encoding=ENCODING, errors="ignore") as f:
                for raw in f:
                    line = raw.strip()
                    if not line:
                        continue
                    if line not in seen:
                        seen.add(line)
                        merged_lines.append(line)
        except Exception as e:
            print(f"⚠️ 读取文件出错: {path} -> {e}")

    out_path = os.path.join(folder, output_filename)
    with open(out_path, "w", encoding=ENCODING) as out:
        out.write("\n".join(merged_lines))
    print(f"✅ 合并 .txt 完成 -> {out_path} （去重后行数: {len(merged_lines)}）")


if __name__ == "__main__":
    if not os.path.isdir(FOLDER):
        print(f"❌ 未找到目录: {FOLDER}")
        raise SystemExit(1)

    merge_m3u(FOLDER, OUTPUT_M3U)
    merge_txt(FOLDER, OUTPUT_TXT)

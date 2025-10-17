#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 功能：合并 history/ 下的 .m3u 和 .txt 文件
# 去重逻辑：
#   - .m3u 文件：只根据链接(URL)去重，保留每个链接第一次出现对应的 #EXTINF + URL 对
#   - .txt 文件：整行内容去重

import os

FOLDER = "history"
ENCODING = "utf-8"


def merge_m3u(folder, output_file):
    seen_urls = set()
    merged_pairs = []

    # 遍历所有 .m3u 文件
    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith(".m3u"):
            continue
        path = os.path.join(folder, fname)
        try:
            with open(path, "r", encoding=ENCODING, errors="ignore") as f:
                lines = [line.strip() for line in f if line.strip()]
                i = 0
                while i < len(lines):
                    line = lines[i]
                    # 如果是标题行
                    if line.startswith("#EXTINF"):
                        if i + 1 < len(lines):
                            url = lines[i + 1]
                            # 如果链接未出现过，则保留这一对
                            if url not in seen_urls:
                                seen_urls.add(url)
                                merged_pairs.append((line, url))
                        i += 2
                    else:
                        # 如果不是 #EXTINF 就直接跳过（防止某些异常行）
                        i += 1
        except Exception as e:
            print(f"⚠️ 读取 {fname} 出错: {e}")

    # 写出结果
    out_path = os.path.join(folder, output_file)
    with open(out_path, "w", encoding=ENCODING) as out:
        for title, url in merged_pairs:
            out.write(f"{title}\n{url}\n")

    print(f"✅ 合并完成: {out_path}，共 {len(merged_pairs)} 条频道链接")


def merge_txt(folder, output_file):
    seen = set()
    merged_lines = []

    for fname in sorted(os.listdir(folder)):
        if not fname.lower().endswith(".txt"):
            continue
        path = os.path.join(folder, fname)
        try:
            with open(path, "r", encoding=ENCODING, errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line not in seen:
                        seen.add(line)
                        merged_lines.append(line)
        except Exception as e:
            print(f"⚠️ 读取 {fname} 出错: {e}")

    out_path = os.path.join(folder, output_file)
    with open(out_path, "w", encoding=ENCODING) as out:
        out.write("\n".join(merged_lines))
    print(f"✅ 合并完成: {out_path}，共 {len(merged_lines)} 行")


if __name__ == "__main__":
    if not os.path.isdir(FOLDER):
        print(f"❌ 未找到目录: {FOLDER}")
        raise SystemExit(1)

    merge_m3u(FOLDER, "merged.m3u")
    merge_txt(FOLDER, "merged.txt")

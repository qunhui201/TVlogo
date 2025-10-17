import os

# 文件夹路径（相对或绝对）
folder = "history"

def merge_files(extension, output_filename):
    seen_lines = set()
    merged_lines = []

    for filename in os.listdir(folder):
        if filename.endswith(extension):
            filepath = os.path.join(folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and line not in seen_lines:
                        seen_lines.add(line)
                        merged_lines.append(line)

    output_path = os.path.join(folder, output_filename)
    with open(output_path, "w", encoding="utf-8") as out:
        out.write("\n".join(merged_lines))
    print(f"✅ 合并完成: {output_path}，共 {len(merged_lines)} 行")

if __name__ == "__main__":
    merge_files(".m3u", "merged.m3u")
    merge_files(".txt", "merged.txt")

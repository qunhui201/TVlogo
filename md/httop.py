# md/httop.py
import os

# 输入文件
channels_file = "channels.txt"

# 输出文件
m3u_file = "output.m3u"
tvbox_file = "channels_tvbox.txt"

# 读取频道列表
with open(channels_file, "r", encoding="utf-8") as f:
    lines = [line.strip() for line in f if line.strip()]

# 初始化
m3u_lines = ["#EXTM3U"]
tvbox_lines = []

current_group = None

for line in lines:
    if line.startswith("#"):
        current_group = line[1:].strip()
        tvbox_lines.append(line)  # 直接写入txt
        continue
    # 构建 M3U，每个频道用示例URL占位，可替换
    url = f"http://example.com/stream/{line.replace(' ', '_')}.m3u8"
    m3u_lines.append(f'#EXTINF:-1,group-title="{current_group}",{line}')
    m3u_lines.append(url)
    tvbox_lines.append(line)

# 写入 M3U
with open(m3u_file, "w", encoding="utf-8") as f:
    f.write("\n".join(m3u_lines))

# 写入 TVBox TXT
with open(tvbox_file, "w", encoding="utf-8") as f:
    f.write("\n".join(tvbox_lines))

print(f"完成: {m3u_file} 和 {tvbox_file}")


# -----------------------------
# 抓取 M3U
# -----------------------------
all_channels = []
channel_names = set()

for url in M3U_URLS:
    print(f"Fetching {url} ...")
    r = requests.get(url, timeout=15)
    r.encoding = 'utf-8'
    lines = r.text.splitlines()
    
    for i, line in enumerate(lines):
        if line.startswith("#EXTINF:"):
            title_line = line
            stream_line = lines[i+1] if i+1 < len(lines) else ""
            # 提取 tvg-name 和 group-title
            tvg_name = ""
            group_title = ""
            try:
                tvg_name = title_line.split('tvg-name="')[1].split('"')[0]
            except:
                tvg_name = title_line.split(',')[-1].strip()
            try:
                group_title = title_line.split('group-title="')[1].split('"')[0]
            except:
                group_title = "其它频道"

            if tvg_name in channel_names:
                continue  # 去重
            channel_names.add(tvg_name)

            # 匹配台标
            logo_path = logos.get(tvg_name, "")

            # 构建新的 EXTINF 行
            new_extinf = f'#EXTINF:-1 tvg-id="{tvg_name}" tvg-name="{tvg_name}" tvg-logo="{logo_path}" group-title="{group_title}",{tvg_name}'
            
            all_channels.append((new_extinf, stream_line))

# -----------------------------
# 写入 M3U 文件
# -----------------------------
with open(output_m3u, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for extinf, url in all_channels:
        f.write(f"{extinf}\n{url}\n")

# -----------------------------
# 写入频道列表文件
# -----------------------------
with open(channel_list_file, "w", encoding="utf-8") as f:
    for name in sorted(channel_names):
        f.write(f"{name}\n")

print(f"完成: {output_m3u} 和 {channel_list_file}")

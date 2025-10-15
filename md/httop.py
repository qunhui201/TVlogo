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
        tvbox_lines.append(line)  # 写入 TVBox TXT
        continue
    # 构建 M3U，每个频道用示例URL占位，可替换为真实链接
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

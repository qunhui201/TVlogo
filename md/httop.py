import requests

# 远程 M3U 链接
urls = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

# 输出文件
output_m3u = "output.m3u"
output_tvbox = "channels_tvbox.txt"

all_lines = []

for url in urls:
    resp = requests.get(url, timeout=10)
    resp.encoding = 'utf-8'  # 保证中文正常
    lines = resp.text.splitlines()
    all_lines.extend(lines)

# 写 output.m3u
with open(output_m3u, "w", encoding="utf-8") as f:
    f.write("\n".join(all_lines))

# 写 channels_tvbox.txt （只保留频道名称和 URL，2行一个集合）
tvbox_list = []
i = 0
while i < len(all_lines):
    line = all_lines[i]
    if line.startswith("#EXTINF:"):
        # 获取频道名
        name = line.split(",")[-1].strip()
        url = all_lines[i + 1].strip() if i + 1 < len(all_lines) else ""
        tvbox_list.append(name)
        tvbox_list.append(url)
        i += 2
    else:
        i += 1

with open(output_tvbox, "w", encoding="utf-8") as f:
    f.write("\n".join(tvbox_list))

print(f"完成: {output_m3u} 和 {output_tvbox}")

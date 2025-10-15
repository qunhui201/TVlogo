import requests
from pathlib import Path

# -----------------------------
# 配置
# -----------------------------
M3U_URLS = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

# 台标文件夹（仓库根目录的 TVlogo_Images）
repo_root = Path(__file__).parent.parent
logo_base = repo_root / "TVlogo_Images"

# 输出文件
output_m3u = repo_root / "output.m3u"
channel_list_file = repo_root / "channels.txt"

# -----------------------------
# 检查台标文件夹
# -----------------------------
if not logo_base.exists():
    raise FileNotFoundError(f"台标文件夹不存在: {logo_base}")

# 遍历台标文件夹，建立映射 {频道名: 台标路径}
logos = {}
for folder in logo_base.iterdir():
    if folder.is_dir():
        for logo_file in folder.iterdir():
            if logo_file.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                logos[logo_file.stem] = logo_file.as_posix()

print(f"共找到 {len(logos)} 个台标文件")

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

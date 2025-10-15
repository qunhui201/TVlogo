# httop.py
import requests
import re
from pathlib import Path

# 两个 m3u 链接
urls = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

# GitHub 台标文件夹本地路径
logo_base = Path(__file__).parent / "TVlogo_Images"

# 输出文件
output_m3u = Path(__file__).parent / "merged_channels.m3u"
output_list = Path(__file__).parent / "channel_list.txt"

# 节目单链接模板（可统一修改）
epg_url_template = "https://github.com/qunhui201/TVlogo/tree/main/TVlogo_Images"

# 用来存储所有频道
channels = []

# 匹配 #EXTINF 信息
extinf_pattern = re.compile(r'#EXTINF:-1.*?,(.*)\n(.*)')

for url in urls:
    print(f"Fetching {url} ...")
    r = requests.get(url, timeout=10)
    r.encoding = 'utf-8'
    text = r.text
    matches = extinf_pattern.findall(text)
    for title, link in matches:
        # 提取 group-title
        group_match = re.search(r'group-title="(.*?)"', title)
        group = group_match.group(1) if group_match else "未分类"
        # 提取 tvg-name
        name_match = re.search(r'tvg-name="(.*?)"', title)
        tvg_name = name_match.group(1) if name_match else title.strip()
        channels.append({
            "title": tvg_name,
            "group": group,
            "link": link.strip()
        })

# 去重（按 title + link）
seen = set()
unique_channels = []
for ch in channels:
    key = (ch['title'], ch['link'])
    if key not in seen:
        seen.add(key)
        unique_channels.append(ch)

# 写出频道列表备用
with open(output_list, "w", encoding="utf-8") as f:
    for ch in unique_channels:
        f.write(f"{ch['title']} ({ch['group']})\n")

# 生成新的 m3u
with open(output_m3u, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for ch in unique_channels:
        # 尝试匹配台标
        logo_path = ""
        # 台标命名规则示例：文件夹名/频道名.png
        for folder in logo_base.iterdir():
            if folder.is_dir():
                candidate = folder / f"{ch['title']}.png"
                if candidate.exists():
                    logo_path = f"{epg_url_template}/{folder.name}/{candidate.name}"
                    break
        # 写入 EXTINF
        f.write(f'#EXTINF:-1 tvg-name="{ch["title"]}" tvg-logo="{logo_path}" group-title="{ch["group"]}",{ch["title"]}\n')
        f.write(f'{ch["link"]}\n')

print(f"Done! {len(unique_channels)} channels merged.")
print(f"M3U output: {output_m3u}")
print(f"Channel list: {output_list}")


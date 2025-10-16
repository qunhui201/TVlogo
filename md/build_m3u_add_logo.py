import re
from pathlib import Path
import os

INPUT_FILE = "output.m3u"
OUTPUT_FILE = "output_with_logo.m3u"
MISSING_LOGO_FILE = "missing_logos.txt"
TVLOGO_DIR = Path("TVlogo_Images")
BASE_LOGO_URL = "https://raw.githubusercontent.com/qunhui201/TVlogo/main/TVlogo_Images"
PROVINCES = [
    "北京", "上海", "天津", "重庆", "辽宁", "吉林", "黑龙江", "江苏", "浙江", "安徽", "福建", "江西",
    "山东", "河南", "湖北", "湖南", "广东", "广西", "海南", "四川", "贵州", "云南", "陕西", "甘肃",
    "青海", "宁夏", "新疆", "内蒙", "西藏", "香港", "澳门", "台湾", "延边", "大湾区"
]

def normalize_name(name: str):
    return name.replace("频道", "").replace("台", "").strip()

def find_fuzzy_folder(name):
    for folder in TVLOGO_DIR.iterdir():
        if folder.is_dir() and name in folder.name:
            return folder
    return None

def match_logo(channel_name, group_title):
    logo_path = ""
    clean_name = normalize_name(channel_name)
    if group_title == "央视频道":
        folder = TVLOGO_DIR / "中央电视台"
        for variant in [channel_name, clean_name]:
            file_path = folder / f"{variant}.png"
            if file_path.exists():
                logo_path = f"{BASE_LOGO_URL}/中央电视台/{variant}.png"
                break
    elif group_title == "卫视频道":
        folder = TVLOGO_DIR / "全国卫视"
        for variant in [channel_name, clean_name]:
            file_path = folder / f"{variant}.png"
            if file_path.exists():
                logo_path = f"{BASE_LOGO_URL}/全国卫视/{variant}.png"
                break
    elif group_title == "地方频道":
        for province in PROVINCES:
            if province in channel_name:
                folder = TVLOGO_DIR / province
                if not folder.exists():
                    folder = find_fuzzy_folder(province)
                if folder and folder.is_dir():
                    for variant in [channel_name, clean_name, f"{clean_name}频道"]:
                        file_path = folder / f"{variant}.png"
                        if file_path.exists():
                            logo_path = f"{BASE_LOGO_URL}/{folder.name}/{variant}.png"
                            return logo_path
    else:
        for folder in TVLOGO_DIR.iterdir():
            if not folder.is_dir():
                continue
            if folder.name in ["中央电视台", "全国卫视"] + PROVINCES:
                continue
            for file in folder.iterdir():
                if not file.is_file():
                    continue
                filename = normalize_name(file.stem)
                if filename in clean_name or clean_name in filename:
                    logo_path = f"{BASE_LOGO_URL}/{folder.name}/{file.name}"
                    return logo_path
    return logo_path

def get_fixed_4k_channels():
    return [
        ("30", "北京卫视4k", "http://192.168.0.109/zgst.php?id=btv4k", "https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/%E5%8C%97%E4%BA%AC%E5%8D%AB%E8%A7%864K.png"),
        ("26", "东方卫视4K", "http://192.168.0.109/zgst.php?id=sh4k", "https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/%E4%B8%9C%E6%96%B9%E5%8D%AB%E8%A7%864K.png"),
        ("29", "江苏卫视4k", "http://192.168.0.109/zgst.php?id=js4k", "https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/%E6%B1%9F%E8%8B%8F%E5%8D%AB%E8%A7%864K.png"),
        ("28", "浙江卫视4k", "http://192.168.0.109/zgst.php?id=zj4k", "https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/%E6%B5%99%E6%B1%9F%E5%8D%AB%E8%A7%864K.png"),
        ("27", "湖南卫视4k", "http://192.168.0.109/zgst.php?id=hn4k", "https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/%E6%B9%96%E5%8D%97%E5%8D%AB%E8%A7%864K.png"),
        ("38", "山东卫视4k", "http://192.168.0.109/zgst.php?id=sd4k", "https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/%E5%B1%B1%E4%B8%9C%E5%8D%AB%E8%A7%864K.png"),
        ("33", "广东卫视4k", "http://192.168.0.109/zgst.php?id=gd4k", "https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/%E5%B9%BF%E4%B8%9C%E5%8D%AB%E8%A7%864K.png"),
        ("56", "四川卫视4k", "http://192.168.0.109/zgst.php?id=sc4k", "https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/%E5%9B%9B%E5%B7%9D%E5%8D%AB%E8%A7%864K.png"),
        ("34", "深圳卫视4k", "http://192.168.0.109/zgst.php?id=sz4k", "https://cdn.jsdelivr.net/gh/qunhui201/TVlogo/img/%E6%B7%B1%E5%9C%B3%E5%8D%AB%E8%A7%864K.png"),
    ]

def append_4k_to_m3u(file_path, k4_channels):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if 'group-title="4K频道"' in content:
        print(f"⚠️ {file_path} 已包含 4K频道，跳过追加。")
        return False
    
    if content and not content.endswith('\n\n'):
        if content.endswith('\n'):
            content += '\n'
        else:
            content += '\n\n'
    
    append_content = ""
    for tvg_id, name, url, logo in k4_channels:
        logo_attr = f' tvg-logo="{logo}"' if logo else ""
        append_content += f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}"{logo_attr} group-title="4K频道",{name}\n'
        append_content += f"{url}\n"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content + append_content)
    
    print(f"✅ 已追加 4K频道 到 {file_path}（强制顶格分离）")
    return True

def append_4k_to_tvbox(file_path, k4_channels):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if '📺4K频道' in content:
        print(f"⚠️ {file_path} 已包含 4K频道，跳过追加。")
        return False
    
    if content and not content.endswith('\n'):
        content += '\n'
    
    append_content = f"📺4K频道,#genre#\n"
    for _, name, url, _ in k4_channels:
        append_content += f"{name},{url}\n"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content + append_content)
    
    print(f"✅ 已追加 4K频道 到 {file_path}（确保顶格换行）")
    return True

def main():
    output_lines = []
    missing_logos = []
    output_lines.append('#EXTM3U x-tvg-url="https://gh.catmak.name/https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/master/output/epg/epg.gz"')
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTINF"):
            info = line
            url = lines[i + 1] if i + 1 < len(lines) else ""
            tvg_name = re.search(r'tvg-name="([^"]+)"', info)
            group_title = re.search(r'group-title="([^"]+)"', info)
            name = tvg_name.group(1) if tvg_name else ""
            group = group_title.group(1) if group_title else ""
            logo = match_logo(name, group)
            if not logo:
                missing_logos.append(f"{group} - {name}")
            output_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{group}",{name}')
            output_lines.append(url)
            i += 2
        else:
            i += 1
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + '\n')  # 强制末尾换行
    with open(MISSING_LOGO_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(missing_logos))
    print(f"✅ 已生成 {OUTPUT_FILE}")
    print(f"📺 共 {sum(1 for l in output_lines if l.startswith('#EXTINF'))} 个频道")
    print(f"⚠️ 未匹配台标的频道已保存至 {MISSING_LOGO_FILE}（共 {len(missing_logos)} 个）")

    k4_channels = get_fixed_4k_channels()
    
    changed1 = append_4k_to_m3u(OUTPUT_FILE, k4_channels)
    changed2 = append_4k_to_m3u(INPUT_FILE, k4_channels)
    
    tvbox_file = "tvbox_output.txt"
    if os.path.exists(tvbox_file):
        changed3 = append_4k_to_tvbox(tvbox_file, k4_channels)
    else:
        changed3 = False
        print(f"⚠️ {tvbox_file} 不存在，跳过 4K 追加。")
    
    if changed1 or changed2 or changed3:
        print("✅ 4K频道 追加导致内容变化，将触发 history 保存。")

if __name__ == "__main__":
    main()

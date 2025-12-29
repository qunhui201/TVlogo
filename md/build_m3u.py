import os
import re
import requests
from pathlib import Path
from collections import defaultdict

# 禁用 SSL 警告（因为我们要忽略过期证书）
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TVLOGO_DIR = Path("TVlogo_Images")
OUTPUT_FILE = "output.m3u"
TVBOX_TXT_FILE = "tvbox_output.txt"
OUTPUT_WITH_LOGO_FILE = "output_with_logo.m3u"
MISSING_LOGOS_FILE = "missing_logos.txt"

# 直接指定的远程 m3u 链接（可随时修改）
REMOTE_M3U_URL = "https://httop.top/hotel.m3u"

# 如果想保存原始下载的文件到本地，可以取消下面一行的注释
SAVE_ORIGINAL_PATH = Path("md/hotel_original.m3u")

PROVINCES = [
    "北京","上海","天津","重庆","辽宁","吉林","黑龙江","江苏","浙江","安徽",
    "福建","江西","山东","河南","湖北","湖南","广东","广西","海南","四川",
    "贵州","云南","陕西","甘肃","青海","宁夏","新疆","内蒙","西藏","香港",
    "澳门","台湾","延边","大湾区"
]

SPECIAL_CHANNELS = {"CCTV17": "央视频道"}

PREFIX_MAP = {
    "BTV": "北京",
    "JSTV": "江苏",
    "GDTV": "广东",
    "HNTV": "湖南",
    "SDTV": "山东",
    "LNTV": "辽宁",
    "HLJTV": "黑龙江",
    "ZJTV": "浙江",
    "CQTV": "重庆",
    "CCTV": "央视频道",
}

def is_content_changed(file_path: Path, new_content: str) -> bool:
    """判断文件内容是否发生变化"""
    if file_path.exists():
        try:
            old_content = file_path.read_text(encoding="utf-8")
            return old_content != new_content
        except Exception:
            return True
    return True

def download_m3u(url: str) -> str:
    """下载 m3u 内容，忽略 SSL 证书错误"""
    try:
        # verify=False 忽略证书验证
        r = requests.get(url, timeout=15, verify=False)
        r.raise_for_status()
        content = r.text
        print(f"✅ 成功下载 {url}")
        return content
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"❌ 下载失败 {url}: {e}")

def save_original_m3u(content: str):
    """可选：保存原始下载的 m3u 文件到本地"""
    if 'SAVE_ORIGINAL_PATH' in globals():
        SAVE_ORIGINAL_PATH.parent.mkdir(parents=True, exist_ok=True)
        SAVE_ORIGINAL_PATH.write_text(content, encoding="utf-8")
        print(f"💾 原始文件已保存到 {SAVE_ORIGINAL_PATH}")

def parse_m3u(content: str):
    lines = content.splitlines()
    result = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            info = lines[i]
            url_line = lines[i + 1] if i + 1 < len(lines) else ""
            tvg_name = re.search(r'tvg-name="([^"]*)"', info)
            group_title = re.search(r'group-title="([^"]*)"', info)
            tvg_logo = re.search(r'tvg-logo="([^"]*)"', info)

            name = tvg_name.group(1) if tvg_name else info.split(",")[-1].strip()
            grp = group_title.group(1) if group_title else ""
            logo = tvg_logo.group(1) if tvg_logo else ""

            result.append((name, url_line.strip(), grp, logo))
            i += 2
        else:
            i += 1
    return result

def classify_channel(name: str, original_group: str, tvlogo_dir: Path) -> str:
    for key, val in SPECIAL_CHANNELS.items():
        if key in name:
            return val
    for prefix, province in PREFIX_MAP.items():
        if name.upper().startswith(prefix):
            return "央视频道" if province == "央视频道" else "地方频道"
    for province in PROVINCES:
        if province in name and "卫视" not in name:
            return "地方频道"
    if "卫视" in name:
        return "卫视频道"

    # 台标文件夹匹配逻辑（保持原样）
    if tvlogo_dir.exists():
        for folder in tvlogo_dir.iterdir():
            if not folder.is_dir() or folder.name in ["央视频道", "卫视频道", "地方频道"]:
                continue
            for logo_file in folder.iterdir():
                if logo_file.is_file():
                    filename = logo_file.stem
                    ch_name = re.sub(r'^[A-Za-z0-9\+\-]+', '', filename)
                    if ch_name and ch_name in name:
                        return folder.name
    return "其他频道"

def generate_tvbox_txt(channels):
    grouped = defaultdict(list)
    for name, url, grp, logo in channels:
        final_group = classify_channel(name, grp, TVLOGO_DIR)
        grouped[final_group].append((name, url))

    lines = []
    for group in grouped:
        lines.append(f"📺{group},#genre#")
        for name, url in grouped[group]:
            lines.append(f"{name},{url}")

    new_content = "\n".join(lines)
    if is_content_changed(Path(TVBOX_TXT_FILE), new_content):
        Path(TVBOX_TXT_FILE).write_text(new_content, encoding="utf-8")
        print(f"✅ 已生成 {TVBOX_TXT_FILE}, 共 {len(channels)} 个频道")
    else:
        print(f"⚠️ {TVBOX_TXT_FILE} 内容无变化，未覆盖")

def generate_output_with_logo(channels):
    out_lines = ["#EXTM3U"]
    missing_logos = []

    for name, url, grp, logo in channels:
        final_group = classify_channel(name, grp, TVLOGO_DIR)
        if not logo:
            missing_logos.append(f"{name}: {url}")
            out_lines.append(f'#EXTINF:-1 tvg-name="{name}" group-title="{final_group}",{name}')
        else:
            out_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{final_group}",{name}')
        out_lines.append(url)

    new_content = "\n".join(out_lines)
    if is_content_changed(Path(OUTPUT_WITH_LOGO_FILE), new_content):
        Path(OUTPUT_WITH_LOGO_FILE).write_text(new_content, encoding="utf-8")
        print(f"✅ 已生成 {OUTPUT_WITH_LOGO_FILE}")
    else:
        print(f"⚠️ {OUTPUT_WITH_LOGO_FILE} 内容无变化，未覆盖")

    if missing_logos:
        Path(MISSING_LOGOS_FILE).write_text("\n".join(missing_logos), encoding="utf-8")
        print(f"⚠️ 未匹配台标的频道已保存至 {MISSING_LOGOS_FILE}（{len(missing_logos)} 个）")

def main():
    # 1. 下载 m3u 内容
    content = download_m3u(REMOTE_M3U_URL)

    # 2. 可选：保存原始文件
    save_original_m3u(content)

    # 3. 解析频道
    channels = parse_m3u(content)
    print(f"📡 解析得到 {len(channels)} 个频道")

    # 4. 生成 output.m3u（带原有 logo）
    out_lines = ["#EXTM3U"]
    for name, url, grp, logo in channels:
        final_group = classify_channel(name, grp, TVLOGO_DIR)
        out_lines.append(f'#EXTINF:-1 tvg-name="{name}" tvg-logo="{logo}" group-title="{final_group}",{name}')
        out_lines.append(url)

    new_output_content = "\n".join(out_lines)
    if is_content_changed(Path(OUTPUT_FILE), new_output_content):
        Path(OUTPUT_FILE).write_text(new_output_content, encoding="utf-8")
        print(f"✅ 已生成 {OUTPUT_FILE}")
    else:
        print(f"⚠️ {OUTPUT_FILE} 内容无变化，未覆盖")

    # 5. 生成其他文件
    generate_output_with_logo(channels)
    generate_tvbox_txt(channels)

if __name__ == "__main__":
    main()

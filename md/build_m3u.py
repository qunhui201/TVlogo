# build_m3u_original.py
import requests

# --------- 配置 ---------
REMOTE_FILES = [
    "http://httop.top/iptvs.m3u",
    "http://httop.top/iptvx.m3u"
]

OUTPUT_FILE = "output_original.m3u"

# --------- 函数 ---------
def download_m3u(url):
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.text

def main():
    all_lines = ["#EXTM3U"]

    for url in REMOTE_FILES:
        try:
            content = download_m3u(url)
            lines = content.splitlines()
            for line in lines:
                # 跳过文件头，只添加 #EXTINF 和 URL
                if line.strip() != "#EXTM3U":
                    all_lines.append(line)
        except Exception as e:
            print(f"下载 {url} 失败: {e}")

    # 写入输出文件
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(all_lines))

    print(f"已生成 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

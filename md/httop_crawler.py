import requests
from bs4 import BeautifulSoup
import os

# 目标网页
URL = "https://httop.top/"

# 保存结果的文件路径（相对 GitHub 仓库根目录的 md 目录）
OUTPUT_PATH = "md/httop_links.txt"

# 确保 md 目录存在
os.makedirs("md", exist_ok=True)

try:
    # 请求网页内容
    response = requests.get(URL, timeout=10)
    response.raise_for_status()

    # 解析 HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # 查找所有节目源链接（iptv*.m3u, e.xml, apk 等）
    results = []
    link_rows = soup.find_all("div", class_="link-row")
    for row in link_rows:
        # 优先 data-copy，否则 data-download
        link = row.get("data-copy") or row.get("data-download")
        if link:
            results.append(link)

    # 保存到 txt 文件
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for link in results:
            f.write(link + "\n")

    print(f"提取成功，共 {len(results)} 条链接。已保存至 {OUTPUT_PATH}")

except Exception as e:
    print(f"抓取失败: {e}")

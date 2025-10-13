import os
import re
import requests

# MD 文件夹路径
md_folder = "md"
# 图片保存路径
output_dir = "img"

os.makedirs(output_dir, exist_ok=True)

# 遍历所有 MD 文件
for md_file in os.listdir(md_folder):
    if not md_file.endswith(".md"):
        continue
    md_path = os.path.join(md_folder, md_file)
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 获取标题作为子文件夹名
    title_match = re.search(r"# 【(.+?)】", content)
    folder_name = title_match.group(1) if title_match else "未知频道"
    folder_path = os.path.join(output_dir, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # 匹配表格中的图片
    pattern = re.compile(r"\|(.+?)\|<img src=\"(.+?)\">")
    matches = pattern.findall(content)

    for name, img_url in matches:
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", name.strip())
        file_path = os.path.join(folder_path, f"{safe_name}.png")

        try:
            resp = requests.get(img_url, timeout=10)
            if resp.status_code == 200:
                with open(file_path, "wb") as img_file:
                    img_file.write(resp.content)
                print(f"下载成功: {safe_name}")
            else:
                print(f"下载失败: {safe_name} {resp.status_code}")
        except Exception as e:
            print(f"下载异常: {safe_name} {e}")

import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor

# ================= 配置区 =================
LOCAL_DIR = "."                     # 仓库根目录
MAX_THREADS = 5
OVERWRITE = False                   # 是否强制覆盖
EXCLUDE_DIRS = {'.git', '.github', 'md'}   # 重点：排除 md 目录（脚本自己就在这里！）
VALID_EXT = {'.txt', '.md', '.json', '.m3u', '.yaml', '.yml', '.csv'}
# ==========================================

def should_skip(path):
    # 排除目录
    if any(exclude in path.split(os.sep) for exclude in EXCLUDE_DIRS):
        return True
    # 只上传指定扩展名
    if not any(path.endswith(ext) for ext in VALID_EXT):
        return True
    return False

def upload_file(key, filepath):
    if not OVERWRITE:
        # 检查是否已存在（用 HEAD 省流量）
        head_url = f"https://api.cloudflare.com/client/v4/accounts/{os.getenv('KV_ACCOUNT_ID')}/storage/kv/namespaces/{os.getenv('KV_NAMESPACE_ID')}/values/{key}"
        try:
            r = requests.head(head_url, headers={"Authorization": f"Bearer {os.getenv('KV_API_TOKEN')}"}, timeout=10)
            if r.status_code == 200:
                print(f"跳过已存在: {key}")
                return
        except:
            pass  # 网络波动也继续上传

    url = head_url.replace("HEAD ", "PUT ")
    try:
        with open(filepath, "rb") as f:
            data = f.read()
        # 可选：加个更新时间注释（只对文本文件）
        if filepath.lower().endswith(('.txt', '.m3u', '.md')):
            timestamp = f"\n# Updated by GitHub Actions at {time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
            data = data + timestamp.encode('utf-8')

        r = requests.put(url, headers={
            "Authorization": f"Bearer {os.getenv('KV_API_TOKEN')}",
            "Content-Type": "text/plain"
        }, data=data, timeout=30)
        r.raise_for_status()
        print(f"上传成功: {key}")
    except Exception as e:
        print(f"上传失败 {key}: {e}")

def main():
    tasks = []
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as pool:
        for root, dirs, files in os.walk(LOCAL_DIR):
            # 动态排除目录
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for f in files:
                filepath = os.path.join(root, f)
                rel_path = os.path.relpath(filepath, LOCAL_DIR)
                key = rel_path.replace("\\", "/")
                
                if should_skip(rel_path):
                    print(f"跳过: {key}")
                    continue
                    
                tasks.append(pool.submit(upload_file, key, filepath))
    
    # 等待完成
    for t in tasks:
        try:
            t.result(timeout=120)
        except Exception as e:
            print(f"任务异常: {e}")

    print("全部完成！")

if __name__ == "__main__":
    main()

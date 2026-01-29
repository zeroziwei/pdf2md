import requests

token = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiI5MDQwMDk0MyIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2ODc2MDExMSwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiYmM4ZGRlZjgtNTZlMC00NGIwLThlYjQtMjVmNzNkYzc5Y2RjIiwiZW1haWwiOiIiLCJleHAiOjE3Njk5Njk3MTF9.HE3Hy5iAbEKILDLJfnmDUEHlLjdk8LGcTit6XRb2lcpSJpMKdvM4sS1wdB2ve0tR6FI7-N6eqV27UFmu2JZTng"

# 步骤1: 申请上传链接
def apply_upload_urls(file_names):
    url = "https://mineru.net/api/v4/file-urls/batch"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "files": [
            {"name": name, "data_id": f"pdf_{i}"}  # data_id 用于标识你的业务数据
            for i, name in enumerate(file_names)
        ],
        "model_version": "vlm"  # 或 "pipeline"
    }
    
    response = requests.post(url, headers=headers, json=data)
    return response.json()

# 步骤2: 上传文件
def upload_files(file_paths, upload_urls):
    for file_path, upload_url in zip(file_paths, upload_urls):
        with open(file_path, 'rb') as f:
            # 注意：使用 PUT 方法，不需要设置 Content-Type
            response = requests.put(upload_url, data=f)
            if response.status_code == 200:
                print(f"✅ {file_path} 上传成功")
            else:
                print(f"❌ {file_path} 上传失败: {response.status_code}")

# 步骤3: 查询解析结果
def get_batch_results(batch_id):
    url = f"https://mineru.net/api/v4/extract-results/batch/{batch_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

import requests
import zipfile
import os

def download_and_extract_results(batch_id, output_dir="output"):
    # 查询结果
    results = get_batch_results(batch_id)
    
    os.makedirs(output_dir, exist_ok=True)
    
    if results["code"] == 0:
        for item in results["data"]["extract_result"]:
            if item["state"] == "done":
                zip_url = item["full_zip_url"]
                file_name = item["file_name"]
                data_id = item["data_id"]
                
                print(f"📥 下载 {file_name} 的解析结果...")
                
                # 下载 ZIP
                zip_response = requests.get(zip_url)
                zip_path = f"{output_dir}/{data_id}.zip"
                
                with open(zip_path, "wb") as f:
                    f.write(zip_response.content)
                
                # 解压
                extract_dir = f"{output_dir}/{data_id}"
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                print(f"✅ {file_name} 解析结果已保存到 {extract_dir}")
                
                # 可选：删除 ZIP 文件
                # os.remove(zip_path)
            else:
                print(f"⚠️ {item['file_name']} 解析失败: {item['err_msg']}")

# 使用
download_and_extract_results("d6b09c10-5047-4c2e-bceb-4e56c04e82f1")


# 使用示例
if __name__ == "__main__":
    # 你的 PDF 文件
    file_paths = [
        "Introduction_to_Linear_Algebra_chapters/01_Table of Contents.pdf",
        # "Introduction_to_Linear_Algebra_chapters/02_1 Introduction to Vectors.pdf",
        # ... 其他文件
    ]
    file_names = [path.split('/')[-1] for path in file_paths]
    
    # 1. 申请上传链接
    result = apply_upload_urls(file_names)
    if result["code"] == 0:
        batch_id = result["data"]["batch_id"]
        upload_urls = result["data"]["file_urls"]
        print(f"📝 batch_id: {batch_id}")
        
        # 2. 上传文件
        upload_files(file_paths, upload_urls)
        
        # 3. 等待一段时间后查询结果（或使用 callback 回调）
        import time
        time.sleep(60)  # 等待解析，实际可能需要更长时间
        results = get_batch_results(batch_id)
        print(results)
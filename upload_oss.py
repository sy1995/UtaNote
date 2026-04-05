#!/usr/bin/env python3
"""
上传 JSON 文件到阿里云 OSS
用法: python3 upload_oss.py
"""

import oss2
import os
from pathlib import Path
from dotenv import load_dotenv


# 加载环境变量
load_dotenv()

# OSS 配置
OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT", "https://oss-cn-hangzhou.aliyuncs.com")
OSS_BUCKET_NAME = os.getenv("OSS_BUCKET_NAME", "utanote-data")

SCRIPT_DIR = Path(__file__).parent


def get_auth():
    """获取 OSS 认证"""
    return oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)


def get_bucket():
    """获取 Bucket 对象"""
    auth = get_auth()
    return oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)


def upload_file(local_path: str, oss_path: str):
    """
    上传单个文件到 OSS
    
    Args:
        local_path: 本地文件路径
        oss_path: OSS 上的路径
    
    Returns:
        str: 文件访问 URL
    """
    bucket = get_bucket()
    
    print(f"⬆️  上传: {local_path} -> {oss_path}")
    
    try:
        # 上传文件
        with open(local_path, 'rb') as f:
            bucket.put_object(oss_path, f)
        
        # 生成访问 URL（公共读）
        url = f"https://{OSS_BUCKET_NAME}.{OSS_ENDPOINT.replace('https://', '')}/{oss_path}"
        print(f"✅ 上传成功")
        print(f"   URL: {url}")
        
        return url
        
    except Exception as e:
        print(f"❌ 上传失败: {str(e)}")
        raise


def upload_all():
    """上传所有 JSON 文件到 OSS"""
    print("="*60)
    print("☁️  上传文件到阿里云 OSS")
    print("="*60)
    print()
    
    # 检查环境变量
    if not all([OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET, OSS_BUCKET_NAME]):
        print("❌ 缺少必要的环境变量")
        print("请设置:")
        print("  - OSS_ACCESS_KEY_ID")
        print("  - OSS_ACCESS_KEY_SECRET")
        print("  - OSS_BUCKET_NAME")
        print("  - OSS_ENDPOINT (可选)")
        return
    
    # 上传 songs.json
    songs_files = list(SCRIPT_DIR.glob("songs_v*.json"))
    if songs_files:
        # 找最新版本
        latest_songs = sorted(songs_files)[-1]
        upload_file(str(latest_songs), "songs.json")
    
    # 上传 config.json
    config_file = SCRIPT_DIR / "config.json"
    if config_file.exists():
        upload_file(str(config_file), "config.json")
    
    # 上传五十音数据
    fiftyon_file = SCRIPT_DIR / "fiftyon_data.json"
    if fiftyon_file.exists():
        upload_file(str(fiftyon_file), "fiftyon_data.json")
    
    print(f"\n{'='*60}")
    print("✅ 上传完成！")
    print(f"{'='*60}")


def main():
    """主函数"""
    upload_all()


if __name__ == "__main__":
    main()

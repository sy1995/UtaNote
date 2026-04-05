#!/usr/bin/env python3
"""
合并新生成的歌曲到 songs.json
用法: python3 merge_songs.py
"""

import json
from pathlib import Path
from datetime import datetime


SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"


def load_existing_songs(songs_file: str = "songs.json"):
    """加载现有的 songs.json"""
    songs_path = SCRIPT_DIR / songs_file
    
    if not songs_path.exists():
        print(f"⚠️  现有文件不存在，将创建新文件")
        return {"version": 1, "songs": []}
    
    with open(songs_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_new_songs(output_dir: Path = OUTPUT_DIR):
    """加载新生成的歌曲 JSON 文件"""
    new_songs = []
    
    for json_file in output_dir.glob("*.json"):
        if json_file.name == "summary.json":
            continue
            
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                song_data = json.load(f)
                new_songs.append(song_data)
        except Exception as e:
            print(f"⚠️  加载失败 {json_file.name}: {str(e)}")
    
    return new_songs


def merge_songs(existing_data: dict, new_songs: list):
    """
    合并歌曲数据（按 ID 去重）
    
    Args:
        existing_data: 现有的 songs.json 数据
        new_songs: 新生成的歌曲列表
    
    Returns:
        dict: 合并后的数据
    """
    existing_songs = {song["id"]: song for song in existing_data.get("songs", [])}
    
    # 添加新歌曲
    added = 0
    updated = 0
    
    for new_song in new_songs:
        song_id = new_song["id"]
        
        if song_id in existing_songs:
            # 更新现有歌曲
            existing_songs[song_id] = new_song
            updated += 1
            print(f"🔄 更新: {new_song['title']}")
        else:
            # 添加新歌曲
            existing_songs[song_id] = new_song
            added += 1
            print(f"➕ 新增: {new_song['title']}")
    
    # 转换为列表
    merged_songs = list(existing_songs.values())
    
    print(f"\n📊 合并结果:")
    print(f"   新增: {added} 首")
    print(f"   更新: {updated} 首")
    print(f"   总计: {len(merged_songs)} 首")
    
    return merged_songs


def save_merged_songs(merged_songs: list, output_file: str = "songs_v1.json"):
    """保存合并后的 songs.json"""
    # 创建输出数据
    output_data = {
        "version": 1,
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
        "total_songs": len(merged_songs),
        "songs": merged_songs
    }
    
    # 保存到文件
    output_path = SCRIPT_DIR / output_file
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 已保存到: {output_path}")
    print(f"   文件大小: {output_path.stat().st_size / 1024:.2f} KB")
    
    return output_path


def update_config(new_version: int, update_note: str):
    """更新 config.json"""
    config = {
        "version": new_version,
        "updated_at": datetime.now().strftime("%Y-%m-%d"),
        "update_note": update_note,
        "total_songs": 0,  # 会在保存 songs.json 后更新
        "recommended_songs": [],
        "min_app_version": "1.0.0"
    }
    
    config_path = SCRIPT_DIR / "config.json"
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"💾 已更新 config.json")


def main():
    """主函数"""
    print("="*60)
    print("🎵 合并歌曲数据")
    print("="*60)
    print()
    
    # 加载现有数据
    print("📂 加载现有数据...")
    existing_data = load_existing_songs()
    print(f"   现有歌曲: {len(existing_data.get('songs', []))} 首")
    
    # 加载新歌曲
    print("\n📂 加载新生成的歌曲...")
    new_songs = load_new_songs()
    print(f"   新歌曲: {len(new_songs)} 首")
    
    if not new_songs:
        print("\n⚠️  没有新歌曲需要合并")
        return
    
    # 合并
    print("\n🔄 开始合并...")
    merged_songs = merge_songs(existing_data, new_songs)
    
    # 保存
    print("\n💾 保存合并结果...")
    output_file = f"songs_v{existing_data.get('version', 1)}.json"
    save_merged_songs(merged_songs, output_file)
    
    # 更新 config
    new_version = existing_data.get("version", 1) + 1
    update_note = f"新增/更新 {len(new_songs)} 首歌曲"
    update_config(new_version, update_note)
    
    print(f"\n{'='*60}")
    print("✅ 合并完成！")
    print(f"{'='*60}")
    print(f"新版本号: {new_version}")
    print(f"输出文件: {output_file}")
    print(f"总歌曲数: {len(merged_songs)} 首")


if __name__ == "__main__":
    main()

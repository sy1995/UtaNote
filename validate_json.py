#!/usr/bin/env python3
"""
校验生成的歌曲 JSON 格式是否符合 schema
用法: python3 validate_json.py <json_file>
"""

import json
import sys
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError


SCRIPT_DIR = Path(__file__).parent
SCHEMA_PATH = SCRIPT_DIR / "prompt_templates" / "schema.json"


def load_schema():
    """加载 JSON Schema"""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_song_json(song_file: str):
    """
    校验歌曲 JSON 文件
    
    Args:
        song_file: JSON 文件路径
    """
    print(f"🔍 校验文件: {song_file}")
    
    # 加载 JSON
    try:
        with open(song_file, 'r', encoding='utf-8') as f:
            song_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式错误: {str(e)}")
        return False
    
    # 加载 Schema
    schema = load_schema()
    
    # 校验
    try:
        validate(instance=song_data, schema=schema)
        print(f"✅ 校验通过！")
        
        # 打印统计信息
        print(f"\n📊 歌曲信息:")
        print(f"   ID: {song_data.get('id')}")
        print(f"   标题: {song_data.get('title')}")
        print(f"   歌手: {song_data.get('artist')}")
        print(f"   动漫: {song_data.get('anime')}")
        print(f"   类型: {song_data.get('type')}")
        print(f"   难度: {song_data.get('difficulty')}")
        print(f"   JLPT范围: {song_data.get('jlpt_range')}")
        print(f"   歌词行数: {len(song_data.get('lines', []))}")
        
        # 词汇统计
        total_words = sum(len(line.get('words', [])) for line in song_data.get('lines', []))
        print(f"   词汇总数: {total_words}")
        
        return True
        
    except ValidationError as e:
        print(f"❌ 校验失败: {e.message}")
        print(f"   路径: {'.'.join(str(p) for p in e.absolute_path)}")
        return False


def validate_all_json_files(output_dir: str = "output"):
    """校验输出目录下的所有 JSON 文件"""
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print(f"❌ 目录不存在: {output_dir}")
        return
    
    json_files = list(output_path.glob("*.json"))
    
    if not json_files:
        print(f"⚠️  没有找到 JSON 文件")
        return
    
    print(f"📁 找到 {len(json_files)} 个 JSON 文件\n")
    
    passed = 0
    failed = 0
    
    for json_file in json_files:
        if validate_song_json(str(json_file)):
            passed += 1
        else:
            failed += 1
        print()
    
    print(f"{'='*60}")
    print(f"📊 校验总结:")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"{'='*60}")


def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 校验单个文件
        validate_song_json(sys.argv[1])
    else:
        # 校验所有文件
        validate_all_json_files("output")


if __name__ == "__main__":
    main()

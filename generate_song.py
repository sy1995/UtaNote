#!/usr/bin/env python3
"""
生成单首歌曲的歌词解析（两阶段流程）
用法: python3 generate_song.py "鬼灭之刃 OP" 或 python3 generate_song.py "红莲华"

流程：
1. 搜索阶段：查找歌曲基本信息和完整歌词（带罗马音和翻译）
2. 解析阶段：拆分词语和语法解释
"""

import json
import os
import sys
from pathlib import Path
from openai import OpenAI

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 配置
client = OpenAI(
    api_key=os.getenv("ALIYUN_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

MODEL = "qwen-plus"
SCRIPT_DIR = Path(__file__).parent
PROMPT_TEMPLATE = SCRIPT_DIR / "prompt_templates" / "song_analysis.txt"

# 关闭思考模式（提高输出稳定性）
EXTRA_BODY = {
    "enable_search": True,      # 启用联网搜索
    "enable_thinking": False,   # 关闭思考模式
    "search_options": {
        "search_strategy": "max"  # 配置搜索策略为高性能模式
    }
}


def load_prompt_template():
    """加载 Prompt 模板"""
    with open(PROMPT_TEMPLATE, 'r', encoding='utf-8') as f:
        return f.read()


def search_song_info(query: str):
    """
    第一阶段：通过大模型联网搜索歌曲基本信息和完整歌词
    
    Args:
        query: 模糊搜索关键词，如 "鬼灭之刃 OP"、"红莲华"
    
    Returns:
        dict: 歌曲信息（包含完整歌词、罗马音、翻译）
    """
    print(f"\n🔍 第一阶段：搜索歌曲信息")
    print(f"   查询: {query}")
    print("-" * 60)
    
    prompt = f"""请根据用户的描述搜索并识别出具体的日本动漫歌曲，返回歌曲的完整信息。

用户描述："{query}"

请严格按照以下 JSON 格式返回（不要添加任何其他文字）：
{{
    "title": "歌曲日文名",
    "title_kana": "歌曲假名读音",
    "title_cn": "歌曲中文名",
    "artist": "歌手/演唱者",
    "anime": "动漫日文名",
    "anime_cn": "动漫中文名",
    "type": "OP/ED/插曲/角色歌/主题曲",
    "year": "年份",
    "lyrics_full": "完整的日文歌词（包含多段，如A段、B段、副歌等，尽量完整）",
    "lyrics_romaji": "完整的罗马音歌词（与日文歌词对应）",
    "lyrics_cn": "完整的中文翻译（与日文歌词对应）",
    "confidence": 0.95
}}

要求：
1. 如果用户给的是模糊描述（如"鬼灭OP"），请识别出具体是哪首歌
2. 歌词必须是真实准确的，尽量获取完整版（多段歌词）
3. 罗马音和中文翻译必须与日文歌词行数对应
4. 如果无法确定某些字段，用合理的推测填充
5. confidence 表示匹配度，0-1之间
6. 只返回 JSON，不要其他文字
"""
    
    try:
        print("⏳ 正在调用大模型联网搜索...")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的日本动漫歌曲识别助手。请根据用户描述准确识别歌曲信息，并获取完整的歌词（日文+罗马音+中文翻译）。请严格按照JSON格式输出。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=32000,  # 增大token以容纳完整歌词
            response_format={"type": "json_object"},
            extra_body=EXTRA_BODY
        )
        print("✅ 搜索完成，正在解析结果...")
        
        content = response.choices[0].message.content
        
        # 提取 JSON
        if content.startswith("```"):
            lines = content.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```json") or line.startswith("```"):
                    in_json = not in_json
                    continue
                if in_json:
                    json_lines.append(line)
            content = "\n".join(json_lines)
        
        song_info = json.loads(content)
        
        # 统计歌词行数
        lyrics_lines = song_info.get('lyrics_full', '').strip().split('\n')
        lyrics_lines = [l for l in lyrics_lines if l.strip()]
        
        print(f"\n✅ 找到歌曲:")
        print(f"   歌名: {song_info.get('title')} ({song_info.get('title_cn', '')})")
        print(f"   歌手: {song_info.get('artist')}")
        print(f"   动漫: {song_info.get('anime')} ({song_info.get('anime_cn', '')})")
        print(f"   类型: {song_info.get('type')}")
        print(f"   年份: {song_info.get('year', '未知')}")
        print(f"   歌词行数: {len(lyrics_lines)}")
        print(f"   匹配度: {song_info.get('confidence', 0):.0%}")
        print("-" * 60)
        
        return song_info
        
    except Exception as e:
        print(f"\n❌ 搜索失败: {str(e)}")
        raise


def parse_single_line(line_idx: int, total_lines: int, original: str, romaji: str, translation: str) -> dict:
    """
    解析单行歌词的词语
    
    Args:
        line_idx: 当前行索引
        total_lines: 总行数
        original: 日文原文
        romaji: 罗马音
        translation: 中文翻译
    
    Returns:
        dict: 解析后的行数据
    """
    prompt = f"""你是一位专业的日语教师。请解析以下歌词行，拆分词汇并标注语法。

第 {line_idx + 1}/{total_lines} 行：
日文原文：{original}
罗马音：{romaji}
中文翻译：{translation}

要求：
1. 将句子拆分成独立的词/助词/语法单位
2. 每个词标注：假名、罗马音、中文释义、词性、JLPT等级
3. 助词要单独解释其语法功能
4. 动词要标注原形和变形说明
5. 如有特殊语法结构，添加 grammar_notes

返回严格的 JSON 格式（只返回这一行的解析，不要其他文字）：
{{
  "original": "{original}",
  "kana": "假名标注",
  "romaji": "{romaji}",
  "translation": "{translation}",
  "words": [
    {{
      "text": "词语",
      "kana": "假名",
      "romaji": "罗马音",
      "meaning": "中文释义",
      "type": "词性",
      "jlpt": "N5/N4/N3/N2/N1",
      "grammar_note": "语法说明（可选）"
    }}
  ],
  "grammar_notes": ["语法注释（可选）"]
}}
"""
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的日语教师，擅长逐词解析日语歌词。请严格按照JSON格式输出。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            max_tokens=4096,
            response_format={"type": "json_object"},
            extra_body={"enable_thinking": False}
        )
        
        content = response.choices[0].message.content
        
        # 提取 JSON
        if content.startswith("```"):
            lines = content.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```json") or line.startswith("```"):
                    in_json = not in_json
                    continue
                if in_json:
                    json_lines.append(line)
            content = "\n".join(json_lines)
        
        return json.loads(content)
        
    except Exception as e:
        print(f"   ⚠️  第 {line_idx + 1} 行解析失败: {str(e)}")
        # 返回基础结构
        return {
            "original": original,
            "kana": original,
            "romaji": romaji,
            "translation": translation,
            "words": [],
            "grammar_notes": []
        }


def generate_song_analysis(title: str, artist: str, anime: str, lyrics_full: str, lyrics_romaji: str, lyrics_cn: str, title_kana: str = "", title_cn: str = "", anime_cn: str = "", song_type: str = "OP", year: str = ""):
    """
    第二阶段：逐行解析歌词词语
    
    Args:
        title: 歌曲标题（日文）
        artist: 歌手
        anime: 动漫名（日文）
        lyrics_full: 日文歌词（完整版）
        lyrics_romaji: 罗马音歌词
        lyrics_cn: 中文翻译
        title_kana: 歌曲标题假名
        title_cn: 歌曲中文名
        anime_cn: 动漫中文名
        song_type: 歌曲类型 (OP/ED/插曲)
        year: 年份
    
    Returns:
        dict: 歌曲解析 JSON
    """
    print(f"\n📝 第二阶段：逐行解析词语")
    print(f"   歌曲: {title} - {artist}")
    print("-" * 60)
    
    # 生成歌曲 ID
    song_id = title.lower().replace(" ", "_").replace("の", "no")
    
    # 解析歌词行
    ja_lines = [l.strip() for l in lyrics_full.strip().split('\n') if l.strip()]
    romaji_lines = [l.strip() for l in lyrics_romaji.strip().split('\n') if l.strip()]
    cn_lines = [l.strip() for l in lyrics_cn.strip().split('\n') if l.strip()]
    
    total_lines = len(ja_lines)
    print(f"🎵 开始逐行解析: {title}")
    print(f"   总行数: {total_lines}")
    print(f"   动漫: {anime}")
    print(f"   类型: {song_type}")
    print("-" * 60)
    
    # 逐行解析
    parsed_lines = []
    for i in range(total_lines):
        ja = ja_lines[i] if i < len(ja_lines) else ""
        roma = romaji_lines[i] if i < len(romaji_lines) else ""
        cn = cn_lines[i] if i < len(cn_lines) else ""
        
        print(f"⏳ 解析第 {i + 1}/{total_lines} 行: {ja[:30]}...")
        
        line_data = parse_single_line(i, total_lines, ja, roma, cn)
        parsed_lines.append(line_data)
        
        # 显示进度
        if (i + 1) % 5 == 0 or i == total_lines - 1:
            print(f"   ✅ 已完成 {i + 1}/{total_lines} 行")
    
    print("\n✅ 所有行解析完成，正在生成最终数据...")
    
    # 构建完整数据
    song_data = {
        "id": song_id,
        "title": title,
        "title_kana": title_kana,
        "title_cn": title_cn,
        "artist": artist,
        "anime": anime,
        "anime_cn": anime_cn,
        "type": song_type,
        "difficulty": "初级",
        "jlpt_range": "N5-N3",
        "lines": parsed_lines
    }
    
    # 调用大模型生成标签
    if "tags" not in song_data or not song_data["tags"]:
        print("🏷️  正在生成智能标签...")
        tags_prompt = f"""请为以下日本动漫歌曲生成用于搜索检索的标签。

歌曲信息：
- 歌曲名：{title} ({title_cn})
- 歌手：{artist}
- 动漫：{anime} ({anime_cn})
- 类型：{song_type}
- 年份：{year}
- 难度：{song_data.get('difficulty', '未知')}
- JLPT范围：{song_data.get('jlpt_range', '未知')}

请生成 8-15 个标签，包括：
1. 歌曲相关：日文名、中文名、罗马音/假名
2. 歌手相关：歌手名、组合名
3. 动漫相关：动漫名（中日文）、动漫缩写
4. 类型相关：OP/ED/插曲、年代、季度
5. 特征相关：风格（热血/抒情/摇滚等）、难度级别

返回 JSON 格式（只返回数组，不要其他文字）：
["标签1", "标签2", "标签3", ...]
"""
        
        try:
            tags_response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个标签生成助手。请根据歌曲信息生成用于检索的标签数组。只返回JSON数组。"
                    },
                    {
                        "role": "user",
                        "content": tags_prompt
                    }
                ],
                temperature=0.5,
                max_tokens=512,
                response_format={"type": "json_object"}
            )
            
            tags_content = tags_response.choices[0].message.content
            
            # 提取 JSON 数组
            if tags_content.startswith("```"):
                lines = tags_content.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.startswith("```json") or line.startswith("```"):
                        in_json = not in_json
                        continue
                    if in_json:
                        json_lines.append(line)
                tags_content = "\n".join(json_lines)
            
            # 如果是对象格式，提取 tags 字段
            tags_json = json.loads(tags_content)
            if isinstance(tags_json, dict) and "tags" in tags_json:
                song_data["tags"] = tags_json["tags"]
            elif isinstance(tags_json, list):
                song_data["tags"] = tags_json
            else:
                raise ValueError("标签格式错误")
            
            print(f"✅ 生成了 {len(song_data['tags'])} 个标签")
            
        except Exception as tag_error:
            print(f"⚠️  标签生成失败，使用默认标签: {str(tag_error)}")
            # 回退到默认标签生成
            tags = []
            if title:
                tags.append(title)
            if title_cn:
                tags.append(title_cn)
            if title_kana:
                tags.append(title_kana)
            if artist:
                tags.append(artist)
            if anime:
                tags.append(anime)
            if anime_cn:
                tags.append(anime_cn)
            if song_type:
                tags.append(song_type)
            if year:
                tags.append(year)
            song_data["tags"] = tags
    
    print(f"✅ 生成成功！")
    return song_data


def save_song_json(song_data: dict, output_dir: str = "output"):
    """保存歌曲 JSON 到文件"""
    print(f"\n💾 正在保存 JSON 文件...")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    file_path = output_path / f"{song_data['id']}.json"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(song_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已保存到: {file_path}")
    return file_path


def preview_lyrics(lyrics_full: str, lyrics_romaji: str, lyrics_cn: str):
    """预览歌词内容，供用户确认"""
    ja_lines = [l.strip() for l in lyrics_full.strip().split('\n') if l.strip()]
    roma_lines = [l.strip() for l in lyrics_romaji.strip().split('\n') if l.strip()]
    cn_lines = [l.strip() for l in lyrics_cn.strip().split('\n') if l.strip()]
    
    print("\n" + "="*60)
    print("📖 歌词预览（前10行）")
    print("="*60)
    
    preview_count = min(10, len(ja_lines))
    for i in range(preview_count):
        ja = ja_lines[i] if i < len(ja_lines) else ""
        roma = roma_lines[i] if i < len(roma_lines) else ""
        cn = cn_lines[i] if i < len(cn_lines) else ""
        
        print(f"\n第 {i+1} 行:")
        print(f"  日文: {ja}")
        print(f"  罗马: {roma}")
        print(f"  中文: {cn}")
    
    if len(ja_lines) > 10:
        print(f"\n... 还有 {len(ja_lines) - 10} 行 ...")
    
    print("\n" + "="*60)
    print(f"总行数: {len(ja_lines)}")
    print("="*60)


def confirm_lyrics() -> bool:
    """询问用户是否确认歌词"""
    while True:
        choice = input("\n🤔 歌词是否正确？确认后将继续解析词语 [y/n]: ").strip().lower()
        if choice in ['y', 'yes', '是', '确认', '1']:
            return True
        elif choice in ['n', 'no', '否', '取消', '0']:
            return False
        else:
            print("请输入 y 或 n")


def main():
    """主函数 - 三步流程：搜索 -> 确认 -> 解析"""
    print("="*60)
    print("🎵 UtaNote 歌曲生成工具")
    print("="*60)
    print("\n流程说明:")
    print("  1️⃣  搜索歌曲信息和歌词")
    print("  2️⃣  预览并确认歌词内容")
    print("  3️⃣  逐行解析词语和语法")
    print("="*60)
    
    # 从命令行获取查询
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        # 交互式输入
        query = input("\n请输入歌曲信息（如：鬼灭之刃 OP / 红莲华）: ").strip()
    
    if not query:
        print("❌ 请输入搜索关键词")
        return
    
    try:
        # ========== 步骤 1：搜索歌曲信息 ==========
        print("\n" + "="*60)
        print("📝 步骤 1/3: 搜索歌曲信息")
        print("="*60)
        
        song_info = search_song_info(query)
        
        # 检查是否获取到完整歌词信息
        lyrics_full = song_info.get("lyrics_full", "")
        lyrics_romaji = song_info.get("lyrics_romaji", "")
        lyrics_cn = song_info.get("lyrics_cn", "")
        
        if not lyrics_full or not lyrics_romaji or not lyrics_cn:
            print("⚠️  警告：未获取到完整的歌词信息（日文/罗马音/中文）")
            print("   将尝试使用旧版格式继续...")
            lyrics_full = song_info.get("lyrics", "")
            lyrics_romaji = ""
            lyrics_cn = ""
        
        # ========== 步骤 2：预览并确认歌词 ==========
        print("\n" + "="*60)
        print("📝 步骤 2/3: 预览歌词内容")
        print("="*60)
        
        preview_lyrics(lyrics_full, lyrics_romaji, lyrics_cn)
        
        if not confirm_lyrics():
            print("\n❌ 已取消，请重新搜索")
            return
        
        # ========== 步骤 3：生成词语解析 ==========
        print("\n" + "="*60)
        print("📝 步骤 3/3: 解析词语和语法")
        print("="*60)
        
        song_data = generate_song_analysis(
            title=song_info["title"],
            artist=song_info["artist"],
            anime=song_info["anime"],
            lyrics_full=lyrics_full,
            lyrics_romaji=lyrics_romaji,
            lyrics_cn=lyrics_cn,
            title_kana=song_info.get("title_kana", ""),
            title_cn=song_info.get("title_cn", ""),
            anime_cn=song_info.get("anime_cn", ""),
            song_type=song_info.get("type", "OP"),
            year=song_info.get("year", "")
        )
        
        # 保存结果
        print("\n" + "="*60)
        save_song_json(song_data)
        
        # 打印统计
        print(f"\n📊 统计信息:")
        print(f"   歌词行数: {len(song_data['lines'])}")
        print(f"   词汇总数: {sum(len(line['words']) for line in song_data['lines'])}")
        print(f"   难度: {song_data['difficulty']}")
        print(f"   JLPT范围: {song_data['jlpt_range']}")
        print(f"   标签: {', '.join(song_data.get('tags', []))}")
        print("="*60)
        print("✅ 全部完成！\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 生成失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

from deep_translator import GoogleTranslator
import time
import logging
from multiprocessing import Pool, cpu_count
from typing import List, Tuple, Dict
import math
import re

class SubtitleBlock:
    def __init__(self, index: int, timestamp: str, content: List[str]):
        self.index = index
        self.timestamp = timestamp
        self.content = content
    
    def __str__(self) -> str:
        return f"{self.index}\n{self.timestamp}\n{''.join(self.content)}\n"

def parse_srt(file_content: List[str]) -> List[SubtitleBlock]:
    """解析SRT文件内容为字幕块列表"""
    blocks = []
    current_block = None
    current_content = []
    
    for line in file_content:
        line = line.strip()
        
        # 如果是序号(纯数字)
        if re.match(r'^\d+$', line):
            if current_block:
                current_block.content = current_content
                blocks.append(current_block)
            current_block = SubtitleBlock(int(line), "", [])
            current_content = []
            
        # 如果是时间戳
        elif '-->' in line:
            if current_block:
                current_block.timestamp = line
                
        # 如果是内容或空行
        else:
            if current_block:
                current_content.append(line + '\n')
    
    # 添加最后一个块
    if current_block:
        current_block.content = current_content
        blocks.append(current_block)
    
    return blocks

def translate_block(args: Tuple) -> Tuple[int, SubtitleBlock]:
    """翻译单个字幕块"""
    block, src_lang, dest_lang, retries, delay = args
    translator = GoogleTranslator(source=src_lang, target=dest_lang)
    
    # 合并多行内容进行翻译
    content = ' '.join(line.strip() for line in block.content if line.strip())
    
    for attempt in range(retries):
        try:
            if content:  # 只翻译非空内容
                translated_content = translator.translate(content)
                block.content = [translated_content + '\n']
            break
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
    
    return block.index, block

def parallel_translate_srt(
    input_path: str,
    output_path: str,
    src_lang: str = 'en',
    dest_lang: str = 'zh-CN',
    retries: int = 3,
    delay: int = 5,
    num_processes: int = None
) -> None:
    """并行处理的SRT字幕翻译函数"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # 语言代码映射
    LANGUAGE_CODES = {
        'zh': 'zh-CN',
        'cn': 'zh-CN',
        'chinese': 'zh-CN',
        'traditional': 'zh-TW',
        'simplified': 'zh-CN'
    }
    
    dest_lang = LANGUAGE_CODES.get(dest_lang.lower(), dest_lang)
    src_lang = LANGUAGE_CODES.get(src_lang.lower(), src_lang)
    
    if num_processes is None:
        num_processes = cpu_count()
    
    logger.info(f"使用 {num_processes} 个进程进行翻译")
    
    # 读取并解析SRT文件
    with open(input_path, 'r', encoding='utf-8') as infile:
        content = infile.readlines()
    
    subtitle_blocks = parse_srt(content)
    total_blocks = len(subtitle_blocks)
    logger.info(f"共发现 {total_blocks} 个字幕块")
    
    # 准备翻译任务
    translation_tasks = [
        (block, src_lang, dest_lang, retries, delay)
        for block in subtitle_blocks
    ]
    
    # 并行翻译
    translated_blocks: Dict[int, SubtitleBlock] = {}
    with Pool(processes=num_processes) as pool:
        for i, (index, block) in enumerate(pool.imap_unordered(translate_block, translation_tasks)):
            translated_blocks[index] = block
            if (i + 1) % 100 == 0:
                logger.info(f"已完成 {i+1}/{total_blocks} 个字幕块")
    
    # 按原始顺序写入结果
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for i in range(1, max(translated_blocks.keys()) + 1):
            if i in translated_blocks:
                outfile.write(str(translated_blocks[i]))
    
    logger.info(f"翻译完成。共处理 {total_blocks} 个字幕块")

if __name__ == "__main__":
    input_file = '（米歇尔·福柯法兰西学院课程）11、治理自我与治理他者（1982-1983）——哥伦比亚当代批判思想中心研讨会.srt'
    output_file = 'translated_subtitles.srt'
    try:
        parallel_translate_srt(
            input_path=input_file,
            output_path=output_file,
            src_lang="en",
            dest_lang="zh-CN"
        )
    except Exception as e:
        logging.error(f"翻译失败: {e}")

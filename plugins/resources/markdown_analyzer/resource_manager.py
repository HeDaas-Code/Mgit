#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Markdown分析器插件资源管理模块
提供统一的资源访问接口
"""

import os
import sys
import platform
from typing import List, Set, Optional

class ResourceManager:
    """资源管理器类"""
    
    def __init__(self):
        """初始化资源管理器"""
        # 获取资源目录路径
        self.resources_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 资源子目录
        self.fonts_dir = os.path.join(self.resources_dir, 'fonts')
        self.stopwords_dir = os.path.join(self.resources_dir, 'stopwords')
        
        # 创建目录（如果不存在）
        os.makedirs(self.fonts_dir, exist_ok=True)
        os.makedirs(self.stopwords_dir, exist_ok=True)
    
    def get_resource_path(self, relative_path: str) -> str:
        """
        获取资源文件的绝对路径
        
        Args:
            relative_path: 相对于资源目录的路径
            
        Returns:
            str: 资源文件的绝对路径
        """
        return os.path.join(self.resources_dir, relative_path)
    
    def get_chinese_stopwords(self) -> Set[str]:
        """
        获取中文停用词列表
        
        Returns:
            Set[str]: 中文停用词集合
        """
        stopwords = set()
        stopwords_file = os.path.join(self.stopwords_dir, 'cn_stopwords.txt')
        
        if os.path.exists(stopwords_file):
            try:
                with open(stopwords_file, 'r', encoding='utf-8') as f:
                    stopwords = set([line.strip() for line in f if line.strip()])
            except Exception as e:
                print(f"读取中文停用词文件失败: {str(e)}")
        
        return stopwords
    
    def get_english_stopwords(self) -> Set[str]:
        """
        获取英文停用词列表
        
        Returns:
            Set[str]: 英文停用词集合
        """
        stopwords = set()
        stopwords_file = os.path.join(self.stopwords_dir, 'en_stopwords.txt')
        
        if os.path.exists(stopwords_file):
            try:
                with open(stopwords_file, 'r', encoding='utf-8') as f:
                    stopwords = set([line.strip() for line in f if line.strip()])
            except Exception as e:
                print(f"读取英文停用词文件失败: {str(e)}")
        
        return stopwords
    
    def get_available_fonts(self) -> List[str]:
        """
        获取可用字体文件列表
        
        Returns:
            List[str]: 字体文件路径列表
        """
        fonts = []
        if os.path.exists(self.fonts_dir):
            for file in os.listdir(self.fonts_dir):
                if file.lower().endswith(('.ttf', '.otf', '.ttc')):
                    fonts.append(os.path.join(self.fonts_dir, file))
        
        return fonts
    
    def get_system_font(self) -> Optional[str]:
        """
        获取系统中可用的中文字体
        
        Returns:
            Optional[str]: 字体文件路径，如果找不到则返回None
        """
        # 先检查用户自定义字体
        custom_fonts = self.get_available_fonts()
        if custom_fonts:
            return custom_fonts[0]  # 返回第一个可用字体
        
        # 如果没有自定义字体，检查系统字体
        system = platform.system()
        if system == 'Windows':
            # Windows常见中文字体
            potential_fonts = [
                os.path.join(os.environ['WINDIR'], 'Fonts', 'simhei.ttf'),   # 黑体
                os.path.join(os.environ['WINDIR'], 'Fonts', 'simsun.ttc'),   # 宋体
                os.path.join(os.environ['WINDIR'], 'Fonts', 'msyh.ttc'),     # 微软雅黑
                os.path.join(os.environ['WINDIR'], 'Fonts', 'simkai.ttf'),   # 楷体
                os.path.join(os.environ['WINDIR'], 'Fonts', 'simfang.ttf'),  # 仿宋
                os.path.join(os.environ['WINDIR'], 'Fonts', 'STKAITI.TTF'),  # 华文楷体
            ]
        elif system == 'Darwin':  # macOS
            # macOS常见中文字体
            potential_fonts = [
                '/System/Library/Fonts/PingFang.ttc',              # 苹方
                '/Library/Fonts/Microsoft/STHeiti Light.ttc',      # 华文黑体
                '/Library/Fonts/Microsoft/STHeiti Medium.ttc',     # 华文黑体
                '/Library/Fonts/Microsoft/STSong.ttc',             # 华文宋体
                '/Library/Fonts/Microsoft/STFangsong.ttc',         # 华文仿宋
                '/Library/Fonts/Microsoft/STKaiti.ttc',            # 华文楷体
            ]
        else:  # Linux/其他
            # Linux常见中文字体
            potential_fonts = [
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',    # Droid字体
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',               # 文泉驿微米黑
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',                 # 文泉驿正黑
                '/usr/share/fonts/truetype/arphic/uming.ttc',                   # AR PL UMing
                '/usr/share/fonts/truetype/arphic/ukai.ttc',                    # AR PL UKai
                '/usr/share/fonts/OpenType/noto/NotoSansCJK-Regular.ttc',       # Noto Sans CJK
            ]
        
        # 检查字体是否存在
        for font in potential_fonts:
            if os.path.exists(font):
                return font
        
        return None

# 全局资源管理器实例
resource_manager = ResourceManager()

def get_resource_manager() -> ResourceManager:
    """
    获取资源管理器实例
    
    Returns:
        ResourceManager: 资源管理器实例
    """
    global resource_manager
    return resource_manager 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import base64
import hmac
import struct
import hashlib
import random
import qrcode
import threading
import requests
import ntplib
import string
from io import BytesIO
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QObject, pyqtSignal
from src.utils.logger import info, warning, error, debug

class TwoFactorAuth(QObject):
    """
    两因素认证工具类
    实现基于TOTP (Time-based One-Time Password) 的两因素认证
    
    支持:
    - 生成密钥
    - 创建二维码
    - 验证TOTP代码
    - 时间同步
    - 生成恢复码
    """
    
    # 定义信号
    qrCodeGenerated = pyqtSignal(QPixmap)  # 二维码生成完成信号
    timeOffsetChanged = pyqtSignal(int)    # 时间偏移更新信号
    
    def __init__(self, issuer="MGit"):
        """
        初始化两因素认证实例
        
        Args:
            issuer: 发行者名称，将显示在认证App中
        """
        super().__init__()
        self.issuer = issuer
        self.digit_count = 6  # TOTP代码位数
        self.interval = 30    # TOTP刷新间隔（秒）
        self.time_offset = 0  # 本地时间与标准时间的偏移量（秒）
        
        # 开始时间同步
        self._sync_time_async()
        
    def generate_secret_key(self, length=20):
        """
        生成随机密钥
        
        Args:
            length: 密钥长度，默认20字节
            
        Returns:
            str: Base32编码的密钥
        """
        # 生成随机字节
        random_bytes = os.urandom(length)
        
        # 转换为Base32编码（认证器常用格式）
        # 使用标准库实现Base32编码
        encoded = base64.b32encode(random_bytes).decode('utf-8')
        
        return encoded
        
    def get_totp_token(self, secret_key, counter=None):
        """
        计算TOTP密码
        
        Args:
            secret_key: Base32编码的密钥
            counter: 计数器值，默认为当前时间戳除以时间间隔
            
        Returns:
            str: 6位TOTP代码
        """
        # 如果未提供counter，使用当前时间（考虑时间偏移）
        if counter is None:
            counter = int((time.time() + self.time_offset) // self.interval)
            
        # 将counter转换为字节
        counter_bytes = struct.pack(">Q", counter)
        
        # 解码密钥（处理填充问题）
        try:
            # 确保密钥格式正确（处理可能的填充）
            if len(secret_key) % 8 != 0:
                secret_key += '=' * (8 - len(secret_key) % 8)
            
            # 移除空格和其他无关字符
            secret_key = ''.join(c for c in secret_key if c.isalnum() or c == '=')
            secret_key = base64.b32decode(secret_key.upper())
        except Exception as e:
            error(f"解码密钥失败: {str(e)}")
            return None
            
        # 计算HMAC-SHA1
        hmac_hash = hmac.new(secret_key, counter_bytes, hashlib.sha1).digest()
        
        # 动态截断
        offset = hmac_hash[-1] & 0x0F
        truncated_hash = ((hmac_hash[offset] & 0x7F) << 24 |
                         (hmac_hash[offset + 1] & 0xFF) << 16 |
                         (hmac_hash[offset + 2] & 0xFF) << 8 |
                         (hmac_hash[offset + 3] & 0xFF))
                         
        # 提取指定位数的代码
        token = truncated_hash % (10 ** self.digit_count)
        
        # 格式化为固定位数的字符串
        return f"{token:0{self.digit_count}d}"
        
    def verify_totp(self, secret_key, token, valid_window=1):
        """
        验证TOTP代码
        
        Args:
            secret_key: Base32编码的密钥
            token: 用户输入的TOTP代码
            valid_window: 验证窗口，默认为前后1个间隔
            
        Returns:
            bool: 验证是否成功
        """
        if not token or not secret_key:
            return False
            
        # 尝试将token转换为整数
        try:
            token = int(token)
        except ValueError:
            return False
            
        # 当前的counter（考虑时间偏移）
        current_counter = int((time.time() + self.time_offset) // self.interval)
        
        # 在给定窗口内检查前后的token（增加窗口大小提高成功率）
        for i in range(-valid_window, valid_window + 1):
            counter = current_counter + i
            expected_token = self.get_totp_token(secret_key, counter)
            
            try:
                expected_token = int(expected_token)
                if token == expected_token:
                    return True
            except ValueError:
                continue
                
        return False
        
    def get_remaining_seconds(self):
        """
        获取当前TOTP代码的剩余有效秒数
        
        Returns:
            int: 剩余秒数
        """
        # 考虑时间偏移，计算更准确的剩余时间
        adjusted_time = time.time() + self.time_offset
        remaining = self.interval - (adjusted_time % self.interval)
        return int(remaining)
        
    def get_current_counter(self):
        """
        获取当前TOTP计数器值
        
        Returns:
            int: 当前计数器值
        """
        return int((time.time() + self.time_offset) // self.interval)
        
    def get_otp_auth_url(self, username, secret_key):
        """
        生成OTP认证URL，用于二维码
        
        Args:
            username: 用户名
            secret_key: Base32编码的密钥
            
        Returns:
            str: OTP认证URL
        """
        return f"otpauth://totp/{self.issuer}:{username}?secret={secret_key}&issuer={self.issuer}&algorithm=SHA1&digits={self.digit_count}&period={self.interval}"
        
    def generate_qrcode(self, username, secret_key):
        """
        生成包含OTP认证URL的二维码
        
        Args:
            username: 用户名
            secret_key: Base32编码的密钥
            
        Returns:
            QPixmap: 二维码图像
        """
        try:
            # 生成认证URL
            auth_url = self.get_otp_auth_url(username, secret_key)
            
            # 创建二维码
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4
            )
            
            qr.add_data(auth_url)
            qr.make(fit=True)
            
            # 生成图像
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 转换为QPixmap
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            
            pixmap = QPixmap()
            pixmap.loadFromData(buffer.read())
            
            # 发出信号
            self.qrCodeGenerated.emit(pixmap)
            
            return pixmap
        except Exception as e:
            error(f"生成二维码失败: {str(e)}")
            return None
            
    def _sync_time_async(self):
        """
        异步同步时间，通过多种方式尝试获取精确时间
        """
        threading.Thread(target=self._sync_time, daemon=True).start()
        
    def _sync_time(self):
        """
        同步时间，尝试多种方式获取精确时间
        """
        try:
            # 首先尝试使用NTP服务器
            ntp_servers = [
                'pool.ntp.org',
                'time.windows.com',
                'time.google.com',
                'time.cloudflare.com'
            ]
            
            for server in ntp_servers:
                try:
                    client = ntplib.NTPClient()
                    response = client.request(server, timeout=2)
                    self.time_offset = response.offset
                    info(f"使用NTP服务器 {server} 同步时间，偏移量: {self.time_offset:.2f}秒")
                    self.timeOffsetChanged.emit(int(self.time_offset))
                    return
                except Exception as e:
                    debug(f"NTP服务器 {server} 同步失败: {str(e)}")
                    continue
            
            # 如果NTP失败，尝试使用HTTP服务
            try:
                response = requests.get('https://worldtimeapi.org/api/ip', timeout=2)
                if response.status_code == 200:
                    server_time = response.json().get('unixtime')
                    if server_time:
                        self.time_offset = server_time - time.time()
                        info(f"使用HTTP时间API同步时间，偏移量: {self.time_offset:.2f}秒")
                        self.timeOffsetChanged.emit(int(self.time_offset))
                        return
            except Exception as e:
                debug(f"HTTP时间API同步失败: {str(e)}")
                
            # 都失败了，使用0偏移
            self.time_offset = 0
            info("时间同步失败，使用本地时间")
            
        except Exception as e:
            error(f"时间同步过程中发生错误: {str(e)}")
            self.time_offset = 0 
        
    def generate_recovery_codes(self, count=8, code_length=10):
        """
        生成用于恢复的一次性备份码
        
        Args:
            count: 生成的备份码数量
            code_length: 每个备份码的长度
            
        Returns:
            list: 备份码列表
        """
        codes = []
        # 使用字母和数字，排除容易混淆的字符
        chars = ''.join(c for c in string.ascii_uppercase + string.digits 
                       if c not in 'IL0O1')  # 排除容易混淆的字符
        
        for _ in range(count):
            # 生成随机码
            code = ''.join(random.choice(chars) for _ in range(code_length))
            
            # 每4个字符添加一个连字符，提高可读性
            formatted_code = '-'.join(code[i:i+4] for i in range(0, len(code), 4))
            codes.append(formatted_code)
            
        return codes
        
    def hash_recovery_code(self, code):
        """
        对恢复码进行哈希，用于安全存储
        
        Args:
            code: 恢复码
            
        Returns:
            str: 哈希后的恢复码
        """
        # 移除所有非字母数字字符（如连字符）
        code = ''.join(c for c in code if c.isalnum())
        code = code.upper()  # 转为大写
        
        # 使用SHA-256哈希
        hashed = hashlib.sha256(code.encode()).hexdigest()
        return hashed
        
    def verify_recovery_code(self, input_code, hashed_codes):
        """
        验证恢复码是否有效
        
        Args:
            input_code: 用户输入的恢复码
            hashed_codes: 哈希后的恢复码列表
            
        Returns:
            bool: 验证是否成功
            str: 使用的恢复码的哈希（如果成功）
        """
        # 移除所有非字母数字字符（如连字符）
        input_code = ''.join(c for c in input_code if c.isalnum())
        input_code = input_code.upper()  # 转为大写
        
        # 计算输入码的哈希
        input_hash = hashlib.sha256(input_code.encode()).hexdigest()
        
        # 检查是否匹配任何存储的哈希值
        if input_hash in hashed_codes:
            return True, input_hash
            
        return False, None 
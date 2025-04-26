#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import socket
import datetime
import OpenSSL
from pathlib import Path
from src.utils.logger import info, warning, error, debug

class SSLHelper:
    """
    SSL辅助工具类，用于生成和管理自签名SSL证书
    主要用于OAuth认证过程中的本地回调服务器
    """
    
    def __init__(self, config_dir=None):
        """
        初始化SSL辅助工具
        
        Args:
            config_dir: 配置目录，默认为用户目录下的.mgit
        """
        # 设置配置目录
        if config_dir is None:
            home_dir = str(Path.home())
            self.config_dir = os.path.join(home_dir, '.mgit')
        else:
            self.config_dir = config_dir
            
        # 证书和密钥路径
        self.cert_dir = os.path.join(self.config_dir, 'certs')
        self.cert_file = os.path.join(self.cert_dir, 'server.crt')
        self.key_file = os.path.join(self.cert_dir, 'server.key')
        
        # 确保证书目录存在
        if not os.path.exists(self.cert_dir):
            os.makedirs(self.cert_dir)
            
    def check_cert(self):
        """
        检查证书是否存在并有效
        
        Returns:
            bool: 证书是否有效
        """
        if not os.path.exists(self.cert_file) or not os.path.exists(self.key_file):
            debug("SSL证书或密钥文件不存在")
            return False
            
        try:
            # 读取证书
            with open(self.cert_file, 'rb') as f:
                cert_data = f.read()
                
            # 解析证书
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
            
            # 检查有效期
            not_after = cert.get_notAfter().decode('ascii')
            not_after_date = datetime.datetime.strptime(not_after, '%Y%m%d%H%M%SZ')
            
            # 如果证书将在30天内过期，视为无效
            if (not_after_date - datetime.datetime.now()).days < 30:
                debug("SSL证书即将过期")
                return False
                
            return True
        except Exception as e:
            error(f"检查SSL证书时出错: {str(e)}")
            return False
            
    def generate_cert(self, host='localhost'):
        """
        生成自签名SSL证书
        
        Args:
            host: 主机名，默认为localhost
            
        Returns:
            tuple: (证书文件路径, 密钥文件路径)
        """
        try:
            debug(f"为主机 {host} 生成自签名SSL证书")
            
            # 创建密钥对
            key = OpenSSL.crypto.PKey()
            key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
            
            # 创建证书请求
            req = OpenSSL.crypto.X509Req()
            req.get_subject().CN = host
            req.set_pubkey(key)
            req.sign(key, 'sha256')
            
            # 创建证书
            cert = OpenSSL.crypto.X509()
            cert.set_serial_number(1)
            cert.gmtime_adj_notBefore(0)
            # 设置证书有效期为1年
            cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)
            cert.set_issuer(req.get_subject())
            cert.set_subject(req.get_subject())
            cert.set_pubkey(req.get_pubkey())
            
            # 添加使用者替代名称扩展
            san_extension = OpenSSL.crypto.X509Extension(
                b'subjectAltName',
                False,
                f'DNS:{host}, IP:127.0.0.1'.encode()
            )
            cert.add_extensions([san_extension])
            
            # 设置基本限制
            basic_constraints = OpenSSL.crypto.X509Extension(
                b'basicConstraints',
                True,
                b'CA:FALSE'
            )
            cert.add_extensions([basic_constraints])
            
            # 设置密钥用途
            key_usage = OpenSSL.crypto.X509Extension(
                b'keyUsage',
                True,
                b'digitalSignature, keyEncipherment'
            )
            cert.add_extensions([key_usage])
            
            # 设置扩展密钥用途
            ext_key_usage = OpenSSL.crypto.X509Extension(
                b'extendedKeyUsage',
                False,
                b'serverAuth, clientAuth'
            )
            cert.add_extensions([ext_key_usage])
            
            # 自签名证书
            cert.sign(key, 'sha256')
            
            # 导出证书和密钥
            cert_data = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
            key_data = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
            
            # 保存证书和密钥
            with open(self.cert_file, 'wb') as f:
                f.write(cert_data)
                
            with open(self.key_file, 'wb') as f:
                f.write(key_data)
                
            info(f"成功生成自签名SSL证书，保存在: {self.cert_dir}")
            return self.cert_file, self.key_file
        except Exception as e:
            error(f"生成SSL证书时出错: {str(e)}")
            return None, None
            
    def ensure_valid_cert(self, host='localhost'):
        """
        确保有有效的SSL证书，如果没有则生成
        
        Args:
            host: 主机名，默认为localhost
            
        Returns:
            tuple: (证书文件路径, 密钥文件路径)
        """
        if not self.check_cert():
            return self.generate_cert(host)
        return self.cert_file, self.key_file
        
    def get_cert_paths(self):
        """
        获取证书和密钥文件路径
        
        Returns:
            tuple: (证书文件路径, 密钥文件路径)
        """
        return self.cert_file, self.key_file
        
    def get_cert_fingerprint(self):
        """
        获取证书指纹，用于验证
        
        Returns:
            str: 证书SHA-1指纹
        """
        try:
            if not os.path.exists(self.cert_file):
                return None
                
            # 读取证书
            with open(self.cert_file, 'rb') as f:
                cert_data = f.read()
                
            # 解析证书
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert_data)
            
            # 计算指纹
            fingerprint = cert.digest('sha1').decode('ascii')
            return fingerprint
        except Exception as e:
            error(f"获取证书指纹时出错: {str(e)}")
            return None 
#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
显示PyQt-Fluent-Widgets中所有可用的FluentIcon
"""

from qfluentwidgets import FluentIcon

if __name__ == "__main__":
    icons = [attr for attr in dir(FluentIcon) if not attr.startswith('_')]
    print("可用的FluentIcon:")
    for icon in sorted(icons):
        print(f"- {icon}") 
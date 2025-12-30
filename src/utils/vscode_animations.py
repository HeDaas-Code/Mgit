#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
VSCode风格动画工具
提供平滑的UI动画效果
"""

from PyQt5.QtCore import (QPropertyAnimation, QEasingCurve, QParallelAnimationGroup,
                          QSequentialAnimationGroup, QVariantAnimation, QPoint, Qt)
from PyQt5.QtWidgets import QGraphicsOpacityEffect
from PyQt5.QtGui import QColor


class AnimationHelper:
    """动画辅助类 - 提供各种平滑动画效果"""
    
    @staticmethod
    def fade_in(widget, duration=200, start_opacity=0.0, end_opacity=1.0):
        """淡入动画
        
        Args:
            widget: 目标组件
            duration: 动画时长（毫秒）
            start_opacity: 起始透明度
            end_opacity: 结束透明度
            
        Returns:
            QPropertyAnimation: 动画对象
        """
        # 尝试复用已有的透明度效果，避免重复创建导致内存泄漏
        existing_effect = widget.graphicsEffect()
        if isinstance(existing_effect, QGraphicsOpacityEffect):
            effect = existing_effect
        else:
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(start_opacity)
        animation.setEndValue(end_opacity)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        return animation
    
    @staticmethod
    def fade_out(widget, duration=200, start_opacity=1.0, end_opacity=0.0):
        """淡出动画
        
        Args:
            widget: 目标组件
            duration: 动画时长（毫秒）
            start_opacity: 起始透明度
            end_opacity: 结束透明度
            
        Returns:
            QPropertyAnimation: 动画对象
        """
        return AnimationHelper.fade_in(widget, duration, start_opacity, end_opacity)
    
    @staticmethod
    def slide_in_from_left(widget, duration=250, start_x=-250):
        """从左侧滑入动画
        
        Args:
            widget: 目标组件
            duration: 动画时长（毫秒）
            start_x: 起始X坐标
            
        Returns:
            QPropertyAnimation: 动画对象
        """
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(QPoint(start_x, widget.y()))
        animation.setEndValue(QPoint(0, widget.y()))
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        return animation
    
    @staticmethod
    def slide_out_to_left(widget, duration=250, end_x=-250):
        """滑出到左侧动画
        
        Args:
            widget: 目标组件
            duration: 动画时长（毫秒）
            end_x: 结束X坐标
            
        Returns:
            QPropertyAnimation: 动画对象
        """
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        animation.setStartValue(widget.pos())
        animation.setEndValue(QPoint(end_x, widget.y()))
        animation.setEasingCurve(QEasingCurve.InCubic)
        
        return animation
    
    @staticmethod
    def expand_width(widget, start_width, end_width, duration=200):
        """宽度展开动画
        
        Args:
            widget: 目标组件
            start_width: 起始宽度
            end_width: 结束宽度
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation: 动画对象
        """
        animation = QPropertyAnimation(widget, b"maximumWidth")
        animation.setDuration(duration)
        animation.setStartValue(start_width)
        animation.setEndValue(end_width)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        return animation
    
    @staticmethod
    def collapse_width(widget, start_width, end_width, duration=200):
        """宽度收起动画
        
        Args:
            widget: 目标组件
            start_width: 起始宽度
            end_width: 结束宽度
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation: 动画对象
        """
        return AnimationHelper.expand_width(widget, start_width, end_width, duration)
    
    @staticmethod
    def expand_height(widget, start_height, end_height, duration=200):
        """高度展开动画
        
        Args:
            widget: 目标组件
            start_height: 起始高度
            end_height: 结束高度
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation: 动画对象
        """
        animation = QPropertyAnimation(widget, b"maximumHeight")
        animation.setDuration(duration)
        animation.setStartValue(start_height)
        animation.setEndValue(end_height)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        return animation
    
    @staticmethod
    def collapse_height(widget, start_height, end_height, duration=200):
        """高度收起动画
        
        Args:
            widget: 目标组件
            start_height: 起始高度
            end_height: 结束高度
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation: 动画对象
        """
        return AnimationHelper.expand_height(widget, start_height, end_height, duration)
    
    @staticmethod
    def color_transition(widget, property_name, start_color, end_color, duration=200):
        """颜色过渡动画
        
        Args:
            widget: 目标组件
            property_name: 属性名称（如 'backgroundColor'）
            start_color: 起始颜色
            end_color: 结束颜色
            duration: 动画时长（毫秒）
            
        Returns:
            QVariantAnimation: 动画对象
        """
        animation = QVariantAnimation()
        animation.setDuration(duration)
        animation.setStartValue(QColor(start_color))
        animation.setEndValue(QColor(end_color))
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        def update_color(color):
            widget.setStyleSheet(f"{property_name}: {color.name()};")
        
        animation.valueChanged.connect(update_color)
        
        return animation
    
    @staticmethod
    def smooth_scroll(scroll_area, target_value, duration=300):
        """平滑滚动动画
        
        Args:
            scroll_area: 滚动区域
            target_value: 目标滚动位置
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation: 动画对象
        """
        scroll_bar = scroll_area.verticalScrollBar()
        
        animation = QPropertyAnimation(scroll_bar, b"value")
        animation.setDuration(duration)
        animation.setStartValue(scroll_bar.value())
        animation.setEndValue(target_value)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        return animation
    
    @staticmethod
    def create_parallel_animation(*animations):
        """创建并行动画组
        
        Args:
            *animations: 多个动画对象
            
        Returns:
            QParallelAnimationGroup: 并行动画组
        """
        group = QParallelAnimationGroup()
        for animation in animations:
            group.addAnimation(animation)
        
        return group
    
    @staticmethod
    def create_sequential_animation(*animations):
        """创建顺序动画组
        
        Args:
            *animations: 多个动画对象
            
        Returns:
            QSequentialAnimationGroup: 顺序动画组
        """
        group = QSequentialAnimationGroup()
        for animation in animations:
            group.addAnimation(animation)
        
        return group
    
    @staticmethod
    def bounce_animation(widget, property_name=b"pos", amplitude=10, duration=500):
        """弹跳动画效果
        
        Args:
            widget: 目标组件
            property_name: 属性名称
            amplitude: 弹跳幅度
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation: 动画对象
        """
        animation = QPropertyAnimation(widget, property_name)
        animation.setDuration(duration)
        
        # 基于当前组件位置设置起始值和关键帧
        current_pos = widget.pos()
        bounce_pos = QPoint(current_pos.x(), current_pos.y() - amplitude)
        
        animation.setStartValue(current_pos)
        animation.setKeyValueAt(0.3, bounce_pos)
        animation.setKeyValueAt(0.6, current_pos)
        animation.setEndValue(current_pos)
        animation.setEasingCurve(QEasingCurve.OutBounce)
        
        return animation
    
    @staticmethod
    def shake_animation(widget, amplitude=5, duration=300):
        """抖动动画效果
        
        Args:
            widget: 目标组件
            amplitude: 抖动幅度
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation: 动画对象
        """
        animation = QPropertyAnimation(widget, b"pos")
        animation.setDuration(duration)
        
        # 基于当前组件位置设置起始值和关键帧
        start_pos = widget.pos()
        
        animation.setStartValue(start_pos)
        animation.setKeyValueAt(0.1, QPoint(start_pos.x() + amplitude, start_pos.y()))
        animation.setKeyValueAt(0.3, QPoint(start_pos.x() - amplitude, start_pos.y()))
        animation.setKeyValueAt(0.5, QPoint(start_pos.x() + amplitude, start_pos.y()))
        animation.setKeyValueAt(0.7, QPoint(start_pos.x() - amplitude, start_pos.y()))
        animation.setKeyValueAt(0.9, QPoint(start_pos.x() + amplitude, start_pos.y()))
        animation.setEndValue(start_pos)
        
        return animation
    
    @staticmethod
    def pulse_animation(widget, duration=1000):
        """脉冲动画效果（透明度闪烁）
        
        Args:
            widget: 目标组件
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation: 动画对象
        """
        # 尝试复用已有的透明度效果，避免重复创建导致内存泄漏
        existing_effect = widget.graphicsEffect()
        if isinstance(existing_effect, QGraphicsOpacityEffect):
            effect = existing_effect
        else:
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setKeyValueAt(0.5, 0.5)
        animation.setEndValue(1.0)
        animation.setLoopCount(-1)  # 无限循环
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        return animation


class VSCodeAnimationPresets:
    """VSCode风格动画预设"""
    
    @staticmethod
    def sidebar_toggle(sidebar_widget, visible, duration=200):
        """侧边栏切换动画
        
        Args:
            sidebar_widget: 侧边栏组件
            visible: 是否可见
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation: 动画对象
        
        注意：每次调用都创建新的动画对象，避免信号连接累积
        """
        if visible:
            # 展开侧边栏
            sidebar_widget.show()
            return AnimationHelper.expand_width(sidebar_widget, 0, 250, duration)
        else:
            # 收起侧边栏 - 每次创建新动画对象避免信号累积
            animation = AnimationHelper.collapse_width(sidebar_widget, 250, 0, duration)
            animation.finished.connect(sidebar_widget.hide)
            return animation
    
    @staticmethod
    def panel_toggle(panel_widget, visible, duration=200):
        """面板切换动画
        
        Args:
            panel_widget: 面板组件
            visible: 是否可见
            duration: 动画时长（毫秒）
            
        Returns:
            QPropertyAnimation: 动画对象
        
        注意：每次调用都创建新的动画对象，避免信号连接累积
        """
        if visible:
            # 展开面板
            panel_widget.show()
            return AnimationHelper.expand_height(panel_widget, 0, 200, duration)
        else:
            # 收起面板 - 每次创建新动画对象避免信号累积
            animation = AnimationHelper.collapse_height(panel_widget, 200, 0, duration)
            animation.finished.connect(panel_widget.hide)
            return animation
    
    @staticmethod
    def tab_switch(old_tab, new_tab, duration=150):
        """标签页切换动画
        
        Args:
            old_tab: 旧标签页组件
            new_tab: 新标签页组件
            duration: 动画时长（毫秒）
            
        Returns:
            QParallelAnimationGroup: 动画组
        
        注意：每次调用都创建新的动画对象，避免信号连接累积
        """
        # 淡出旧标签页 - 每次创建新动画对象避免信号累积
        fade_out = AnimationHelper.fade_out(old_tab, duration)
        fade_out.finished.connect(old_tab.hide)
        
        # 淡入新标签页
        new_tab.show()
        fade_in = AnimationHelper.fade_in(new_tab, duration)
        
        # 创建并行动画
        return AnimationHelper.create_parallel_animation(fade_out, fade_in)
    
    @staticmethod
    def notification_slide_in(notification_widget, duration=250):
        """通知滑入动画
        
        Args:
            notification_widget: 通知组件
            duration: 动画时长（毫秒）
            
        Returns:
            QSequentialAnimationGroup: 动画组
        """
        notification_widget.show()
        
        # 从右侧滑入
        slide = QPropertyAnimation(notification_widget, b"pos")
        slide.setDuration(duration)
        
        start_x = notification_widget.parent().width()
        end_x = notification_widget.parent().width() - notification_widget.width() - 20
        
        slide.setStartValue(QPoint(start_x, notification_widget.y()))
        slide.setEndValue(QPoint(end_x, notification_widget.y()))
        slide.setEasingCurve(QEasingCurve.OutCubic)
        
        # 淡入
        fade = AnimationHelper.fade_in(notification_widget, int(duration * 0.6))
        
        return AnimationHelper.create_parallel_animation(slide, fade)

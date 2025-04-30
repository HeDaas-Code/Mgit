#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                           QListWidgetItem, QPushButton, QLabel, QInputDialog, 
                           QMessageBox, QSplitter, QWidget, QApplication, 
                           QToolButton, QMenu, QAction, QComboBox, QFrame,
                           QLineEdit, QGroupBox, QFormLayout, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor
from qfluentwidgets import (PrimaryPushButton, TransparentToolButton, ToolButton, 
                         FluentIcon, InfoBar, InfoBarPosition, SearchLineEdit,
                         PushButton, TransparentPushButton, MessageBox, 
                         LineEdit, ExpandLayout, TeachingTip)

from src.utils.logger import info, warning, error, Logger, LogCategory

class BranchItem(QListWidgetItem):
    """分支列表项"""
    
    def __init__(self, name, is_current=False, parent=None):
        super().__init__(parent)
        self.branch_name = name
        self.is_current = is_current
        
        # 设置显示文本
        display_text = name
        if is_current:
            display_text += " (当前)"
            
        self.setText(display_text)
        
        # 设置图标
        if is_current:
            self.setIcon(FluentIcon.ACCEPT.icon())
        else:
            # 使用确定存在的FluentIcon
            self.setIcon(FluentIcon.CODE.icon())
            
        # 设置字体
        font = self.font()
        if is_current:
            font.setBold(True)
        self.setFont(font)
        
        # 存储数据
        self.setData(Qt.UserRole, name)


class BranchManagerDialog(QDialog):
    """分支管理对话框"""
    
    # 定义信号
    branchSwitched = pyqtSignal(str)  # 分支切换信号
    branchCreated = pyqtSignal(str)   # 分支创建信号
    branchDeleted = pyqtSignal(str)   # 分支删除信号
    branchMerged = pyqtSignal(str, str)  # 分支合并信号 (源分支, 目标分支)
    
    def __init__(self, git_manager, parent=None):
        super().__init__(parent)
        self.git_manager = git_manager
        self.logger = Logger()
        self.current_branch = self.git_manager.getCurrentBranch()
        self.initUI()
        self.loadBranches()
        
    def initUI(self):
        """初始化UI"""
        self.setWindowTitle("分支管理器")
        self.setMinimumSize(600, 450)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("分支管理器")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建分支区域
        create_group = QGroupBox("创建新分支")
        create_layout = QHBoxLayout(create_group)
        
        self.new_branch_input = LineEdit()
        self.new_branch_input.setPlaceholderText("输入新分支名称")
        
        self.checkout_checkbox = QCheckBox("创建后切换")
        self.checkout_checkbox.setChecked(True)
        
        create_btn = PrimaryPushButton("创建")
        create_btn.setIcon(FluentIcon.ADD.icon())
        create_btn.clicked.connect(self.createBranch)
        
        create_layout.addWidget(self.new_branch_input)
        create_layout.addWidget(self.checkout_checkbox)
        create_layout.addWidget(create_btn)
        
        main_layout.addWidget(create_group)
        
        # 分支列表和操作区域的分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：分支列表
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("分支列表")
        list_label.setFont(QFont("Arial", 12, QFont.Bold))
        
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("搜索分支...")
        self.search_input.textChanged.connect(self.filterBranches)
        
        self.branch_list = QListWidget()
        self.branch_list.setSelectionMode(QListWidget.SingleSelection)
        self.branch_list.currentItemChanged.connect(self.onBranchSelected)
        self.branch_list.itemDoubleClicked.connect(self.onBranchDoubleClicked)
        
        list_layout.addWidget(list_label)
        list_layout.addWidget(self.search_input)
        list_layout.addWidget(self.branch_list)
        
        splitter.addWidget(list_widget)
        
        # 右侧：分支操作
        actions_widget = QWidget()
        actions_layout = QVBoxLayout(actions_widget)
        
        actions_label = QLabel("分支操作")
        actions_label.setFont(QFont("Arial", 12, QFont.Bold))
        actions_layout.addWidget(actions_label)
        
        # 显示当前选中的分支信息
        self.branch_info = QLabel("请选择一个分支")
        actions_layout.addWidget(self.branch_info)
        
        # 分支操作按钮组
        self.checkout_btn = PushButton("切换到此分支")
        self.checkout_btn.setIcon(FluentIcon.SYNC.icon())
        self.checkout_btn.clicked.connect(self.checkoutBranch)
        self.checkout_btn.setEnabled(False)
        
        self.merge_btn = PushButton("合并到当前分支")
        self.merge_btn.setIcon(FluentIcon.EMBED.icon())
        self.merge_btn.clicked.connect(self.mergeBranch)
        self.merge_btn.setEnabled(False)
        
        self.delete_btn = PushButton("删除分支")
        self.delete_btn.setIcon(FluentIcon.DELETE.icon())
        self.delete_btn.clicked.connect(self.deleteBranch)
        self.delete_btn.setEnabled(False)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        
        # 合并特定分支的组合框
        merge_group = QGroupBox("高级合并")
        merge_group_layout = QHBoxLayout(merge_group)
        
        self.source_branch_combo = QComboBox()
        self.target_branch_combo = QComboBox()
        
        merge_specific_btn = PushButton("合并")
        merge_specific_btn.setIcon(FluentIcon.EMBED.icon())
        merge_specific_btn.clicked.connect(self.mergeSpecificBranches)
        
        merge_group_layout.addWidget(QLabel("从:"))
        merge_group_layout.addWidget(self.source_branch_combo, 1)
        merge_group_layout.addWidget(QLabel("到:"))
        merge_group_layout.addWidget(self.target_branch_combo, 1)
        merge_group_layout.addWidget(merge_specific_btn)
        
        # 添加所有操作小部件
        actions_layout.addWidget(self.checkout_btn)
        actions_layout.addWidget(self.merge_btn)
        actions_layout.addWidget(self.delete_btn)
        actions_layout.addWidget(line)
        actions_layout.addWidget(merge_group)
        actions_layout.addStretch()
        
        splitter.addWidget(actions_widget)
        
        # 设置默认分割比例 (2:1)
        splitter.setSizes([400, 200])
        
        main_layout.addWidget(splitter)
        
        # 底部按钮
        bottom_layout = QHBoxLayout()
        
        refresh_btn = PushButton("刷新")
        refresh_btn.setIcon(FluentIcon.SYNC.icon())
        refresh_btn.clicked.connect(self.loadBranches)
        
        close_btn = PushButton("关闭")
        close_btn.setIcon(FluentIcon.CLOSE.icon())
        close_btn.clicked.connect(self.close)
        
        bottom_layout.addWidget(refresh_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(close_btn)
        
        main_layout.addLayout(bottom_layout)
        
    def loadBranches(self):
        """加载所有分支"""
        try:
            self.branch_list.clear()
            self.source_branch_combo.clear()
            self.target_branch_combo.clear()
            
            # 获取当前分支
            self.current_branch = self.git_manager.getCurrentBranch()
            
            # 获取所有分支
            branches = self.git_manager.getBranches()
            
            for branch in branches:
                is_current = (branch == self.current_branch)
                item = BranchItem(branch, is_current)
                self.branch_list.addItem(item)
                
                # 添加到组合框
                self.source_branch_combo.addItem(branch)
                self.target_branch_combo.addItem(branch)
                
            # 默认选择当前分支
            self.selectCurrentBranch()
            
        except Exception as e:
            self.logger.error(f"加载分支失败: {str(e)}", category=LogCategory.REPOSITORY)
            QMessageBox.critical(self, "错误", f"加载分支失败: {str(e)}")
            
    def filterBranches(self, text):
        """根据搜索文本过滤分支"""
        text = text.lower()
        
        for i in range(self.branch_list.count()):
            item = self.branch_list.item(i)
            branch_name = item.branch_name.lower()
            
            if text in branch_name:
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def selectCurrentBranch(self):
        """选择当前分支"""
        for i in range(self.branch_list.count()):
            item = self.branch_list.item(i)
            if item.branch_name == self.current_branch:
                self.branch_list.setCurrentItem(item)
                break
    
    def onBranchSelected(self, current, previous):
        """处理分支选择变化"""
        if not current:
            self.branch_info.setText("请选择一个分支")
            self.checkout_btn.setEnabled(False)
            self.merge_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            return
            
        branch_name = current.branch_name
        is_current = (branch_name == self.current_branch)
        
        # 更新分支信息
        if is_current:
            self.branch_info.setText(f"<b>{branch_name}</b> (当前分支)")
        else:
            self.branch_info.setText(f"<b>{branch_name}</b>")
            
        # 更新按钮状态
        self.checkout_btn.setEnabled(not is_current)
        self.merge_btn.setEnabled(not is_current)
        # 不允许删除当前分支
        self.delete_btn.setEnabled(not is_current)
        
    def onBranchDoubleClicked(self, item):
        """处理分支双击事件"""
        branch_name = item.branch_name
        if branch_name != self.current_branch:
            self.checkoutBranch()
            
    def createBranch(self):
        """创建新分支"""
        branch_name = self.new_branch_input.text().strip()
        if not branch_name:
            InfoBar.warning(
                title="警告",
                content="请输入分支名称",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
            
        try:
            # 检查分支名称是否合法
            if not self.isValidBranchName(branch_name):
                InfoBar.error(
                    title="错误",
                    content="分支名称无效，不能包含空格、^、~、:、\\、*、?、[等特殊字符",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
                return
                
            # 检查分支是否已存在
            branches = self.git_manager.getBranches()
            if branch_name in branches:
                InfoBar.error(
                    title="错误",
                    content=f"分支 '{branch_name}' 已存在",
                    parent=self,
                    position=InfoBarPosition.TOP
                )
                return
                
            # 创建分支
            checkout = self.checkout_checkbox.isChecked()
            self.git_manager.createBranch(branch_name, checkout)
            
            # 发送信号
            self.branchCreated.emit(branch_name)
            
            # 如果切换了分支，更新当前分支
            if checkout:
                self.current_branch = branch_name
                self.branchSwitched.emit(branch_name)
                
            # 重新加载分支列表
            self.loadBranches()
            
            # 清空输入框
            self.new_branch_input.clear()
            
            InfoBar.success(
                title="成功",
                content=f"分支 '{branch_name}' 创建成功" + (" 并已切换" if checkout else ""),
                parent=self,
                position=InfoBarPosition.TOP
            )
            
        except Exception as e:
            self.logger.error(f"创建分支失败: {str(e)}", category=LogCategory.REPOSITORY)
            QMessageBox.critical(self, "错误", f"创建分支失败: {str(e)}")
            
    def checkoutBranch(self):
        """切换到选中的分支"""
        current_item = self.branch_list.currentItem()
        if not current_item:
            return
            
        branch_name = current_item.branch_name
        if branch_name == self.current_branch:
            return
            
        try:
            # 检查工作区是否有未提交的更改
            changed_files = self.git_manager.getChangedFiles()
            if changed_files:
                reply = QMessageBox.question(
                    self,
                    "未提交的更改",
                    f"工作区有未提交的更改。切换分支可能会丢失这些更改。\n是否继续?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            
            # 切换分支
            self.git_manager.checkoutBranch(branch_name)
            
            # 更新当前分支
            self.current_branch = branch_name
            
            # 重新加载分支列表，确保UI状态一致
            self.loadBranches()
            
            # 发送信号
            self.branchSwitched.emit(branch_name)
            
            InfoBar.success(
                title="成功",
                content=f"已切换到分支 '{branch_name}'",
                parent=self,
                position=InfoBarPosition.TOP
            )
            
        except Exception as e:
            self.logger.error(f"切换分支失败: {str(e)}", category=LogCategory.REPOSITORY)
            QMessageBox.critical(self, "错误", f"切换分支失败: {str(e)}")
            
    def mergeBranch(self):
        """将选中的分支合并到当前分支"""
        current_item = self.branch_list.currentItem()
        if not current_item:
            return
            
        branch_name = current_item.branch_name
        if branch_name == self.current_branch:
            return
            
        try:
            # 确认合并
            reply = QMessageBox.question(
                self,
                "合并确认",
                f"确定要将分支 '{branch_name}' 合并到当前分支 '{self.current_branch}' 吗?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
            # 执行合并
            self.git_manager.mergeBranch(branch_name)
            
            # 发送信号
            self.branchMerged.emit(branch_name, self.current_branch)
            
            InfoBar.success(
                title="成功",
                content=f"分支 '{branch_name}' 已合并到 '{self.current_branch}'",
                parent=self,
                position=InfoBarPosition.TOP
            )
            
        except Exception as e:
            self.logger.error(f"合并分支失败: {str(e)}", category=LogCategory.REPOSITORY)
            QMessageBox.critical(self, "错误", f"合并分支失败: {str(e)}")
            
    def mergeSpecificBranches(self):
        """将特定分支合并到另一个分支"""
        source_branch = self.source_branch_combo.currentText()
        target_branch = self.target_branch_combo.currentText()
        
        if source_branch == target_branch:
            InfoBar.warning(
                title="警告",
                content="源分支和目标分支不能相同",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
            
        try:
            # 确认合并
            reply = QMessageBox.question(
                self,
                "合并确认",
                f"确定要将分支 '{source_branch}' 合并到分支 '{target_branch}' 吗?\n这将切换到目标分支。",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
            # 切换到目标分支
            self.git_manager.checkoutBranch(target_branch)
            
            # 执行合并
            self.git_manager.mergeBranch(source_branch)
            
            # 更新当前分支
            self.current_branch = target_branch
            
            # 发送信号
            self.branchSwitched.emit(target_branch)
            self.branchMerged.emit(source_branch, target_branch)
            
            # 重新加载分支列表
            self.loadBranches()
            
            InfoBar.success(
                title="成功",
                content=f"分支 '{source_branch}' 已合并到 '{target_branch}'",
                parent=self,
                position=InfoBarPosition.TOP
            )
            
        except Exception as e:
            self.logger.error(f"合并分支失败: {str(e)}", category=LogCategory.REPOSITORY)
            QMessageBox.critical(self, "错误", f"合并分支失败: {str(e)}")
            
    def deleteBranch(self):
        """删除选中的分支"""
        current_item = self.branch_list.currentItem()
        if not current_item:
            return
            
        branch_name = current_item.branch_name
        if branch_name == self.current_branch:
            InfoBar.warning(
                title="警告",
                content="不能删除当前分支",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
            
        try:
            # 确认删除
            reply = QMessageBox.question(
                self,
                "删除确认",
                f"确定要删除分支 '{branch_name}' 吗?\n这个操作不可撤销!",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
                
            # 执行删除
            try:
                # 先尝试普通删除
                self.git_manager.deleteBranch(branch_name, force=False)
            except Exception as e:
                # 如果普通删除失败，询问是否强制删除
                if "not fully merged" in str(e):
                    reply = QMessageBox.question(
                        self,
                        "强制删除",
                        f"分支 '{branch_name}' 未完全合并。\n强制删除可能会丢失提交。\n是否强制删除?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.No:
                        return
                        
                    # 强制删除
                    self.git_manager.deleteBranch(branch_name, force=True)
                else:
                    # 其他错误，直接抛出
                    raise e
            
            # 发送信号
            self.branchDeleted.emit(branch_name)
            
            # 重新加载分支列表
            self.loadBranches()
            
            InfoBar.success(
                title="成功",
                content=f"分支 '{branch_name}' 已删除",
                parent=self,
                position=InfoBarPosition.TOP
            )
            
        except Exception as e:
            self.logger.error(f"删除分支失败: {str(e)}", category=LogCategory.REPOSITORY)
            QMessageBox.critical(self, "错误", f"删除分支失败: {str(e)}")
            
    def isValidBranchName(self, name):
        """检查分支名称是否合法"""
        # Git分支名称不能包含: 空格、^~:、\、*、?、[
        invalid_chars = [' ', '^', '~', ':', '\\', '*', '?', '[', '.', ',', '/', '@', '{', '}']
        return not any(char in name for char in invalid_chars) 
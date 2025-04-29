#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import git
from datetime import datetime
from src.utils.license_templates import get_cc_by_4_0_license
import datetime as dt

class GitManager:
    """ Git仓库管理器 """
    
    # 类级变量，用于防止循环调用
    _is_fetching = False
    
    def __init__(self, repo_path):
        """ 初始化Git管理器 """
        self.repo_path = repo_path
        self.repo = None
        self.connect()
        
    def connect(self):
        """ 连接到Git仓库 """
        if os.path.exists(os.path.join(self.repo_path, '.git')):
            self.repo = git.Repo(self.repo_path)
        else:
            raise ValueError(f"{self.repo_path} 不是有效的Git仓库")
    
    @staticmethod
    def initRepository(path, initial_branch="main"):
        """ 初始化一个新的Git仓库
        Args:
            path: 仓库路径
            initial_branch: 初始分支名称，默认为main
        Returns:
            git.Repo: 初始化的仓库对象
        """
        # 确保路径是绝对路径
        path = os.path.abspath(path)
        
        # 输出路径信息用于调试
        import sys
        if hasattr(sys, "_MEIPASS"):
            print(f"在PyInstaller环境中，初始化仓库路径: {path}")
        
        # 创建目录（如果不存在）
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except Exception as e:
                raise Exception(f"无法创建目录 {path}: {str(e)}")
            
        # 检查目录是否为空
        if os.listdir(path):
            # 目录非空，检查是否已经是Git仓库
            if os.path.exists(os.path.join(path, '.git')):
                return git.Repo(path)
        
        # 初始化仓库
        try:
            repo = git.Repo.init(path, initial_branch=initial_branch)
        except Exception as e:
            raise Exception(f"初始化仓库失败: {str(e)}")
        
        # 获取项目名称
        project_name = os.path.basename(path)
        
        # 获取当前年份
        current_year = dt.datetime.now().year
        
        try:
            # 创建README文件
            readme_path = os.path.join(path, 'README.md')
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(f"# {project_name}\n\n初始化的Git仓库")
            
            # 创建LICENSE文件（使用CC4.0许可证）
            license_path = os.path.join(path, 'LICENSE')
            with open(license_path, 'w', encoding='utf-8') as f:
                license_content = get_cc_by_4_0_license(project_name, current_year, "Author")
                f.write(license_content)
                
            # 添加并提交README和LICENSE
            repo.git.add('README.md')
            repo.git.add('LICENSE')
            repo.git.commit('-m', '初始化仓库，添加README和CC4.0协议LICENSE')
        except Exception as e:
            raise Exception(f"初始化仓库文件失败: {str(e)}")
        
        return repo
            
    def isValidRepo(self):
        """ 检查是否为有效的Git仓库 """
        try:
            if self.repo is None:
                self.connect()
            return True
        except:
            return False
            
    def getCurrentBranch(self):
        """ 获取当前分支名称 """
        if not self.isValidRepo():
            return ""
        return self.repo.active_branch.name
        
    def getChangedFiles(self):
        """ 获取已更改的文件列表 """
        if not self.isValidRepo():
            return []
            
        changed_files = []
        
        # 获取未跟踪文件
        for untracked_file in self.repo.untracked_files:
            changed_files.append(("未跟踪", untracked_file))
            
        # 获取已修改但未暂存的文件
        for diff in self.repo.index.diff(None):
            if diff.change_type == 'D':
                changed_files.append(("已删除", diff.a_path))
            elif diff.change_type == 'M':
                changed_files.append(("已修改", diff.a_path))
            elif diff.change_type == 'R':
                changed_files.append(("已重命名", diff.a_path))
            else:
                changed_files.append((diff.change_type, diff.a_path))
                
        # 获取已暂存的文件
        for diff in self.repo.index.diff('HEAD'):
            if diff.change_type == 'A':
                changed_files.append(("已暂存", diff.a_path))
            elif diff.change_type == 'D':
                changed_files.append(("已暂存删除", diff.a_path))
            elif diff.change_type == 'M':
                changed_files.append(("已暂存修改", diff.a_path))
            else:
                changed_files.append((f"已暂存{diff.change_type}", diff.a_path))
                
        return changed_files
        
    def getCommitHistory(self, count=10):
        """ 获取提交历史 """
        if not self.isValidRepo():
            return []
            
        commits = []
        for commit in list(self.repo.iter_commits('HEAD', max_count=count)):
            commits.append({
                'hash': str(commit.hexsha),
                'author': str(commit.author),
                'date': datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S'),
                'message': commit.message.strip()
            })
            
        return commits
        
    def getCommitDetails(self, commit_hash):
        """ 获取提交详情
        Args:
            commit_hash: 提交的哈希值
        Returns:
            str: 格式化的提交详情
        """
        if not self.isValidRepo():
            return "无效的Git仓库"
            
        try:
            # 使用Git命令获取详细信息
            return self.repo.git.show(commit_hash, pretty='fuller', name_only=False, name_status=True)
        except Exception as e:
            return f"无法获取提交详情: {str(e)}"
        
    def stage(self, file_paths):
        """ 暂存文件 """
        if not self.isValidRepo():
            return
            
        # 转换为相对路径
        relative_paths = []
        for path in file_paths:
            if os.path.isabs(path):
                rel_path = os.path.relpath(path, self.repo_path)
            else:
                rel_path = path
            relative_paths.append(rel_path)
            
        self.repo.git.add(relative_paths)
        
    def unstage(self, file_paths):
        """ 取消暂存文件 """
        if not self.isValidRepo():
            return
            
        # 转换为相对路径
        relative_paths = []
        for path in file_paths:
            if os.path.isabs(path):
                rel_path = os.path.relpath(path, self.repo_path)
            else:
                rel_path = path
            relative_paths.append(rel_path)
            
        self.repo.git.reset('HEAD', '--', *relative_paths)
        
    def commit(self, file_paths, message):
        """ 提交更改 """
        if not self.isValidRepo():
            return
            
        # 暂存文件
        self.stage(file_paths)
        
        # 提交更改
        self.repo.git.commit('-m', message)
        
    def pull(self, remote_name='origin', branch=None):
        """ 拉取远程更改
        Args:
            remote_name: 远程仓库名称，默认为origin
            branch: 分支名称，默认为当前分支
        """
        if not self.isValidRepo():
            return
            
        try:
            # 检查远程仓库是否存在
            if remote_name not in [remote.name for remote in self.repo.remotes]:
                raise Exception(f"找不到名为 '{remote_name}' 的远程仓库")
                
            # 如果未指定分支，使用当前分支
            if branch is None:
                branch = self.getCurrentBranch()
                
            # 拉取更改
            self.repo.git.pull(remote_name, branch)
        except git.exc.GitCommandError as e:
            error_msg = str(e).lower()
            if "could not resolve host" in error_msg:
                raise Exception("无法连接到远程仓库，请检查网络连接")
            elif "authentication failed" in error_msg:
                raise Exception("身份验证失败，请检查您的凭据")
            elif "not a git repository" in error_msg:
                raise Exception(f"远程 '{remote_name}' 不是有效的Git仓库")
            elif "no such remote" in error_msg:
                raise Exception(f"找不到名为 '{remote_name}' 的远程仓库")
            else:
                raise Exception(f"拉取更改失败: {str(e)}")
        except Exception as e:
            raise Exception(f"拉取更改失败: {str(e)}")
            
    def push(self, remote_name='origin', branch=None, set_upstream=False):
        """ 推送更改到远程仓库
        Args:
            remote_name: 远程仓库名称，默认为origin
            branch: 分支名称，默认为当前分支
            set_upstream: 是否设置上游分支，默认为False
        """
        if not self.isValidRepo():
            return
            
        try:
            # 检查远程仓库是否存在
            if remote_name not in [remote.name for remote in self.repo.remotes]:
                raise Exception(f"找不到名为 '{remote_name}' 的远程仓库")
                
            # 如果未指定分支，使用当前分支
            if branch is None:
                branch = self.getCurrentBranch()
                
            # 获取远程URL以进行调试
            remote = self.repo.remote(remote_name)
            urls = list(remote.urls)
            remote_url = urls[0] if urls else "未知URL"
            print(f"准备推送到远程仓库: {remote_url}, 分支: {branch}")
                
            # 推送更改
            if set_upstream:
                # 添加调试信息
                print(f"执行: git push -u {remote_name} {branch}")
                self.repo.git.push('-u', remote_name, branch)
            else:
                print(f"执行: git push {remote_name} {branch}")
                self.repo.git.push(remote_name, branch)
        except git.exc.GitCommandError as e:
            error_msg = str(e).lower()
            if "could not resolve host" in error_msg:
                raise Exception("无法连接到远程仓库，请检查网络连接")
            elif "authentication failed" in error_msg or "not authorized" in error_msg:
                raise Exception("身份验证失败，请检查您的凭据和权限是否正确")
            elif "not a git repository" in error_msg or "repository not found" in error_msg:
                raise Exception(f"远程 '{remote_name}' 不是有效的Git仓库或您没有访问权限，URL: {remote_url}")
            elif "no such remote" in error_msg:
                raise Exception(f"找不到名为 '{remote_name}' 的远程仓库")
            elif "refused" in error_msg:
                raise Exception("远程仓库拒绝了推送，可能需要先拉取更新")
            elif "remote contains work that you do" in error_msg or "reject" in error_msg:
                raise Exception("远程仓库包含您没有的更改，请先使用拉取(pull)操作")
            else:
                # 提供原始错误信息以便调试
                raise Exception(f"推送更改失败: {str(e)}")
        except Exception as e:
            raise Exception(f"推送更改失败: {str(e)}")
        
    def discard(self, file_paths):
        """ 丢弃更改 """
        if not self.isValidRepo():
            return
            
        # 转换为相对路径
        relative_paths = []
        for path in file_paths:
            if os.path.isabs(path):
                rel_path = os.path.relpath(path, self.repo_path)
            else:
                rel_path = path
            relative_paths.append(rel_path)
            
        # 检查文件是否未跟踪
        untracked = self.repo.untracked_files
        
        for path in relative_paths:
            if path in untracked:
                # 对于未跟踪的文件，直接删除
                full_path = os.path.join(self.repo_path, path)
                if os.path.exists(full_path):
                    os.remove(full_path)
            else:
                # 对于已跟踪的文件，恢复到HEAD
                self.repo.git.checkout('HEAD', '--', path)
                
    def createBranch(self, branch_name):
        """ 创建新分支 """
        if not self.isValidRepo():
            return
            
        self.repo.git.branch(branch_name)
        
    def checkoutBranch(self, branch_name):
        """ 切换到指定分支 """
        if not self.isValidRepo():
            return
            
        self.repo.git.checkout(branch_name)
        
    def mergeBranch(self, branch_name):
        """ 合并指定分支到当前分支 """
        if not self.isValidRepo():
            return
            
        self.repo.git.merge(branch_name)
        
    def getBranches(self):
        """ 获取所有分支 """
        if not self.isValidRepo():
            return []
            
        branches = []
        for branch in self.repo.branches:
            branches.append(str(branch))
            
        return branches
        
    def getRemotes(self):
        """ 获取所有远程仓库 """
        if not self.isValidRepo():
            return []
            
        remotes = []
        for remote in self.repo.remotes:
            remotes.append(str(remote))
            
        return remotes
        
    def getFileHistory(self, file_path, count=10):
        """ 获取文件的历史记录 """
        if not self.isValidRepo():
            return []
            
        # 转换为相对路径
        if os.path.isabs(file_path):
            rel_path = os.path.relpath(file_path, self.repo_path)
        else:
            rel_path = file_path
            
        commits = []
        for commit in list(self.repo.iter_commits('HEAD', paths=rel_path, max_count=count)):
            commits.append({
                'hash': str(commit.hexsha),
                'author': str(commit.author),
                'date': datetime.fromtimestamp(commit.committed_date).strftime('%Y-%m-%d %H:%M:%S'),
                'message': commit.message.strip()
            })
            
        return commits
        
    def getFileContent(self, file_path, commit_hash='HEAD'):
        """ 获取指定提交中的文件内容 """
        if not self.isValidRepo():
            return ""
            
        # 转换为相对路径
        if os.path.isabs(file_path):
            rel_path = os.path.relpath(file_path, self.repo_path)
        else:
            rel_path = file_path
            
        # 获取文件内容
        try:
            return self.repo.git.show(f"{commit_hash}:{rel_path}")
        except:
            return ""
            
    def addRemote(self, name, url):
        """ 添加远程仓库
        Args:
            name: 远程仓库名称
            url: 远程仓库URL
        """
        if not self.isValidRepo():
            return
            
        try:
            # 处理URL格式
            url = GitManager.sanitize_url(url)
            
            # 检查是否已存在同名远程仓库
            for remote in self.repo.remotes:
                if remote.name == name:
                    raise Exception(f"远程仓库 '{name}' 已存在")
                    
            # 添加远程仓库
            self.repo.create_remote(name, url)
        except Exception as e:
            raise Exception(f"添加远程仓库失败: {str(e)}")
            
    def removeRemote(self, name):
        """ 删除远程仓库
        Args:
            name: 远程仓库名称
        """
        if not self.isValidRepo():
            return False
            
        try:
            self.repo.delete_remote(name)
            return True
        except Exception as e:
            raise Exception(f"删除远程仓库失败: {str(e)}")
            
    def getRemoteDetails(self):
        """ 获取远程仓库详细信息
        Returns:
            list: 远程仓库信息列表，包含名称和URL
        """
        if not self.isValidRepo():
            return []
            
        remotes = []
        for remote in self.repo.remotes:
            remote_urls = list(remote.urls)
            remotes.append({
                'name': remote.name,
                'url': remote_urls[0] if remote_urls else ""
            })
            
        return remotes
            
    def fetch(self, remote_name='origin'):
        """ 从远程仓库获取更新
        Args:
            remote_name: 远程仓库名称，默认为origin
        """
        if not self.isValidRepo():
            return
            
        # 防止循环调用
        if GitManager._is_fetching:
            return
            
        try:
            GitManager._is_fetching = True
            # 使用git命令直接执行fetch，避免使用GitPython的高级API可能引起的循环调用
            self.repo.git.fetch(remote_name)
            GitManager._is_fetching = False
        except Exception as e:
            GitManager._is_fetching = False
            raise Exception(f"获取更新失败: {str(e)}")
            
    def createBranch(self, branch_name, checkout=False):
        """ 创建新分支
        Args:
            branch_name: 分支名称
            checkout: 是否切换到新分支，默认为False
        """
        if not self.isValidRepo():
            return
            
        try:
            # 创建分支
            self.repo.git.branch(branch_name)
            
            # 如果需要，切换到新分支
            if checkout:
                self.repo.git.checkout(branch_name)
        except Exception as e:
            raise Exception(f"创建分支失败: {str(e)}")
            
    def deleteBranch(self, branch_name, force=False):
        """ 删除分支
        Args:
            branch_name: 分支名称
            force: 是否强制删除，默认为False
        """
        if not self.isValidRepo():
            return
            
        try:
            # 删除分支
            if force:
                self.repo.git.branch('-D', branch_name)
            else:
                self.repo.git.branch('-d', branch_name)
        except Exception as e:
            raise Exception(f"删除分支失败: {str(e)}")
            
    def hasMergeConflicts(self):
        """ 检查是否有合并冲突
        Returns:
            bool: 是否有合并冲突
        """
        if not self.isValidRepo():
            return False
            
        try:
            # 获取未合并的路径
            unmerged_blobs = self.repo.index.unmerged_blobs()
            return len(unmerged_blobs) > 0
        except:
            return False
            
    def getConflictFiles(self):
        """ 获取冲突文件列表
        Returns:
            list: 冲突文件路径列表
        """
        if not self.isValidRepo():
            return []
            
        try:
            # 获取未合并的路径
            unmerged_blobs = self.repo.index.unmerged_blobs()
            conflict_files = set()
            
            for path in unmerged_blobs:
                conflict_files.add(path)
                
            return list(conflict_files)
        except:
            return []
            
    def abortMerge(self):
        """ 中止合并操作 """
        if not self.isValidRepo():
            return
            
        try:
            self.repo.git.merge('--abort')
        except Exception as e:
            raise Exception(f"中止合并失败: {str(e)}")
            
    def continueMerge(self):
        """ 继续合并操作 """
        if not self.isValidRepo():
            return
            
        try:
            self.repo.git.merge('--continue')
        except Exception as e:
            raise Exception(f"继续合并失败: {str(e)}")
            
    def getStashList(self):
        """ 获取存储列表
        Returns:
            list: 存储信息列表
        """
        if not self.isValidRepo():
            return []
            
        try:
            # 获取存储列表
            result = self.repo.git.stash('list')
            stashes = []
            
            if result:
                for line in result.split('\n'):
                    if line:
                        stashes.append(line)
                        
            return stashes
        except:
            return []
            
    def stashChanges(self, message=None):
        """ 存储更改
        Args:
            message: 存储描述，默认为None
        """
        if not self.isValidRepo():
            return
            
        try:
            if message:
                self.repo.git.stash('save', message)
            else:
                self.repo.git.stash()
        except Exception as e:
            raise Exception(f"存储更改失败: {str(e)}")
            
    def applyStash(self, stash_id=0):
        """ 应用存储
        Args:
            stash_id: 存储ID，默认为0（最近的存储）
        """
        if not self.isValidRepo():
            return
            
        try:
            self.repo.git.stash('apply', f'stash@{{{stash_id}}}')
        except Exception as e:
            raise Exception(f"应用存储失败: {str(e)}")
            
    def dropStash(self, stash_id=0):
        """ 删除存储
        Args:
            stash_id: 存储ID，默认为0（最近的存储）
        """
        if not self.isValidRepo():
            return
            
        try:
            self.repo.git.stash('drop', f'stash@{{{stash_id}}}')
        except Exception as e:
            raise Exception(f"删除存储失败: {str(e)}")
            
    def clearStash(self):
        """ 清空所有存储 """
        if not self.isValidRepo():
            return
            
        try:
            self.repo.git.stash('clear')
        except Exception as e:
            raise Exception(f"清空存储失败: {str(e)}")
            
    @staticmethod
    def sanitize_url(url):
        """ 清理并规范化Git URL
        Args:
            url: 原始URL
        Returns:
            str: 清理后的URL
        """
        # 移除URL中可能的空格和特殊字符
        url = url.strip()
        
        # 如果是快捷方式格式，转换为完整URL
        if not url.startswith("http") and not url.startswith("git@") and "/" in url:
            if url.count("/") == 1:  # 确保只有一个斜杠
                url = f"https://github.com/{url}.git"
                
        # 处理GitHub特定的快捷格式
        if "github.com:HeDass-OF" in url:
            url = url.replace("github.com:HeDass-OF", "github.com/HeDass-OF")
        
        # 标准化GitHub URL格式
        if "github.com" in url:
            # 移除多余的冒号
            url = url.replace("github.com:/", "github.com/")
            url = url.replace("github.com://", "github.com/")
            url = url.replace("github.com:///", "github.com/")
            
            # 修复格式不正确的URL
            if ":github.com" in url and "git@:github.com" not in url:
                url = url.replace(":github.com", "github.com")
                
            # 确保使用正确的协议格式
            if not url.startswith("git@") and "github.com:" in url:
                parts = url.split("github.com:")
                if len(parts) > 1:
                    if url.startswith("http"):
                        url = f"{parts[0]}github.com/{parts[1]}"
                    else:
                        url = f"https://github.com/{parts[1]}"
        
        # 处理可能的URL格式问题（处理冒号问题）
        if ":" in url and not url.startswith("git@"):
            # 检查是否有不正确的端口指定
            parts = url.split(":")
            if len(parts) > 1 and not parts[0].endswith("//"):
                # 修正格式为标准https URL
                domain_parts = parts[0].split("//")
                if len(domain_parts) > 1:
                    protocol = domain_parts[0] + "//"
                    domain = domain_parts[1]
                    url = protocol + domain + "/" + "/".join(parts[1:])
        
        # 确保没有特殊字符，如中文括号等
        url = url.replace("（", "(").replace("）", ")")
        
        # 确保.git后缀
        if "github.com" in url and not url.endswith(".git") and not "github.com//" in url:
            if not any(char in url for char in "?&#"):  # 排除有查询参数的URL
                url = url + ".git"
        
        return url
            
    @staticmethod
    def cloneRepository(url, target_path, branch=None, depth=None, recursive=False):
        """ 从远程克隆仓库
        Args:
            url: 远程仓库URL
            target_path: 本地目标路径
            branch: 指定要克隆的分支，默认为None（克隆默认分支）
            depth: 指定历史深度，默认为None（完整历史）
            recursive: 是否递归克隆子模块，默认为False
        Returns:
            git.Repo: 克隆的仓库对象
        """
        try:
            # 处理URL格式
            url = GitManager.sanitize_url(url)
            
            # 构建克隆参数
            clone_args = {}
            if branch:
                clone_args['branch'] = branch
            if depth:
                clone_args['depth'] = depth
            if recursive:
                clone_args['recursive'] = True
                
            # 克隆仓库
            repo = git.Repo.clone_from(url, target_path, **clone_args)
            return repo
        except git.exc.GitCommandError as e:
            error_msg = str(e).lower()
            # 处理特定的Git错误
            if "could not resolve host" in error_msg:
                raise Exception("无法连接到远程仓库，请检查网络连接或URL是否正确")
            elif "authentication failed" in error_msg:
                raise Exception("身份验证失败，请检查您的凭据或确认是否有访问权限")
            elif "not a git repository" in error_msg:
                raise Exception("指定的URL不是一个有效的Git仓库")
            elif "already exists" in error_msg and "destination path" in error_msg:
                raise Exception(f"目标路径 '{target_path}' 已存在且不为空")
            elif "couldn't find remote ref" in error_msg and branch:
                raise Exception(f"找不到指定的分支 '{branch}'")
            else:
                raise Exception(f"克隆仓库失败: {str(e)}")
        except Exception as e:
            raise Exception(f"克隆仓库失败: {str(e)}")
            
    def syncWithRemote(self, remote_name='origin', branch=None):
        """ 与远程仓库同步（先拉取后推送）
        Args:
            remote_name: 远程仓库名称，默认为origin
            branch: 分支名称，默认为当前分支
        """
        if not self.isValidRepo():
            return
            
        try:
            # 如果未指定分支，使用当前分支
            if branch is None:
                branch = self.getCurrentBranch()
            
            # 先执行fetch操作
            self.fetch(remote_name)
            
            # 执行merge操作（相当于git pull的第二步）
            remote_branch = f"{remote_name}/{branch}"
            self.repo.git.merge(remote_branch)
            
            # 推送更改
            self.push(remote_name, branch)
        except Exception as e:
            raise Exception(f"同步失败: {str(e)}")
            
    def importExternalRepo(self, url, as_remote=True, remote_name="origin"):
        """ 导入外部仓库（添加为远程仓库或直接合并）
        Args:
            url: 外部仓库URL
            as_remote: 是否添加为远程仓库，默认为True
            remote_name: 远程仓库名称，默认为origin
        """
        if not self.isValidRepo():
            return
            
        try:
            # 处理URL格式
            url = GitManager.sanitize_url(url)
            
            if as_remote:
                # 添加为远程仓库
                if remote_name in [remote.name for remote in self.repo.remotes]:
                    # 已存在同名远程仓库，更新URL
                    self.repo.git.remote('set-url', remote_name, url)
                else:
                    # 添加新的远程仓库
                    self.repo.create_remote(remote_name, url)
            else:
                # 不添加为远程仓库，直接拉取合并
                # 防止循环调用fetch
                if not GitManager._is_fetching:
                    try:
                        GitManager._is_fetching = True
                        # 使用git命令直接执行fetch，避免使用GitPython的高级API
                        self.repo.git.fetch(url, f"{self.getCurrentBranch()}:temp_branch")
                        GitManager._is_fetching = False
                    except Exception as e:
                        GitManager._is_fetching = False
                        raise e
                
                # 合并临时分支
                self.repo.git.merge("temp_branch")
                # 删除临时分支
                self.repo.git.branch("-D", "temp_branch")
        except git.exc.GitCommandError as e:
            # 处理特定的Git错误
            if "could not resolve host" in str(e).lower():
                raise Exception("无法连接到远程仓库，请检查网络连接或URL是否正确")
            elif "authentication failed" in str(e).lower():
                raise Exception("身份验证失败，请检查您的凭据或确认是否有访问权限")
            elif "not a git repository" in str(e).lower():
                raise Exception("指定的URL不是一个有效的Git仓库")
            elif "already exists" in str(e).lower() and "remote" in str(e).lower():
                raise Exception(f"远程仓库 '{remote_name}' 已存在")
            else:
                raise Exception(f"导入外部仓库失败: {str(e)}")
        except Exception as e:
            raise Exception(f"导入外部仓库失败: {str(e)}")
            
    def isFileTracked(self, file_path):
        """ 检查文件是否被Git跟踪
        Args:
            file_path: 相对于仓库根目录的文件路径
        Returns:
            bool: 是否被跟踪
        """
        try:
            return not self.repo.git.ls_files('--error-unmatch', file_path).strip() == ''
        except:
            return False
            
    def getFileCommitHistory(self, file_path, max_count=10):
        """ 获取文件的提交历史
        Args:
            file_path: 相对于仓库根目录的文件路径
            max_count: 最大返回数量
        Returns:
            list: 历史提交列表
        """
        try:
            # 检查文件是否存在且被跟踪
            if not self.isFileTracked(file_path):
                return []
                
            # 获取文件的提交历史
            log_output = self.repo.git.log(f'--max-count={max_count}', '--pretty=format:%H|%an|%at|%s', file_path)
            
            if not log_output:
                return []
                
            commits = []
            for line in log_output.split('\n'):
                parts = line.split('|')
                if len(parts) >= 4:
                    commit_hash, author, timestamp, message = parts
                    
                    # 格式化时间戳
                    import datetime
                    date = datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
                    
                    commits.append({
                        'hash': commit_hash,
                        'author': author,
                        'date': date,
                        'message': message
                    })
                    
            return commits
        except Exception as e:
            print(f"获取文件提交历史失败: {str(e)}")
            return []
            
    def getFileContentAtCommit(self, file_path, commit_hash):
        """ 获取指定提交版本的文件内容
        Args:
            file_path: 相对于仓库根目录的文件路径
            commit_hash: 提交哈希
        Returns:
            str: 文件内容
        """
        try:
            content = self.repo.git.show(f'{commit_hash}:{file_path}')
            return content
        except Exception as e:
            print(f"获取提交版本的文件内容失败: {str(e)}")
            return ""
            
    def revertFileToCommit(self, file_path, commit_hash):
        """ 回退文件到指定提交版本
        Args:
            file_path: 相对于仓库根目录的文件路径
            commit_hash: 提交哈希
        """
        try:
            self.repo.git.checkout(commit_hash, '--', file_path)
            return True
        except Exception as e:
            print(f"回退文件到指定版本失败: {str(e)}")
            return False 
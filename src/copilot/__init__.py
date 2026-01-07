#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copilot module for MGit - AI-powered writing assistant
"""

from .copilot_manager import CopilotManager
from .siliconflow_client import SiliconFlowClient
from .modelscope_client import ModelScopeClient

__all__ = ['CopilotManager', 'SiliconFlowClient', 'ModelScopeClient']

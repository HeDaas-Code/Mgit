# Copilot Developer Guide

This guide is for developers who want to understand, modify, or extend the MGit Copilot system.

## Architecture Overview

The copilot system consists of four main components:

```
┌─────────────────┐
│  Main Window    │  - UI Integration
│                 │  - Menu items & shortcuts
└────────┬────────┘
         │
    ┌────▼────────────────┐
    │  CopilotManager     │  - Central coordinator
    │                     │  - Mode management
    └────┬────────────────┘
         │
    ┌────▼────────────────┐
    │ SiliconFlowClient   │  - API communication
    │                     │  - HTTP requests
    └─────────────────────┘
         │
    ┌────▼────────────────┐
    │   AgentMode         │  - Autonomous tasks
    │                     │  - Audit system
    └─────────────────────┘
```

## Component Details

### 1. SiliconFlowClient (`src/copilot/siliconflow_client.py`)

**Purpose**: HTTP client for SiliconFlow API

**Key Methods**:
- `chat_completion()`: Send chat messages to LLM
- `text_completion()`: Get text completion
- `get_embedding()`: Get text embeddings
- `test_connection()`: Verify API connectivity

**Usage Example**:
```python
from src.copilot.siliconflow_client import SiliconFlowClient

client = SiliconFlowClient(api_key="your-key")
messages = [{'role': 'user', 'content': 'Hello'}]
response = client.chat_completion(messages)
```

### 2. CopilotManager (`src/copilot/copilot_manager.py`)

**Purpose**: Central manager coordinating all copilot features

**Key Methods**:
- `get_inline_completion()`: Request inline completion
- `edit_text()`: Edit text with instructions
- `create_content()`: Generate new content
- `chat()`: Chat conversation

**Signals**:
- `completion_ready`: Emitted when completion is ready
- `chat_response`: Emitted for chat responses
- `error_occurred`: Emitted on errors
- `status_changed`: Emitted when status changes

**Usage Example**:
```python
from src.copilot.copilot_manager import CopilotManager

manager = CopilotManager(config_manager)
manager.get_inline_completion(
    context_before="Hello",
    context_after="world",
    callback=my_callback
)
```

### 3. AgentMode (`src/copilot/agent_mode.py`)

**Purpose**: Autonomous task execution with audit workflow

**Key Classes**:
- `AgentTask`: Represents a single task
- `AgentMode`: Manages task lifecycle

**Key Methods**:
- `read_document()`: Read file content
- `edit_document()`: Edit file with AI
- `create_document()`: Create new file
- `create_branch()`: Create git branch
- `commit_changes()`: Commit to git
- `audit_task()`: Review and approve/reject

**Task Lifecycle**:
```
pending → in_progress → completed → auditing → approved/rejected
```

### 4. CopilotPanel (`src/components/copilot_panel.py`)

**Purpose**: UI components for copilot features

**Key Widgets**:
- `CopilotPanel`: Main panel widget
- `CopilotSettingsDialog`: Settings dialog
- `TaskAuditDialog`: Task audit dialog

## Adding a New Copilot Mode

To add a new mode (e.g., "Summary Mode"):

### Step 1: Add to CopilotManager

```python
# In copilot_manager.py

def summarize_text(
    self,
    text: str,
    style: str = "concise",
    callback: Optional[Callable] = None
):
    """Summarize text in given style"""
    if not self.is_enabled():
        warning("Copilot is not enabled")
        return
        
    self.current_mode = 'summary'
    self.status_changed.emit("Summarizing...")
    
    thread = SummaryThread(self.client, text, style)
    thread.summary_ready.connect(self._on_summary_ready)
    thread.error_occurred.connect(self._on_error)
    
    if callback:
        thread.summary_ready.connect(callback)
        
    thread.start()

def _on_summary_ready(self, summary: str):
    """Handle summary ready"""
    self.completion_ready.emit(summary)
    self.status_changed.emit("Summary ready")
    self.current_mode = 'none'
```

### Step 2: Create Thread Class

```python
# In copilot_manager.py

class SummaryThread(QThread):
    """Thread for summarizing text"""
    
    summary_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, client: SiliconFlowClient, text: str, style: str):
        super().__init__()
        self.client = client
        self.text = text
        self.style = style
        
    def run(self):
        try:
            prompt = f"""Summarize the following text in a {self.style} style:

{self.text}

Summary:"""

            messages = [{'role': 'user', 'content': prompt}]
            response = self.client.chat_completion(messages, temperature=0.3)
            
            if 'choices' in response and len(response['choices']) > 0:
                summary = response['choices'][0]['message']['content'].strip()
                self.summary_ready.emit(summary)
            else:
                self.error_occurred.emit("No summary generated")
        except Exception as e:
            self.error_occurred.emit(str(e))
```

### Step 3: Add UI to CopilotPanel

```python
# In copilot_panel.py

def _create_summary_widget(self) -> QWidget:
    """Create summary mode widget"""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # Text input
    layout.addWidget(BodyLabel("文本:"))
    self.summary_text = TextEdit()
    layout.addWidget(self.summary_text)
    
    # Style selector
    style_layout = QHBoxLayout()
    style_layout.addWidget(BodyLabel("风格:"))
    self.summary_style = ComboBox()
    self.summary_style.addItems(["简洁", "详细", "要点"])
    style_layout.addWidget(self.summary_style)
    layout.addLayout(style_layout)
    
    # Summarize button
    summarize_btn = PushButton("生成摘要")
    summarize_btn.clicked.connect(self._on_summarize)
    layout.addWidget(summarize_btn)
    
    return widget

def _on_summarize(self):
    """Handle summarize request"""
    text = self.summary_text.toPlainText().strip()
    style = self.summary_style.currentText()
    
    if not text:
        QMessageBox.warning(self, "输入错误", "请输入要摘要的文本")
        return
        
    self.summary_requested.emit(text, style)
```

### Step 4: Integrate in Main Window

```python
# In main_window.py

def _connect_copilot_signals(self):
    """Connect copilot signals"""
    # ... existing connections ...
    
    # Add summary connection
    self.copilotPanel.summary_requested.connect(
        lambda text, style: self.copilotManager.summarize_text(
            text, style, self._on_summary_ready
        )
    )

def _on_summary_ready(self, summary: str):
    """Handle summary ready"""
    self.copilotPanel.display_summary_result(summary)
```

## Modifying Prompts

All AI prompts are currently in the code. To modify them:

### Inline Completion Prompt
Location: `copilot_manager.py` → `CompletionThread.run()`

### Edit Prompt
Location: `copilot_manager.py` → `EditThread.run()`

### Creation Prompt
Location: `copilot_manager.py` → `CreationThread.run()`

### Agent Prompts
Location: `agent_mode.py` → `TaskExecutionThread._execute_*()`

**Best Practice**: Extract prompts to a separate configuration file or constants module.

## Testing

### Unit Tests

Create tests in `tests/test_copilot.py`:

```python
import unittest
from src.copilot.siliconflow_client import SiliconFlowClient

class TestSiliconFlowClient(unittest.TestCase):
    def test_initialization(self):
        client = SiliconFlowClient("test_key")
        self.assertEqual(client.api_key, "test_key")
        self.assertIsNotNone(client.model)
        
    def test_headers(self):
        client = SiliconFlowClient("test_key")
        self.assertIn('Authorization', client.headers)
        self.assertEqual(
            client.headers['Authorization'],
            'Bearer test_key'
        )
```

### Integration Tests

Test with mock API responses:

```python
from unittest.mock import Mock, patch

class TestCopilotManager(unittest.TestCase):
    @patch('src.copilot.siliconflow_client.requests.post')
    def test_completion(self, mock_post):
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'choices': [{'message': {'content': 'Test completion'}}]
        }
        mock_post.return_value = mock_response
        
        # Test completion
        manager = CopilotManager(mock_config)
        # ... test logic ...
```

## Error Handling

### API Errors

Handle in `SiliconFlowClient`:
```python
try:
    response = requests.post(url, headers=self.headers, json=data)
    response.raise_for_status()
    return response.json()
except requests.exceptions.RequestException as e:
    error(f"API error: {str(e)}")
    raise
```

### Task Errors

Handle in `AgentMode`:
```python
try:
    result = self._execute_task()
    self.task_completed.emit(task_id, result)
except Exception as e:
    self.task_failed.emit(task_id, str(e))
```

## Performance Optimization

### 1. Caching

Cache frequently used completions:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_completion(self, prompt: str) -> str:
    return self.client.text_completion(prompt)
```

### 2. Streaming Responses

For long generations, use streaming:
```python
for chunk in client._stream_chat_completion(url, data):
    self.partial_response.emit(chunk)
```

### 3. Request Batching

Batch multiple requests when possible:
```python
def batch_completions(self, prompts: List[str]) -> List[str]:
    # Send multiple prompts in one request
    pass
```

## Security Considerations

### API Key Storage

- Never hardcode API keys
- Store encrypted in config
- Use environment variables for sensitive deployments

### Input Validation

```python
def sanitize_input(text: str) -> str:
    """Sanitize user input before sending to API"""
    # Remove sensitive patterns
    # Limit length
    # Escape special characters
    return text
```

### Rate Limiting

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, max_requests: int, time_window: int):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        
    def can_proceed(self) -> bool:
        now = time.time()
        # Remove old requests
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
```

## Debugging

### Enable Debug Logging

```python
from src.utils.logger import debug

# In copilot modules
debug(f"Request: {messages}")
debug(f"Response: {response}")
```

### Network Inspection

Use `requests_toolbelt` for detailed HTTP logging:
```python
from requests_toolbelt.utils import dump

response = requests.post(...)
print(dump.dump_all(response).decode('utf-8'))
```

## Contributing

When contributing copilot features:

1. Follow existing code style
2. Add comprehensive docstrings
3. Include error handling
4. Write tests
5. Update documentation
6. Test with actual API

## Resources

- [SiliconFlow API Docs](https://docs.siliconflow.cn)
- [PyQt5 Documentation](https://doc.qt.io/qtforpython/)
- [MGit Architecture](../docs/)

## Future Improvements

Planned enhancements:
- [ ] Streaming responses for real-time feedback
- [ ] Context window management
- [ ] Custom prompt templates
- [ ] Model fine-tuning support
- [ ] Multi-modal support (images, etc.)
- [ ] Collaborative editing features
- [ ] Usage analytics and optimization

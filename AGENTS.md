# AGENTS.md - Playwright Automation Testing Project

## Project Overview

This is a Python-based Playwright automation testing harness for Web App system. Tests are defined in YAML format and executed via the `ScenarioExecutor` class.

**Primary Language:** Python 3  
**Test Framework:** pytest + playwright  
**Configuration Format:** YAML

---

## Build/Lint/Test Commands

### Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or: .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### Running Tests

```bash
# Run all test scenarios
python scenario_executor.py

# Run a specific scenario
python scenario_executor.py inventory_check_query

# Run with pytest (for pytest-based tests)
pytest

# Run specific test file with pytest
pytest tests/test_example.py

# Run with verbose output
pytest -v

# Run specific test by name
pytest -k "test_name"

# Run with Playwright headed mode (visible browser)
pytest --headed

# Run specific browser
pytest --browser chromium
pytest --browser firefox
pytest --browser webkit
```

### Linting

```bash
# Using flake8 (recommended)
pip install flake8
flake8 . --max-line-length=120 --exclude=.venv,__pycache__,.git

# Using ruff (faster alternative)
pip install ruff
ruff check .

# Format with black
pip install black
black .
```

### Type Checking

```bash
pip install mypy
mypy scenario_executor.py --ignore-missing-imports
```

---

## Project Structure

```
playwright-auto/
├── scenario_executor.py    # Main executor - parses YAML and runs scenarios (with assertions)
├── test_scenarios.yaml     # Test scenario definitions (with assertions support)
├── requirements.txt        # Python dependencies
├── specs/                  # Feature specifications
│   └── assertion_spec.md   # Assertion feature spec
├── tests/                  # Unit tests
│   └── test_assertions.py  # Assertion functionality tests
├── screenshots/            # Test screenshots (created at runtime)
├── .env                    # Environment variables (URL, USERNAME, PASSWORD)
└── .gitignore
```

---

## Code Style Guidelines

### Imports

```python
# Standard library first
import os
import time
from pickle import TRUE  # Note: This is legacy, avoid using pickle

# Third-party next
import yaml
from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv

# Local imports last (none currently)
```

### Naming Conventions

- **Files:** `snake_case.py` (e.g., `scenario_executor.py`)
- **Classes:** `PascalCase` (e.g., `ScenarioExecutor`)
- **Functions/Methods:** `snake_case` (e.g., `execute_action`, `run_scenario`)
- **Private methods:** `_leading_underscore` (e.g., `_do_login`, `_do_click`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `URL`, `USERNAME`, `PASSWORD`)
- **YAML keys:** `snake_case` (e.g., `inventory_check_query`)

### Type Annotations

```python
# Use type hints for function parameters and return types
def execute_action(self, action: dict, step_num: int = 0, total_steps: int = 0):
    ...

def load_scenarios(self, yaml_file: str) -> dict:
    ...

def _do_click(self, selector: str, iframe: str = None, exact: bool = True) -> bool:
    ...
```

### Error Handling

```python
# Use try/except for expected failures with specific error messages
try:
    self.page.locator('.verify-code-img').screenshot(path=captcha_path)
except:
    pass  # Silently ignore if captcha not found

# For test assertions, provide clear error context
try:
    success = self.execute_action(step, i, total_steps)
    if not success:
        print(f"\n    ❌ 步骤 {i} 执行失败")
        self.page.screenshot(path=f"error_step_{i}.png")
        return False
except Exception as e:
    print(f"\n    ❌ 步骤 {i} 异常: {e}")
    self.page.screenshot(path=f"error_step_{i}.png")
    return False
```

### Documentation

```python
def _do_click(self, selector: str, iframe: str = None, exact: bool = True) -> bool:
    """执行点击
    
    Args:
        selector: 元素选择器
        iframe: iframe选择器，如 "iframe#WrhContent"
        exact: 是否精确匹配文本
    
    Returns:
        bool: 操作是否成功
    """
```

---

## Key Patterns and Conventions

### YAML Scenario Structure

```yaml
scenarios:
  scenario_id:
    name: "场景名称"
    description: "场景描述"
    steps:
      - action: login | navigate | click | fill | screenshot | wait | switch_frame
        description: "步骤描述"
        # Action-specific parameters
        selector: "button:has-text('查询')"  # For click/fill
        iframe: "#WrhContent"                 # Optional iframe context
        value: "填写内容"                      # For fill action
        path: ["库存", "盘点", "盘点单"]      # For navigate
        filename: "screenshot.png"           # For screenshot
        seconds: 1                           # For wait
        exact: true                          # For click (text matching)
        
        # Assertions (executed after step completion)
        assertions:
          - type: element_visible
            selector: ".grid-row"
            message: "应显示数据表格"
          - type: text_contains
            selector: ".grid-toolbar"
            value: "单据总数"
            message: "应显示单据统计信息"
          - type: url_contains
            value: "newframe.html"
            message: "应跳转到正确页面"
```

### Playwright Selectors

```python
# Text-based selectors
"button:has-text('查询')"
"text=登录"

# CSS selectors
"input[placeholder='手机号/用户名']"
".grid-row"
"#WrhContent"

# Combined selectors
"button:has-text('查询')"

# iframe handling
iframe: "#WrhContent"  # Use frame_locator for iframe content
```

### iframe Handling Pattern

```python
# Wait for iframe to load
self.page.wait_for_selector(selector=iframe, timeout=30000)

# Interact with elements inside iframe
self.page.frame_locator(selector=iframe).get_by_text(text=selector, exact=exact).click()
self.page.frame_locator(iframe).locator(selector).fill(value)
```

---

## Environment Configuration

Create a `.env` file in the project root:

```env
URL=https://your-app-url.com
USERNAME=your_username
PASSWORD=your_password
```

**Never commit `.env` file to version control.**

---

## Testing Best Practices

1. **Screenshot on failure:** Always capture screenshots when tests fail
2. **Wait strategies:** Use `wait_for_selector`, `wait_for_load_state` instead of fixed `time.sleep()`
3. **Descriptive steps:** Add `description` to each step for better logging
4. **Cleanup:** Use `finally` blocks to ensure browser cleanup

---

## Development Notes

- The project uses Chinese comments and print statements - maintain this pattern for consistency
- Emoji icons are used in console output (✅, ❌, 📍, 🖱️, etc.) - maintain this style
- The `ScenarioExecutor` class includes comprehensive assertion functionality:
  - 6 standard assertion types (url_contains, element_visible, element_hidden, text_contains, text_equals, count_greater)
  - Support for multiple assertions per step
  - Automatic screenshot on assertion failure
  - Detailed assertion result logging
  - iframe support for all assertion types
- Consider using pytest fixtures for browser setup/teardown in future test files
# Scenario Executor 功能规格说明书

## 1. 概述

`scenario_executor.py` 是一个基于 Playwright 的自动化测试场景执行器，用于解析 YAML 格式的测试场景配置并自动执行测试步骤。

### 1.1 核心功能
- 从 YAML 文件加载测试场景配置
- 支持多种预定义动作类型（登录、导航、点击、填写、截图等）
- 自动处理 iframe 上下文切换
- 提供详细的执行日志和错误报告
- 支持单个场景执行或批量场景执行

### 1.2 技术栈
- **Python 3** - 主要编程语言
- **Playwright** - 浏览器自动化框架
- **PyYAML** - YAML 配置文件解析
- **python-dotenv** - 环境变量管理

---

## 2. 架构设计

### 2.1 类结构

```
ScenarioExecutor
├── __init__(page: Page)
├── load_scenarios(yaml_file: str) -> dict
├── execute_action(action: dict, step_num: int, total_steps: int)
├── run_scenario(scenario_id: str, yaml_file: str) -> bool
├── run_all_scenarios(yaml_file: str)
└── 私有方法
    ├── _print_step_header(...)
    ├── _do_login() -> bool
    ├── _do_navigate(path: list) -> bool
    ├── _do_click(selector, iframe, exact) -> bool
    ├── _do_fill(selector, value, iframe) -> bool
    ├── _do_switch_frame(iframe) -> bool
    ├── _do_screenshot(filename) -> bool
    └── _do_wait(seconds) -> bool
```

### 2.2 依赖关系

```
scenario_executor.py
├── playwright.sync_api (Page, sync_playwright)
├── yaml (PyYAML)
├── os (环境变量)
├── time (延时等待)
└── dotenv (load_dotenv)
```

---

## 3. 功能模块详解

### 3.1 初始化与配置

#### `__init__(self, page: Page)`
初始化场景执行器实例。

**参数：**
- `page`: Playwright Page 对象

**属性：**
- `self.page`: 当前页面实例
- `self.results`: 执行结果列表

#### 环境配置
通过 `.env` 文件加载以下环境变量：
- `URL`: 应用基础 URL
- `USERNAME`: 登录用户名
- `PASSWORD`: 登录密码
- `HEADED`: 浏览器模式（可选，默认 `true`）
  - `true`: 有头模式（显示浏览器窗口）
  - `false`: 无头模式（后台运行，不显示界面）
- `BROWSER`: 浏览器类型（可选，默认 `chromium`）
  - `chromium`: Chrome/Edge 内核
  - `firefox`: Firefox 浏览器
  - `webkit`: Safari 浏览器内核
- `SCREENSHOT_DIR`: 截图保存目录（可选，默认 `screenshots`）
  - 指定相对路径或绝对路径
  - 目录不存在时会自动创建

---

### 3.2 场景加载

#### `load_scenarios(self, yaml_file: str) -> dict`
从 YAML 文件加载测试场景配置。

**参数：**
- `yaml_file`: YAML 配置文件路径

**返回：**
- 包含所有场景配置的字典

**示例：**
```python
config = executor.load_scenarios("test_scenarios.yaml")
```

---

### 3.3 动作执行引擎

#### `execute_action(self, action: dict, step_num: int = 0, total_steps: int = 0)`
执行单个测试动作的核心方法。

**参数：**
- `action`: 动作配置字典，包含：
  - `action`: 动作类型（login/navigate/click/fill/screenshot/wait/switch_frame）
  - `description`: 步骤描述
  - `selector`: 元素选择器（可选）
  - `iframe`: iframe 选择器（可选）
  - `value`: 填写值（fill 动作使用）
  - `filename`: 截图文件名（screenshot 动作使用）
  - `seconds`: 等待秒数（wait 动作使用）
  - `path`: 导航路径列表（navigate 动作使用）
  - `exact`: 是否精确匹配文本（click 动作使用，默认 True）
- `step_num`: 当前步骤序号（用于日志输出）
- `total_steps`: 总步骤数（用于日志输出）

**返回：**
- `bool`: 动作执行是否成功

**支持的动作类型：**

| 动作类型 | 描述 | 必需参数 | 可选参数 |
|---------|------|---------|---------|
| `login` | 执行系统登录 | 无 | 无 |
| `navigate` | 菜单导航 | `path` (列表) | 无 |
| `click` | 点击元素 | `selector` | `iframe`, `exact` |
| `fill` | 填写表单 | `selector`, `value` | `iframe` |
| `screenshot` | 页面截图 | `filename` | 无 |
| `wait` | 延时等待 | `seconds` | 无 |
| `switch_frame` | 切换 iframe | `iframe` | 无 |

---

### 3.4 内置动作实现

#### 3.4.1 登录动作 `_do_login() -> bool`
执行系统登录流程。

**执行步骤：**
1. 导航到登录页面 (`/www/view/entry3.html`)
2. 等待网络空闲
3. 填写用户名和密码
4. 截取验证码图片（如果存在）
5. 等待用户输入验证码
6. 填写验证码并提交
7. 等待跳转到主框架页面

**特点：**
- 自动识别并保存验证码截图
- 支持人工输入验证码
- 等待 URL 变化确认登录成功

---

#### 3.4.2 导航动作 `_do_navigate(path: list) -> bool`
执行菜单导航操作。

**参数：**
- `path`: 菜单点击路径列表，如 `["库存", "盘点", "盘点单"]`

**执行逻辑：**
```python
for item in path:
    self.page.click(f"text={item}")
    time.sleep(0.5)  # 等待菜单动画
```

---

#### 3.4.3 点击动作 `_do_click(selector, iframe, exact) -> bool`
执行元素点击操作。

**参数：**
- `selector`: 元素选择器（CSS 选择器或文本）
- `iframe`: iframe 选择器（可选）
- `exact`: 是否精确匹配文本（默认 True）

**iframe 处理：**
- 如果在 iframe 中操作，先等待 iframe 加载完成
- 使用 `frame_locator()` 定位到 iframe 内容
- 支持 `get_by_text()` 和 `locator()` 两种方式

**示例：**
```python
# 主页面点击
_do_click("button:has-text('查询')")

# iframe 内点击
_do_click("保存", iframe="#WrhContent", exact=True)
```

---

#### 3.4.4 填写动作 `_do_fill(selector, value, iframe) -> bool`
执行表单填写操作。

**参数：**
- `selector`: 输入框选择器
- `value`: 要填写的值
- `iframe`: iframe 选择器（可选）

**特点：**
- 自动等待 iframe 和输入框可用（超时 10 秒）
- 支持在 iframe 内的表单填写

---

#### 3.4.5 截图动作 `_do_screenshot(filename) -> bool`
执行页面截图。

**参数：**
- `filename`: 截图文件名

**保存路径：**
```
screenshots/{timestamp}_{filename}
```
其中 `timestamp` 格式为 `YYYYMMDD_HHMMSS`

**自动创建目录：**
- 如果 `screenshots/` 目录不存在会自动创建

---

#### 3.4.6 等待动作 `_do_wait(seconds) -> bool`
执行同步等待。

**参数：**
- `seconds`: 等待秒数（默认 1 秒）

**注意：**
- 使用 `time.sleep()` 实现阻塞式等待
- 建议优先使用 Playwright 的异步等待方法

---

#### 3.4.7 切换帧动作 `_do_switch_frame(iframe) -> bool`
切换到指定的 iframe 上下文。

**参数：**
- `iframe`: iframe 选择器

**验证：**
- 等待 iframe 元素出现（超时 30 秒）
- 确保后续操作在正确的 iframe 上下文中执行

---

### 3.5 场景执行

#### `run_scenario(self, scenario_id: str, yaml_file: str) -> bool`
运行指定的测试场景。

**参数：**
- `scenario_id`: 场景 ID（YAML 中的键名）
- `yaml_file`: YAML 配置文件路径

**执行流程：**
1. 加载 YAML 配置
2. 查找对应场景
3. 打印场景信息（名称、描述）
4. 按顺序执行所有步骤
5. 错误处理：
   - 步骤失败时截图保存为 `error_step_{i}.png`
   - 打印错误信息
   - 立即终止场景执行
6. 返回执行结果（True/False）

**日志输出：**
```
============================================================
🚀 开始执行场景：场景名称
📝 场景描述：场景描述
============================================================

📋 共 X 个步骤待执行

  📍 步骤 1/X: [LOGIN]
     ✅ 步骤完成
  
  📍 步骤 2/X: [NAVIGATE]
     🧭 导航路径：库存 -> 盘点 -> 盘点单
     ✅ 步骤完成
...
```

---

#### `run_all_scenarios(self, yaml_file: str)`
运行 YAML 文件中的所有场景。

**执行流程：**
1. 加载所有场景配置
2. 依次执行每个场景
3. 场景间暂停 6 秒（避免操作过快）
4. 统计并输出汇总结果

**汇总输出：**
```
============================================================
📊 执行结果汇总
============================================================
  ✅ 通过 [scenario_1] 场景 1 名称
  ❌ 失败 [scenario_2] 场景 2 名称

总计：X 通过，Y 失败，Z 个场景
```

---

### 3.6 辅助方法

#### `_print_step_header(...)`
打印步骤执行信息的头部。

**输出格式：**
```
  📍 步骤 1/5: [CLICK] [iframe: #WrhContent]
     📝 点击查询按钮提交表单
```

**包含信息：**
- 步骤序号和总步骤数
- 动作类型（大写）
- iframe 上下文（如果有）
- 步骤描述

---

## 4. YAML 配置格式

### 4.1 完整示例

```yaml
scenarios:
  inventory_check_query:
    name: "库存查询场景"
    description: "验证库存查询功能正常工作"
    steps:
      - action: login
        description: "登录系统"
      
      - action: navigate
        description: "导航到库存查询页面"
        path: ["库存", "查询", "库存查询"]
      
      - action: click
        description: "打开查询条件面板"
        selector: "button:has-text('查询条件')"
        iframe: "#WrhContent"
      
      - action: fill
        description: "填写仓库编码"
        selector: "input[name='warehouse']"
        value: "WH001"
        iframe: "#WrhContent"
      
      - action: click
        description: "点击查询按钮"
        selector: "button:has-text('查询')"
        iframe: "#WrhContent"
        exact: true
      
      - action: screenshot
        description: "截图保存查询结果"
        filename: "inventory_result.png"
      
      - action: wait
        description: "等待数据加载"
        seconds: 2
```

### 4.2 动作参数详解

#### login 动作
```yaml
- action: login
  description: "登录系统"
```
无需额外参数，自动从环境变量读取凭证。

---

#### navigate 动作
```yaml
- action: navigate
  description: "导航到目标页面"
  path: ["一级菜单", "二级菜单", "三级菜单"]
```
`path`: 必须，菜单点击顺序列表。

---

#### click 动作
```yaml
- action: click
  description: "点击按钮"
  selector: "button:has-text('查询')"
  iframe: "#WrhContent"  # 可选
  exact: true  # 可选，默认 true
```
`selector`: 必须，元素选择器  
`iframe`: 可选，iframe 选择器  
`exact`: 可选，文本是否精确匹配

---

#### fill 动作
```yaml
- action: fill
  description: "填写表单"
  selector: "input[name='username']"
  value: "admin"
  iframe: "#WrhContent"  # 可选
```
`selector`: 必须，输入框选择器  
`value`: 必须，填写内容  
`iframe`: 可选，iframe 选择器

---

#### screenshot 动作
```yaml
- action: screenshot
  description: "页面截图"
  filename: "result.png"
```
`filename`: 必须，保存的文件名（不含路径）

---

#### wait 动作
```yaml
- action: wait
  description: "等待加载"
  seconds: 3
```
`seconds`: 必须，等待秒数

---

#### switch_frame 动作
```yaml
- action: switch_frame
  description: "切换到主框架"
  iframe: "#mainFrame"
```
`iframe`: 必须，iframe 选择器

---

## 5. 命令行接口

### 5.1 执行所有场景

```bash
python scenario_executor.py
```

执行 `test_scenarios.yaml` 中定义的所有场景。

---

### 5.2 执行指定场景

```bash
python scenario_executor.py scenario_id
```

执行指定 ID 的场景，例如：
```bash
python scenario_executor.py inventory_check_query
```

---

### 5.3 浏览器配置

#### 5.3.1 浏览器模式配置

在 `.env` 文件中配置浏览器显示模式：

```env
# 有头模式 - 显示浏览器窗口（调试推荐）
HEADED=true
```

```env
# 无头模式 - 后台运行（CI/CD 推荐）
HEADED=false
```

**使用建议：**
- **开发调试**: 使用 `HEADED=true`，便于观察执行过程
- **CI/CD**: 使用 `HEADED=false`，节省资源
- **截图调试**: 使用 `HEADED=true`，确保截图时机准确

---

#### 5.3.2 浏览器类型配置

在 `.env` 文件中配置浏览器类型：

```env
# Chromium (默认) - 推荐用于大多数场景
BROWSER=chromium
```

```env
# Firefox - 用于 Firefox 特定测试
BROWSER=firefox
```

```env
# WebKit - 用于 Safari/iOS 兼容性测试
BROWSER=webkit
```

**浏览器对比：**

| 浏览器 | 内核 | 适用场景 |
|--------|------|----------|
| Chromium | Blink | 大多数 Web 应用，Chrome/Edge 用户 |
| Firefox | Gecko | Firefox 用户，特定兼容性测试 |
| WebKit | WebKit | Safari 用户，iOS/macOS 兼容性测试 |

**注意事项：**
- 首次使用需要安装对应浏览器：`playwright install chromium firefox webkit`
- 不同浏览器的行为可能略有差异
- 建议在至少一种浏览器上验证后，再扩展到其他浏览器

---

#### 5.3.3 截图目录配置

在 `.env` 文件中配置截图保存目录：

```env
# 使用默认目录
SCREENSHOT_DIR=screenshots
```

```env
# 使用自定义相对路径
SCREENSHOT_DIR=test_results/screenshots
```

```env
# 使用绝对路径
SCREENSHOT_DIR=/tmp/test_screenshots
```

**目录规则：**
- 支持相对路径（相对于项目根目录）
- 支持绝对路径
- 目录不存在时会自动创建
- 截图文件名格式：`{SCREENSHOT_DIR}/{YYYYMMDD_HHMMSS}_{filename}`

**使用建议：**
- **日常开发**: 使用默认的 `screenshots/` 目录
- **CI/CD**: 使用统一的结果目录，如 `test_results/screenshots/`
- **多项目区分**: 使用项目名作为目录前缀，如 `project_a_screenshots/`

---

### 5.4 程序化调用

```python
from playwright.sync_api import sync_playwright
from scenario_executor import ScenarioExecutor

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    
    executor = ScenarioExecutor(page)
    
    # 执行单个场景
    executor.run_scenario("scenario_id")
    
    # 执行所有场景
    executor.run_all_scenarios()
    
    browser.close()
```

---

## 6. 错误处理

### 6.1 异常捕获
每个步骤都包含 try-except 块：

```python
try:
    success = self.execute_action(step, i, total_steps)
    if not success:
        print(f"\n    ❌ 步骤 {i} 执行失败")
        self.page.screenshot(path=f"error_step_{i}.png")
        return False
except Exception as e:
    print(f"\n    ❌ 步骤 {i} 异常：{e}")
    self.page.screenshot(path=f"error_step_{i}.png")
    return False
```

### 6.2 错误截图
- 任何步骤失败都会自动截图
- 截图保存在当前目录：`error_step_{i}.png`
- 便于问题排查和调试

### 6.3 超时处理
关键操作都设置了超时时间：
- iframe 加载：30 秒
- 元素等待：10-30 秒
- URL 跳转：30 秒

---

## 7. 日志输出规范

### 7.1 输出级别

| 级别 | 图标 | 用途 |
|-----|------|-----|
| 信息 | 📍 | 步骤开始 |
| 说明 | 📝 | 步骤描述 |
| 成功 | ✅ | 步骤完成 |
| 失败 | ❌ | 步骤失败/异常 |
| 警告 | ⚠️ | 未知动作 |
| 导航 | 🧭 | 导航路径 |
| 点击 | 🖱️ | 点击操作 |
| 填写 | ⌨️ | 填写内容 |
| 截图 | 📸 | 截图保存 |
| 等待 | ⏱️ | 等待延时 |
| 切换 | 🔄 | iframe 切换 |

### 7.2 输出示例

```
============================================================
🚀 开始执行场景：库存盘点查询
📝 场景描述：验证盘点单查询功能
============================================================

📋 共 5 个步骤待执行

  📍 步骤 1/5: [LOGIN]
     ✅ 步骤完成

  📍 步骤 2/5: [NAVIGATE]
     🧭 导航路径：库存 -> 盘点 -> 盘点单
     ✅ 步骤完成

  📍 步骤 3/5: [CLICK] [iframe: #WrhContent]
     📝 点击查询按钮
     🖱️ 点击元素：查询
        在 iframe 中：#WrhContent
        excat: True
     ✅ 步骤完成

============================================================
✅ 场景完成：库存盘点查询
============================================================
```

---

## 8. 扩展性设计

### 8.1 新增动作类型

在 `execute_action` 方法中添加新的分支：

```python
def execute_action(self, action: dict, step_num: int, total_steps: int):
    ...
    elif action_type == "new_action":
        result = self._do_new_action(action.get("param"))
    ...
```

然后实现对应的私有方法：

```python
def _do_new_action(self, param: str) -> bool:
    """新动作实现"""
    print(f"     🔧 执行新动作：{param}")
    # 实现逻辑
    return True
```

### 8.2 自定义断言（未来扩展）

可以在现有架构基础上添加断言功能：

```python
# 在 execute_action 执行后添加断言验证
if action.get("assertions"):
    for assertion in action["assertions"]:
        self._do_assertion(assertion)
```

---

## 9. 最佳实践

### 9.1 场景设计原则

1. **原子性**: 每个场景应该测试一个独立的功能点
2. **可重复性**: 场景应该可以多次重复执行
3. **自包含**: 场景之间不应该有依赖关系
4. **清晰命名**: 场景 ID 应该清晰表达测试目的

### 9.2 步骤编写建议

1. **添加描述**: 为每个步骤添加 `description` 便于日志输出
2. **合理使用等待**: 避免过长的固定等待时间
3. **截图时机**: 在关键节点添加 screenshot 步骤
4. **iframe 处理**: 明确标注每个步骤的 iframe 上下文

### 9.3 错误处理建议

1. **及时截图**: 失败时自动保存现场截图
2. **详细日志**: 输出足够的调试信息
3. **快速失败**: 遇到错误立即停止，避免级联失败

---

## 10. 限制与注意事项

### 10.1 当前限制

1. **验证码处理**: 需要人工输入验证码（已实现自动截图）
2. **同步执行**: 使用同步 API，不支持并发执行多个场景
3. **浏览器支持**: 默认使用 Chromium，可通过配置支持 Firefox/WebKit
4. **断言功能**: 暂未实现自动断言验证（见 assertion_spec.md）

### 10.2 环境要求

- Python 3.7+
- Playwright 浏览器需要预先安装：`playwright install`
- 需要有效的 `.env` 配置文件

### 10.3 性能考虑

- 场景间默认暂停 6 秒，可根据需要调整
- 截图会占用磁盘空间，建议定期清理
- 长时间运行建议使用 headed 模式便于观察

---

## 11. 版本历史

### v1.0 (当前版本)

**核心功能:**
- ✅ YAML 场景配置解析
- ✅ 7 种基础动作类型支持
- ✅ iframe 上下文处理
- ✅ 详细日志输出
- ✅ 错误截图
- ✅ 单个/批量场景执行

**已知问题:**
- 验证码需要人工介入
- 缺少自动断言功能
- 同步阻塞式执行

---

## 12. 相关文件

- `scenario_executor.py` - 主执行器实现
- `test_scenarios.yaml` - 测试场景配置
- `.env.example` - 环境变量模板
- `requirements.txt` - Python 依赖包
- `specs/assertion_spec.md` - 断言功能规格（规划中）

# Playwright Auto - 自动化测试 Harness

基于 **Playwright** 的 YAML 驱动自动化测试框架，专为 Web  系统设计。
通过简单的 YAML 配置文件即可定义和执行测试场景，无需编写复杂的代码。

## ✨ 特性

- 🚀 **YAML 驱动** - 测试场景使用 YAML 格式定义，简单易读
- 🎯 **零编码** - 无需编写代码，只需配置 YAML 即可完成测试
- 🔧 **灵活配置** - 支持多种浏览器、有头/无头模式、自定义截图目录
- 📸 **自动截图** - 失败时自动截图，便于问题排查
- 🧪 **断言验证** - 支持多种断言类型（URL、元素可见性、文本内容、元素数量等）
- 🌐 **多浏览器支持** - Chromium、Firefox、WebKit
- 📊 **详细日志** - 清晰的步骤执行日志和结果汇总
- 🔄 **iframe 支持** - 自动处理 iframe 上下文切换

## 📦 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或：.venv\Scripts\activate  # Windows

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install
```

### 2. 配置环境变量

复制环境变量模板并修改：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 应用地址
URL=https://your-app-url.com

# 登录凭证
USERNAME=your_username
PASSWORD=your_password

# 浏览器配置（可选）
HEADED=true              # true=显示浏览器，false=后台运行
BROWSER=chromium         # chromium/firefox/webkit

# 截图目录（可选）
SCREENSHOT_DIR=screenshots
```

### 3. 运行测试

```bash
# 运行所有测试场景
python scenario_executor.py

# 运行指定场景
python scenario_executor.py inventory_check_query
```

## 📖 使用指南

### YAML 场景配置

在 `test_scenarios.yaml` 中定义测试场景：

```yaml
scenarios:
  inventory_check_query:
    name: "库存查询场景"
    description: "验证库存查询功能正常工作"
    steps:
      - action: login
        description: "登录系统"
      
      - action: navigate
        description: "导航到库存页面"
        path: ["库存", "查询", "库存查询"]
      
      - action: click
        description: "点击查询按钮"
        selector: "button:has-text('查询')"
        iframe: "#WrhContent"
      
      - action: screenshot
        description: "截图保存结果"
        filename: "inventory_result.png"
```

### 支持的动作类型

| 动作 | 描述 | 参数 |
|------|------|------|
| `login` | 登录系统 | 无 |
| `navigate` | 菜单导航 | `path`: 菜单路径列表 |
| `click` | 点击元素 | `selector`: 选择器<br>`iframe`: iframe（可选）<br>`exact`: 精确匹配（可选） |
| `fill` | 填写表单 | `selector`: 选择器<br>`value`: 填写值<br>`iframe`: iframe（可选） |
| `screenshot` | 页面截图 | `filename`: 文件名 |
| `wait` | 延时等待 | `seconds`: 等待秒数 |
| `switch_frame` | 切换 iframe | `iframe`: iframe 选择器 |

### 断言功能

每个步骤后可以添加多个断言验证：

```yaml
steps:
  - action: click
    description: "点击查询按钮"
    selector: "button:has-text('查询')"
    iframe: "#WrhContent"
    assertions:
      - type: element_visible
        selector: ".grid-row"
        iframe: "#WrhContent"
        message: "查询后应显示数据表格"
      - type: text_contains
        selector: ".grid-toolbar"
        value: "单据总数"
        message: "应显示单据统计信息"
      - type: count_greater
        selector: ".grid-row"
        count: 0
        iframe: "#WrhContent"
        message: "应至少有一条数据"
```

#### 支持的断言类型

| 断言类型 | 参数 | 说明 |
|----------|------|------|
| `url_contains` | `value` | 验证 URL 包含指定字符串 |
| `element_visible` | `selector`, `iframe?` | 验证元素可见 |
| `element_hidden` | `selector`, `iframe?` | 验证元素隐藏 |
| `text_contains` | `selector`, `value`, `iframe?` | 验证元素文本包含字符串 |
| `text_equals` | `selector`, `value`, `iframe?` | 验证元素文本完全相等 |
| `count_greater` | `selector`, `count`, `iframe?` | 验证元素数量大于指定值 |

### 命令行参数

```bash
# 运行所有场景
python scenario_executor.py

# 运行指定场景
python scenario_executor.py <scenario_id>

# 示例
python scenario_executor.py inventory_check_query
```

## ⚙️ 配置选项

### 环境变量

| 变量名 | 说明 | 默认值 | 可选值 |
|--------|------|--------|--------|
| `URL` | 应用地址 | 必填 | - |
| `USERNAME` | 用户名 | 必填 | - |
| `PASSWORD` | 密码 | 必填 | - |
| `HEADED` | 浏览器模式 | `true` | `true`/`false` |
| `BROWSER` | 浏览器类型 | `chromium` | `chromium`/`firefox`/`webkit` |
| `SCREENSHOT_DIR` | 截图目录 | `screenshots` | 任意路径 |

### 浏览器模式说明

- **HEADED=true**: 显示浏览器窗口，适合开发调试
- **HEADED=false**: 后台运行，适合 CI/CD

### 浏览器类型说明

| 浏览器 | 内核 | 适用场景 |
|--------|------|----------|
| Chromium | Blink | 大多数 Web 应用（推荐） |
| Firefox | Gecko | Firefox 特定测试 |
| WebKit | WebKit | Safari/iOS兼容性测试 |

## 📁 项目结构

```
playwright-auto/
├── scenario_executor.py    # 核心执行器（包含断言功能）
├── test_scenarios.yaml     # 测试场景配置（含断言）
├── requirements.txt        # Python 依赖
├── .env                    # 环境变量（需自行创建）
├── .env.example           # 环境变量模板
├── README.md              # 项目说明
├── specs/                 # 规格说明书
│   ├── scenario_executor.md
│   └── assertion_spec.md
├── tests/                 # 单元测试
│   └── test_assertions.py # 断言功能测试
└── screenshots/           # 截图输出目录（运行时创建）
```

## 🛠️ 开发与测试

### 运行测试

```bash
# 使用 pytest 运行（如果有 pytest 测试）
pytest

# 运行特定测试文件
pytest tests/test_example.py

# 详细输出
pytest -v

# 有头模式运行
pytest --headed

# 指定浏览器
pytest --browser chromium
```

### 代码质量检查

```bash
# 使用 flake8 进行代码检查
flake8 . --max-line-length=120 --exclude=.venv,__pycache__,.git

# 使用 black 格式化代码
black .
```

## 📝 最佳实践

### 1. 场景设计原则

- ✅ **原子性**: 每个场景测试一个独立功能点
- ✅ **可重复性**: 场景可以多次重复执行
- ✅ **自包含**: 场景之间无依赖关系
- ✅ **清晰命名**: 场景 ID 清晰表达测试目的

### 2. 步骤编写建议

- 为每个步骤添加 `description` 便于日志输出
- 合理使用等待时间，避免过长的固定等待
- 在关键节点添加 screenshot 步骤
- 明确标注每个步骤的 iframe 上下文

### 3. 错误处理

- 失败时自动截图保存到 `error_step_{i}.png`
- 查看详细的步骤执行日志定位问题
- 使用有头模式观察执行过程

## 📚 文档

- [Scenario Executor 规格说明书](specs/scenario_executor.md) - 详细的功能说明和 API 文档
- [断言功能规格](specs/assertion_spec.md) - 断言功能设计文档

## 参考：

- [Playwright - Python](https://playwright.dev/python/docs/intro)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License



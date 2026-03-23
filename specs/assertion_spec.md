## 需求说明

为 `test_scenarios.yaml` 中的每个 Step 添加 assertion（断言）支持，使执行时可以验证页面状态并输出结果。

## 功能要求

1. 每个步骤执行后可选择添加多个断言验证
2. 支持多种断言类型（URL、元素可见性、文本内容、元素数量等）
3. 断言失败时显示清晰的错误信息并截图
4. 执行输出中显示每个断言的通过/失败状态
5. 场景执行完成后汇总所有断言结果

## 技术方案

### 断言类型设计

| 断言类型 | 参数 | 说明 |
| --- | --- | --- |
| `url_contains` | `value` | 验证 URL 包含指定字符串 |
| `element_visible` | `selector`, `iframe?` | 验证元素可见 |
| `element_hidden` | `selector`, `iframe?` | 验证元素隐藏 |
| `text_contains` | `selector`, `value`, `iframe?` | 验证元素文本包含字符串 |
| `text_equals` | `selector`, `value`, `iframe?` | 验证元素文本完全相等 |
| `count_greater` | `selector`, `count`, `iframe?` | 验证元素数量大于指定值 |


### 代码修改

**scenario_executor.py**:

- 新增 `_do_assertions()` 方法 - 执行步骤中的所有断言
- 新增 `_assert_*()` 方法族 - 各类断言的具体实现
- 修改 `execute_action()` - 步骤执行后自动执行断言
- 修改输出格式 - 清晰展示断言结果

### YAML 配置格式

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
```

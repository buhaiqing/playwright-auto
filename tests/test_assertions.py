#!/usr/bin/env python3
"""
断言功能单元测试
测试 scenario_executor.py 中的各种断言方法
"""

import pytest
import yaml
from unittest.mock import Mock, MagicMock, patch
from playwright.sync_api import Page, Locator, FrameLocator
from scenario_executor import ScenarioExecutor


class TestAssertions:
    """断言功能测试类"""

    @pytest.fixture
    def mock_page(self):
        """创建模拟的 page 对象"""
        page = Mock(spec=Page)
        page.url = "https://example.com/newframe.html"
        return page

    @pytest.fixture
    def executor(self, mock_page):
        """创建 ScenarioExecutor 实例"""
        return ScenarioExecutor(mock_page)

    def test_assert_url_contains_success(self, executor):
        """测试 URL 包含断言 - 成功情况"""
        assertion = {
            "type": "url_contains",
            "value": "newframe",
            "message": "URL 应包含 newframe"
        }
        result = executor._assert_url_contains(assertion)
        assert result is True

    def test_assert_url_contains_failure(self, executor):
        """测试 URL 包含断言 - 失败情况"""
        assertion = {
            "type": "url_contains",
            "value": "login",
            "message": "URL 应包含 login"
        }
        result = executor._assert_url_contains(assertion)
        assert result is False

    def test_assert_element_visible_success(self, executor):
        """测试元素可见断言 - 成功情况"""
        mock_locator = Mock(spec=Locator)
        mock_locator.wait_for.return_value = None
        
        executor.page.locator.return_value = mock_locator
        
        assertion = {
            "type": "element_visible",
            "selector": ".grid-row",
            "message": "元素应可见"
        }
        result = executor._assert_element_visible(assertion)
        assert result is True
        mock_locator.wait_for.assert_called_once_with(state="visible", timeout=5000)

    def test_assert_element_visible_failure(self, executor):
        """测试元素可见断言 - 失败情况"""
        mock_locator = Mock(spec=Locator)
        mock_locator.wait_for.side_effect = Exception("Element not visible")
        
        executor.page.locator.return_value = mock_locator
        
        assertion = {
            "type": "element_visible",
            "selector": ".hidden-element",
            "message": "元素应可见"
        }
        result = executor._assert_element_visible(assertion)
        assert result is False

    def test_assert_element_hidden_success(self, executor):
        """测试元素隐藏断言 - 成功情况"""
        mock_locator = Mock(spec=Locator)
        mock_locator.wait_for.return_value = None
        
        executor.page.locator.return_value = mock_locator
        
        assertion = {
            "type": "element_hidden",
            "selector": ".loading",
            "message": "元素应隐藏"
        }
        result = executor._assert_element_hidden(assertion)
        assert result is True
        mock_locator.wait_for.assert_called_once_with(state="hidden", timeout=5000)

    def test_assert_element_hidden_failure(self, executor):
        """测试元素隐藏断言 - 失败情况"""
        mock_locator = Mock(spec=Locator)
        mock_locator.wait_for.side_effect = Exception("Element still visible")
        
        executor.page.locator.return_value = mock_locator
        
        assertion = {
            "type": "element_hidden",
            "selector": ".visible-element",
            "message": "元素应隐藏"
        }
        result = executor._assert_element_hidden(assertion)
        assert result is False

    def test_assert_text_contains_success(self, executor):
        """测试文本包含断言 - 成功情况"""
        mock_locator = Mock(spec=Locator)
        mock_locator.text_content.return_value = "这是一个测试文本"
        
        executor.page.locator.return_value = mock_locator
        
        assertion = {
            "type": "text_contains",
            "selector": ".content",
            "value": "测试",
            "message": "文本应包含'测试'"
        }
        result = executor._assert_text_contains(assertion)
        assert result is True

    def test_assert_text_contains_failure(self, executor):
        """测试文本包含断言 - 失败情况"""
        mock_locator = Mock(spec=Locator)
        mock_locator.text_content.return_value = "这是其他内容"
        
        executor.page.locator.return_value = mock_locator
        
        assertion = {
            "type": "text_contains",
            "selector": ".content",
            "value": "测试",
            "message": "文本应包含'测试'"
        }
        result = executor._assert_text_contains(assertion)
        assert result is False

    def test_assert_text_equals_success(self, executor):
        """测试文本相等断言 - 成功情况"""
        mock_locator = Mock(spec=Locator)
        mock_locator.text_content.return_value = "精确匹配文本"
        
        executor.page.locator.return_value = mock_locator
        
        assertion = {
            "type": "text_equals",
            "selector": ".title",
            "value": "精确匹配文本",
            "message": "文本应精确匹配"
        }
        result = executor._assert_text_equals(assertion)
        assert result is True

    def test_assert_text_equals_failure(self, executor):
        """测试文本相等断言 - 失败情况"""
        mock_locator = Mock(spec=Locator)
        mock_locator.text_content.return_value = "不匹配的文本"
        
        executor.page.locator.return_value = mock_locator
        
        assertion = {
            "type": "text_equals",
            "selector": ".title",
            "value": "期望的文本",
            "message": "文本应精确匹配"
        }
        result = executor._assert_text_equals(assertion)
        assert result is False

    def test_assert_count_greater_success(self, executor):
        """测试元素数量大于断言 - 成功情况"""
        mock_locator = Mock(spec=Locator)
        mock_locator.count.return_value = 5
        
        executor.page.locator.return_value = mock_locator
        
        assertion = {
            "type": "count_greater",
            "selector": ".grid-row",
            "count": 3,
            "message": "元素数量应大于 3"
        }
        result = executor._assert_count_greater(assertion)
        assert result is True

    def test_assert_count_greater_failure(self, executor):
        """测试元素数量大于断言 - 失败情况"""
        mock_locator = Mock(spec=Locator)
        mock_locator.count.return_value = 2
        
        executor.page.locator.return_value = mock_locator
        
        assertion = {
            "type": "count_greater",
            "selector": ".grid-row",
            "count": 5,
            "message": "元素数量应大于 5"
        }
        result = executor._assert_count_greater(assertion)
        assert result is False

    def test_assert_with_iframe(self, executor):
        """测试带 iframe 的断言"""
        mock_frame = Mock(spec=FrameLocator)
        mock_locator = Mock(spec=Locator)
        mock_locator.text_content.return_value = "iframe 中的文本"
        
        executor.page.frame_locator.return_value = mock_frame
        mock_frame.locator.return_value = mock_locator
        
        assertion = {
            "type": "text_contains",
            "selector": ".content",
            "value": "iframe",
            "iframe": "#WrhContent",
            "message": "iframe 中的文本应包含 iframe"
        }
        result = executor._assert_text_contains(assertion)
        assert result is True
        executor.page.frame_locator.assert_called_once_with("#WrhContent")

    def test_do_assertions_multiple(self, executor):
        """测试执行多个断言"""
        # Mock all assertion methods to return True
        with patch.object(executor, '_assert_url_contains', return_value=True), \
             patch.object(executor, '_assert_element_visible', return_value=True):
            
            assertions = [
                {
                    "type": "url_contains",
                    "value": "newframe",
                    "message": "URL 测试"
                },
                {
                    "type": "element_visible",
                    "selector": ".element",
                    "message": "元素测试"
                }
            ]
            
            result = executor._do_assertions(assertions, step_num=1)
            assert result is True
            assert len(executor.assertion_results) == 2
            assert all(a["passed"] for a in executor.assertion_results)

    def test_do_assertions_mixed_results(self, executor):
        """测试执行多个断言 - 有通过有失败"""
        with patch.object(executor, '_assert_url_contains', return_value=True), \
             patch.object(executor, '_assert_element_visible', return_value=False):
            
            assertions = [
                {
                    "type": "url_contains",
                    "value": "newframe",
                    "message": "URL 测试"
                },
                {
                    "type": "element_visible",
                    "selector": ".hidden",
                    "message": "元素测试"
                }
            ]
            
            result = executor._do_assertions(assertions, step_num=1)
            assert result is False  # 有一个失败，总体失败
            assert len(executor.assertion_results) == 2
            passed_count = sum(1 for a in executor.assertion_results if a["passed"])
            assert passed_count == 1

    def test_execute_action_with_assertions(self, executor):
        """测试步骤执行后自动执行断言"""
        action = {
            "action": "wait",
            "seconds": 0.1,
            "assertions": [
                {
                    "type": "url_contains",
                    "value": "newframe",
                    "message": "URL 验证"
                }
            ]
        }
        
        with patch.object(executor, '_do_wait', return_value=True), \
             patch.object(executor, '_do_assertions', return_value=True) as mock_do_assertions:
            
            result = executor.execute_action(action, step_num=1, total_steps=5)
            
            assert result is True
            mock_do_assertions.assert_called_once()

    def test_load_scenarios_with_assertions(self, executor, tmp_path):
        """测试加载包含断言的场景配置"""
        yaml_content = """
scenarios:
  test_scenario:
    name: "测试场景"
    description: "测试断言功能"
    steps:
      - action: click
        selector: "button"
        assertions:
          - type: element_visible
            selector: ".result"
            message: "应显示结果"
"""
        yaml_file = tmp_path / "test_scenario.yaml"
        yaml_file.write_text(yaml_content, encoding='utf-8')
        
        config = executor.load_scenarios(str(yaml_file))
        
        assert "scenarios" in config
        assert "test_scenario" in config["scenarios"]
        steps = config["scenarios"]["test_scenario"]["steps"]
        assert len(steps) == 1
        assert "assertions" in steps[0]
        assert steps[0]["assertions"][0]["type"] == "element_visible"


class TestAssertionTypes:
    """测试所有支持的断言类型"""

    @pytest.fixture
    def mock_page(self):
        page = Mock(spec=Page)
        page.url = "https://example.com/page"
        return page

    @pytest.fixture
    def executor(self, mock_page):
        return ScenarioExecutor(mock_page)

    def test_all_assertion_types_supported(self, executor):
        """测试所有断言类型都被支持"""
        supported_types = [
            "url_contains",
            "element_visible",
            "element_hidden",
            "text_contains",
            "text_equals",
            "count_greater"
        ]
        
        # 检查每个断言类型都有对应的处理方法
        for assertion_type in supported_types:
            method_name = f"_assert_{assertion_type}"
            assert hasattr(executor, method_name), f"缺少断言类型 {assertion_type} 的实现方法"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

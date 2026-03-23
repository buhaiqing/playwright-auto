#!/usr/bin/env python3
"""
YAML 测试场景执行器
自动解析 test_scenarios.yaml 并执行测试
支持每个步骤的 description 描述输出
"""

import yaml
import os
import time
import logging
from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

URL = os.getenv("URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
HEADED = os.getenv("HEADED", "true").lower() == "true"
BROWSER = os.getenv("BROWSER", "chromium").lower()
SCREENSHOT_DIR = os.getenv("SCREENSHOT_DIR", "screenshots")

# 默认超时设置（毫秒）
DEFAULT_TIMEOUT = 30000
ELEMENT_WAIT_TIMEOUT = 10000
NETWORK_WAIT_TIMEOUT = 5000


class ScenarioExecutor:
    """场景执行器"""

    def __init__(self, page: Page):
        self.page = page
        self.results = []
        self.assertion_results = []  # 存储断言结果

    def load_scenarios(self, yaml_file: str) -> dict:
        """加载YAML场景配置"""
        with open(yaml_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def execute_action(self, action: dict, step_num: int = 0, total_steps: int = 0):
        """执行单个动作

        Args:
            action: 动作配置字典
            step_num: 当前步骤序号
            total_steps: 总步骤数
        """
        action_type = action.get("action")
        description = action.get("description", "")
        iframe = action.get("iframe")  # iframe 选择器
        exact = action.get("exact", True)

        # 打印步骤信息
        self._print_step_header(step_num, total_steps, action_type, description, iframe)

        # 执行动作
        result = False
        if action_type == "login":
            result = self._do_login()
        elif action_type == "navigate":
            result = self._do_navigate(action.get("path", []))
        elif action_type == "click":
            result = self._do_click(action.get("selector"), iframe, exact)
        elif action_type == "fill":
            result = self._do_fill(action.get("selector"), action.get("value"), iframe)
        elif action_type == "screenshot":
            result = self._do_screenshot(action.get("filename"))
        elif action_type == "wait":
            result = self._do_wait(action.get("seconds", 1))
        elif action_type == "switch_frame":
            result = self._do_switch_frame(action.get("iframe"))
        else:
            logger.warning(f"未知动作：{action_type}")
            return False
        
        # 打印执行结果
        if result:
            logger.info("步骤完成")
        
        # 执行断言（如果有）
        assertions = action.get("assertions", [])
        if assertions and result:
            logger.info(f"  执行 {len(assertions)} 个断言...")
            assertion_result = self._do_assertions(assertions, step_num)
            if not assertion_result:
                logger.warning(f"  ⚠️   步骤 {step_num} 的断言失败")
        
        return result

    def _print_step_header(
        self,
        step_num: int,
        total_steps: int,
        action_type: str,
        description: str,
        iframe: str = None,
    ):
        """打印步骤标题"""
        iframe_info = f" [iframe: {iframe}]" if iframe else ""
        logger.info(f"步骤 {step_num}/{total_steps}: [{action_type.upper()}]{iframe_info}")
        if description:
            logger.info(f"  {description}")

    def _do_login(self) -> bool:
        """执行登录
            
        Returns:
            bool: 登录是否成功
        """
        # 导航到登录页
        self.page.goto(f"{URL}/www/view/entry3.html")
        self.page.wait_for_load_state("networkidle")
    
        # 填写凭证
        username_input = self.page.locator('input[placeholder="手机号/用户名"]')
        password_input = self.page.locator('input[placeholder="密码"]')
            
        username_input.wait_for(state='visible', timeout=ELEMENT_WAIT_TIMEOUT)
        username_input.fill(USERNAME)
            
        password_input.wait_for(state='visible', timeout=ELEMENT_WAIT_TIMEOUT)
        password_input.fill(PASSWORD)
    
        # 验证码处理（截图后等待人工输入）
        captcha_path = "temp_captcha.png"
        captcha_locator = self.page.locator('.verify-code-img, img[src*="captcha"]')
        try:
            captcha_locator.wait_for(state='visible', timeout=5000)
            captcha_locator.screenshot(path=captcha_path)
            logger.info(f"验证码已保存：{captcha_path}")
        except Exception:
            # 验证码可能不可见或不存在，继续流程
            pass
    
        captcha = input("     🔑 请输入验证码：")
        captcha_input = self.page.locator('input[placeholder="验证码"]')
        captcha_input.wait_for(state='visible', timeout=ELEMENT_WAIT_TIMEOUT)
        captcha_input.fill(captcha)
    
        # 点击登录并等待跳转
        login_button = self.page.locator('button:has-text("登录")')
        login_button.click()
        self.page.wait_for_url("**/newframe.html**", timeout=DEFAULT_TIMEOUT)
        return True

    def _do_navigate(self, path: list) -> bool:
        """执行导航

        Args:
            path: 导航路径列表

        Returns:
            bool: 导航是否成功
        """
        logger.info(f"导航路径：{' -> '.join(path)}")
        for item in path:
            # 使用智能等待：等待元素可见且可点击
            locator = self.page.locator(f"text={item}")
            locator.wait_for(state="visible", timeout=10000)
            locator.click()
            # 等待网络空闲或页面加载完成，替代固定等待
            try:
                self.page.wait_for_load_state("networkidle", timeout=5000)
            except:
                # 如果超时，说明没有网络请求，继续下一步
                pass
        return True

    def _do_click(self, selector: str, iframe: str = None, exact: bool = True) -> bool:
        """执行点击
        
        Args:
            selector: 元素选择器
            iframe: iframe 选择器，如 "iframe#WrhContent"
            exact: 是否精确匹配文本
            
        Returns:
            bool: 操作是否成功
        """
        if iframe:
            logger.info(f"点击元素：{selector} (iframe: {iframe}, 精确匹配：{exact})")
            
            # 智能等待 iframe 加载完成
            iframe_locator = self.page.locator(iframe)
            iframe_locator.wait_for(state='attached', timeout=30000)
            
            # 在 iframe 中查找并等待元素
            frame = self.page.frame_locator(iframe)
            element = frame.get_by_text(text=selector, exact=exact)
            element.wait_for(state='visible', timeout=10000)
            element.click()
        else:
            logger.info(f"点击元素：{selector}")
            # 智能等待元素可点击
            locator = self.page.locator(selector)
            locator.wait_for(state='visible', timeout=10000)
            locator.click()
        
        # 等待导航或网络请求完成（如果有）
        try:
            self.page.wait_for_load_state('networkidle', timeout=3000)
        except:
            pass
        
        return True

    def _do_fill(self, selector: str, value: str, iframe: str = None) -> bool:
        """执行填写
        
        Args:
            selector: 元素选择器
            value: 填写值
            iframe: iframe 选择器
            
        Returns:
            bool: 操作是否成功
        """
        if iframe:
            logger.info(f"填写内容：{selector} = {value} (iframe: {iframe})")
            
            # 智能等待 iframe 和输入框
            iframe_locator = self.page.locator(iframe)
            iframe_locator.wait_for(state='attached', timeout=10000)
            
            frame = self.page.frame_locator(iframe)
            input_element = frame.locator(selector)
            input_element.wait_for(state='visible', timeout=10000)
            
            # 清空并填写
            input_element.clear()
            input_element.fill(value)
        else:
            logger.info(f"填写内容：{selector} = {value}")
            # 智能等待输入框
            locator = self.page.locator(selector)
            locator.wait_for(state='visible', timeout=10000)
            locator.clear()
            locator.fill(value)
        return True

    def _do_switch_frame(self, iframe: str) -> bool:
        """切换 iframe 上下文

        Args:
            iframe: iframe 选择器

        Returns:
            bool: 操作是否成功
        """
        logger.info(f"切换到 iframe: {iframe}")
        # 智能等待 iframe 附加到 DOM
        iframe_locator = self.page.locator(iframe)
        iframe_locator.wait_for(state="attached", timeout=30000)
        # 进一步等待 iframe 内容加载完成
        try:
            iframe_locator.wait_for(state="visible", timeout=5000)
        except:
            pass
        return True

    def _do_screenshot(self, filename: str) -> bool:
        """执行截图"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filepath = f"{SCREENSHOT_DIR}/{timestamp}_{filename}"
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        self.page.screenshot(path=filepath)
        logger.info(f"截图保存：{filepath}")
        return True

    def _do_wait(self, seconds: int) -> bool:
        """执行等待

        注意：仅在必要时使用固定等待，优先使用智能等待

        Args:
            seconds: 等待秒数

        Returns:
            bool: 操作是否成功
        """
        logger.info(f"等待 {seconds} 秒...")
        time.sleep(seconds)
        return True

    def _do_assertions(self, assertions: list, step_num: int) -> bool:
        """执行步骤的所有断言
        
        Args:
            assertions: 断言配置列表
            step_num: 当前步骤序号
            
        Returns:
            bool: 所有断言是否通过
        """
        all_passed = True
        for i, assertion in enumerate(assertions, 1):
            assertion_type = assertion.get("type")
            message = assertion.get("message", f"断言 {i}")
            
            logger.info(f"    📍 断言 {i}: {message}")
            
            try:
                if assertion_type == "url_contains":
                    passed = self._assert_url_contains(assertion)
                elif assertion_type == "element_visible":
                    passed = self._assert_element_visible(assertion)
                elif assertion_type == "element_hidden":
                    passed = self._assert_element_hidden(assertion)
                elif assertion_type == "text_contains":
                    passed = self._assert_text_contains(assertion)
                elif assertion_type == "text_equals":
                    passed = self._assert_text_equals(assertion)
                elif assertion_type == "count_greater":
                    passed = self._assert_count_greater(assertion)
                # 向后兼容旧的断言类型
                elif assertion_type == "text":
                    passed = self._assert_text(assertion.get("selector"), assertion.get("expected"), assertion.get("iframe"))
                elif assertion_type == "visible":
                    passed = self._assert_visible(assertion.get("selector"), assertion.get("iframe"))
                elif assertion_type == "hidden":
                    passed = self._assert_hidden(assertion.get("selector"), assertion.get("iframe"))
                else:
                    logger.warning(f"      ⚠️  未知断言类型：{assertion_type}")
                    passed = False
                
                # 记录断言结果
                self.assertion_results.append({
                    "step": step_num,
                    "type": assertion_type,
                    "message": message,
                    "passed": passed
                })
                
                if passed:
                    logger.info(f"      ✅ 通过")
                else:
                    logger.error(f"      ❌ 失败")
                    all_passed = False
                    # 断言失败时截图
                    error_screenshot = f"assertion_step_{step_num}_assert_{i}.png"
                    self.page.screenshot(path=error_screenshot)
                    logger.error(f"      错误截图已保存：{error_screenshot}")
                    
            except Exception as e:
                logger.error(f"      ❌ 异常：{e}")
                self.assertion_results.append({
                    "step": step_num,
                    "type": assertion_type,
                    "message": message,
                    "passed": False,
                    "error": str(e)
                })
                all_passed = False
                # 断言异常时截图
                error_screenshot = f"assertion_step_{step_num}_assert_{i}_error.png"
                self.page.screenshot(path=error_screenshot)
                logger.error(f"      错误截图已保存：{error_screenshot}")
        
        return all_passed

    def _assert_text(self, selector: str, expected: str, iframe: str = None) -> bool:
        """断言文本内容

        Args:
            selector: 元素选择器
            expected: 期望的文本内容
            iframe: iframe 选择器

        Returns:
            bool: 断言是否通过
        """
        if iframe:
            frame = self.page.frame_locator(iframe)
            element = frame.locator(selector)
        else:
            element = self.page.locator(selector)

        try:
            element.wait_for(state='visible', timeout=ELEMENT_WAIT_TIMEOUT)
            actual = element.text_content()
            return actual == expected
        except Exception:
            return False

    def _assert_visible(self, selector: str, iframe: str = None) -> bool:
        """断言元素可见

        Args:
            selector: 元素选择器
            iframe: iframe 选择器

        Returns:
            bool: 断言是否通过
        """
        if iframe:
            frame = self.page.frame_locator(iframe)
            element = frame.locator(selector)
        else:
            element = self.page.locator(selector)

        try:
            element.wait_for(state='visible', timeout=ELEMENT_WAIT_TIMEOUT)
            return True
        except Exception:
            return False

    def _assert_hidden(self, selector: str, iframe: str = None) -> bool:
        """断言元素不可见

        Args:
            selector: 元素选择器
            iframe: iframe 选择器

        Returns:
            bool: 断言是否通过
        """
        if iframe:
            frame = self.page.frame_locator(iframe)
            element = frame.locator(selector)
        else:
            element = self.page.locator(selector)

        try:
            element.wait_for(state='hidden', timeout=ELEMENT_WAIT_TIMEOUT)
            return True
        except Exception:
            return False


    def _assert_url_contains(self, assertion: dict) -> bool:
        """断言 URL 包含指定字符串
        
        Args:
            assertion: 断言配置，包含 value 字段
            
        Returns:
            bool: 断言是否通过
        """
        expected = assertion.get("value", "")
        current_url = self.page.url
        passed = expected in current_url
        logger.info(f"      URL: {current_url}")
        logger.info(f"      期望包含：{expected}")
        return passed

    def _assert_element_visible(self, assertion: dict) -> bool:
        """断言元素可见
        
        Args:
            assertion: 断言配置，包含 selector 和可选的 iframe 字段
            
        Returns:
            bool: 断言是否通过
        """
        selector = assertion.get("selector")
        iframe = assertion.get("iframe")
        
        if iframe:
            frame = self.page.frame_locator(iframe)
            locator = frame.locator(selector)
        else:
            locator = self.page.locator(selector)
        
        try:
            locator.wait_for(state="visible", timeout=5000)
            return True
        except:
            return False

    def _assert_element_hidden(self, assertion: dict) -> bool:
        """断言元素隐藏
        
        Args:
            assertion: 断言配置，包含 selector 和可选的 iframe 字段
            
        Returns:
            bool: 断言是否通过
        """
        selector = assertion.get("selector")
        iframe = assertion.get("iframe")
        
        if iframe:
            frame = self.page.frame_locator(iframe)
            locator = frame.locator(selector)
        else:
            locator = self.page.locator(selector)
        
        try:
            locator.wait_for(state="hidden", timeout=5000)
            return True
        except:
            return False

    def _assert_text_contains(self, assertion: dict) -> bool:
        """断言元素文本包含指定字符串
        
        Args:
            assertion: 断言配置，包含 selector、value 和可选的 iframe 字段
            
        Returns:
            bool: 断言是否通过
        """
        selector = assertion.get("selector")
        expected = assertion.get("value", "")
        iframe = assertion.get("iframe")
        
        if iframe:
            frame = self.page.frame_locator(iframe)
            locator = frame.locator(selector)
        else:
            locator = self.page.locator(selector)
        
        try:
            actual_text = locator.text_content(timeout=5000)
            passed = expected in actual_text
            logger.info(f"      实际文本：{actual_text[:100]}...")
            logger.info(f"      期望包含：{expected}")
            return passed
        except:
            return False

    def _assert_text_equals(self, assertion: dict) -> bool:
        """断言元素文本完全相等
        
        Args:
            assertion: 断言配置，包含 selector、value 和可选的 iframe 字段
            
        Returns:
            bool: 断言是否通过
        """
        selector = assertion.get("selector")
        expected = assertion.get("value", "")
        iframe = assertion.get("iframe")
        
        if iframe:
            frame = self.page.frame_locator(iframe)
            locator = frame.locator(selector)
        else:
            locator = self.page.locator(selector)
        
        try:
            actual_text = locator.text_content(timeout=5000)
            passed = actual_text.strip() == expected
            logger.info(f"      实际文本：{actual_text[:100]}...")
            logger.info(f"      期望等于：{expected}")
            return passed
        except:
            return False

    def _assert_count_greater(self, assertion: dict) -> bool:
        """断言元素数量大于指定值
        
        Args:
            assertion: 断言配置，包含 selector、count 和可选的 iframe 字段
            
        Returns:
            bool: 断言是否通过
        """
        selector = assertion.get("selector")
        expected_count = assertion.get("count", 0)
        iframe = assertion.get("iframe")
        
        if iframe:
            frame = self.page.frame_locator(iframe)
            locator = frame.locator(selector)
        else:
            locator = self.page.locator(selector)
        
        try:
            actual_count = locator.count()
            passed = actual_count > expected_count
            logger.info(f"      实际数量：{actual_count}")
            logger.info(f"      期望大于：{expected_count}")
            return passed
        except:
            return False

    def run_scenario(self, scenario_id: str, yaml_file: str = "test_scenarios.yaml", max_retries: int = 1):
        """运行指定场景
        
        Args:
            scenario_id: 场景 ID
            yaml_file: YAML 配置文件路径
            max_retries: 最大重试次数，默认 1 次
            
        Returns:
            bool: 场景执行是否成功
        """
        config = self.load_scenarios(yaml_file)
        scenario = config["scenarios"].get(scenario_id)

        if not scenario:
            logger.error(f"场景未找到：{scenario_id}")
            return False

        logger.info("=" * 60)
        logger.info(f"开始执行场景：{scenario['name']}")
        logger.info(f"场景描述：{scenario['description']}")
        logger.info("=" * 60)

        steps = scenario.get("steps", [])
        total_steps = len(steps)
        logger.info(f"共 {total_steps} 个步骤待执行")

        for attempt in range(max_retries + 1):
            if attempt > 0:
                logger.info(f"第 {attempt + 1} 次重试场景...")
            
            success = True
            for i, step in enumerate(steps, 1):
                try:
                    result = self.execute_action(step, i, total_steps)
                    if not result:
                        logger.error(f"步骤 {i} 执行失败")
                        error_screenshot = f"error_step_{i}_attempt_{attempt + 1}.png"
                        self.page.screenshot(path=error_screenshot)
                        logger.error(f"错误截图已保存：{error_screenshot}")
                        success = False
                        break
                except Exception as e:
                    logger.error(f"步骤 {i} 异常：{e}")
                    error_screenshot = f"error_step_{i}_attempt_{attempt + 1}.png"
                    self.page.screenshot(path=error_screenshot)
                    logger.error(f"错误截图已保存：{error_screenshot}")
                    success = False
                    break
            
            if success:
                break

        if success:
            logger.info("=" * 60)
            logger.info(f"场景完成：{scenario['name']}")
            logger.info("=" * 60)
        else:
            logger.error("=" * 60)
            logger.error(f"场景失败：{scenario['name']}（已重试{max_retries}次）")
            logger.error("=" * 60)
        
        return success

    def run_all_scenarios(self, yaml_file: str = "test_scenarios.yaml", inter_scenario_delay: int = 2):
        """运行所有场景
            
        Args:
            yaml_file: YAML 配置文件路径
            inter_scenario_delay: 场景间延迟（秒），默认 2 秒
                
        Returns:
            dict: 执行结果字典
        """
        config = self.load_scenarios(yaml_file)
        scenarios = config["scenarios"]
    
        logger.info("=" * 60)
        logger.info(f"共有 {len(scenarios)} 个场景待执行")
        logger.info("=" * 60)
    
        results = {}
        for idx, scenario_id in enumerate(scenarios):
            success = self.run_scenario(scenario_id, yaml_file)
            results[scenario_id] = success
                
            # 如果不是最后一个场景，添加延迟
            if idx < len(scenarios) - 1:
                logger.info(f"等待 {inter_scenario_delay} 秒后继续下一个场景...")
                time.sleep(inter_scenario_delay)
    
        # 打印汇总
        logger.info("=" * 60)
        logger.info("执行结果汇总")
        logger.info("=" * 60)
        for sid, success in results.items():
            scenario_name = config["scenarios"][sid]["name"]
            status = "✅ 通过" if success else "❌ 失败"
            logger.info(f"  {status} [{sid}] {scenario_name}")
    
        passed = sum(1 for s in results.values() if s)
        failed = len(results) - passed
        logger.info(f"总计：{passed} 通过，{failed} 失败，{len(results)} 个场景")
            
        return results


def main():
    """主函数 - 命令行入口"""
    import sys

    # 获取命令行参数
    scenario_id = sys.argv[1] if len(sys.argv) > 1 else None

    with sync_playwright() as p:
        # 根据环境变量选择浏览器类型
        if BROWSER == "firefox":
            browser = p.firefox.launch(headless=not HEADED, slow_mo=100)
        elif BROWSER == "webkit":
            browser = p.webkit.launch(headless=not HEADED, slow_mo=100)
        else:  # default to chromium
            browser = p.chromium.launch(headless=not HEADED, slow_mo=100)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        executor = ScenarioExecutor(page)

        try:
            if scenario_id:
                # 执行指定场景
                logger.info("执行指定场景")
                executor.run_scenario(scenario_id)
            else:
                # 执行所有场景
                logger.info("执行所有场景")
                executor.run_all_scenarios()
        except KeyboardInterrupt:
            logger.warning("用户中断")
        finally:
            browser.close()


if __name__ == "__main__":
    main()

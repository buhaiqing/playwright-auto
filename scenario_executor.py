#!/usr/bin/env python3
"""
YAML 测试场景执行器
自动解析 test_scenarios.yaml 并执行测试
支持每个步骤的 description 描述输出
"""

from pickle import TRUE
import yaml
import os
import time
from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv

load_dotenv()

URL = os.getenv("URL")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")


class ScenarioExecutor:
    """场景执行器"""

    def __init__(self, page: Page):
        self.page = page
        self.results = []

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
        iframe = action.get("iframe")  # iframe选择器
        exact = action.get("exact") or True

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
            print(f"    ⚠️ 未知动作: {action_type}")
            return False

        # 打印执行结果
        if result:
            print(f"    ✅ 步骤完成")
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
        print(
            f"\n  📍 步骤 {step_num}/{total_steps}: [{action_type.upper()}]{iframe_info}"
        )
        if description:
            print(f"     📝 {description}")

    def _do_login(self) -> bool:
        """执行登录"""
        self.page.goto(f"{URL}/www/view/entry3.html")
        self.page.wait_for_load_state("networkidle")

        # 填写凭证
        self.page.fill('input[placeholder="手机号/用户名"]', USERNAME)
        self.page.fill('input[placeholder="密码"]', PASSWORD)

        # 验证码处理（截图后等待人工输入）
        captcha_path = "temp_captcha.png"
        try:
            self.page.locator('.verify-code-img, img[src*="captcha"]').screenshot(
                path=captcha_path
            )
            print(f"     📸 验证码已保存: {captcha_path}")
        except:
            pass

        captcha = input("     🔑 请输入验证码: ")
        self.page.fill('input[placeholder="验证码"]', captcha)

        # 点击登录
        self.page.click('button:has-text("登录")')
        self.page.wait_for_url("**/newframe.html**", timeout=30000)
        return True

    def _do_navigate(self, path: list) -> bool:
        """执行导航"""
        print(f"     🧭 导航路径: {' -> '.join(path)}")
        for item in path:
            self.page.click(f"text={item}")
            time.sleep(0.5)
        return True

    def _do_click(self, selector: str, iframe: str = None, exact: bool = True) -> bool:
        """执行点击

        Args:
            selector: 元素选择器
            iframe: iframe选择器，如 "iframe#WrhContent"
        """
        if iframe:
            # if iframe.startswith("iframe"):
            #     iframe = iframe[len("iframe") :]
            print(f"     🖱️ 点击元素: {selector}")
            print(f"        在iframe中: {iframe}")
            print(f"        excat: {exact}")
            # 等待iframe加载并点击
            self.page.wait_for_selector(selector=iframe, timeout=30000)

            self.page.frame_locator(selector=iframe).locator(selector_or_locator=selector).click()
            # self.page.frame_locator(selector=iframe).get_by_text(
            #     text=selector, exact=exact
            # ).click()

           
        else:
            print(f"     🖱️ 点击元素: {selector}")
            self.page.click(selector)
        time.sleep(1)
        return True

    def _do_fill(self, selector: str, value: str, iframe: str = None) -> bool:
        """执行填写

        Args:
            selector: 元素选择器
            value: 填写值
            iframe: iframe选择器
        """
        if iframe:
            print(f"     ⌨️ 填写内容: {selector}")
            print(f"        值: {value}")
            print(f"        在iframe中: {iframe}")
            # 等待iframe加载并填写
            self.page.wait_for_selector(iframe, timeout=10000)
            self.page.frame_locator(iframe).locator(selector).wait_for(timeout=10000)
            self.page.frame_locator(iframe).locator(selector).fill(value)
        else:
            print(f"     ⌨️ 填写内容: {selector}")
            print(f"        值: {value}")
            self.page.fill(selector, value)
        return True

    def _do_switch_frame(self, iframe: str) -> bool:
        """切换iframe上下文

        Args:
            iframe: iframe选择器
        """
        print(f"     🔄 切换到iframe: {iframe}")
        # 验证iframe存在
        self.page.wait_for_selector(iframe, timeout=10000)
        return True

    def _do_screenshot(self, filename: str) -> bool:
        """执行截图"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filepath = f"screenshots/{timestamp}_{filename}"
        os.makedirs("screenshots", exist_ok=True)
        self.page.screenshot(path=filepath)
        print(f"     📸 截图保存: {filepath}")
        return True

    def _do_wait(self, seconds: int) -> bool:
        """执行等待"""
        print(f"     ⏱️ 等待 {seconds} 秒...")
        time.sleep(seconds)
        return True

    def run_scenario(self, scenario_id: str, yaml_file: str = "test_scenarios.yaml"):
        """运行指定场景"""
        config = self.load_scenarios(yaml_file)
        scenario = config["scenarios"].get(scenario_id)

        if not scenario:
            print(f"❌ 场景未找到: {scenario_id}")
            return False

        print("=" * 60)
        print(f"🚀 开始执行场景: {scenario['name']}")
        print(f"📝 场景描述: {scenario['description']}")
        print("=" * 60)

        steps = scenario.get("steps", [])
        total_steps = len(steps)
        print(f"\n📋 共 {total_steps} 个步骤待执行\n")

        for i, step in enumerate(steps, 1):
            try:
                success = self.execute_action(step, i, total_steps)
                if not success:
                    print(f"\n    ❌ 步骤 {i} 执行失败")
                    self.page.screenshot(path=f"error_step_{i}.png")
                    print(f"    📸 错误截图已保存: error_step_{i}.png")
                    return False
            except Exception as e:
                print(f"\n    ❌ 步骤 {i} 异常: {e}")
                self.page.screenshot(path=f"error_step_{i}.png")
                return False

        print("\n" + "=" * 60)
        print(f"✅ 场景完成: {scenario['name']}")
        print("=" * 60 + "\n")
        return True

    def run_all_scenarios(self, yaml_file: str = "test_scenarios.yaml"):
        """运行所有场景"""
        config = self.load_scenarios(yaml_file)
        scenarios = config["scenarios"]

        print(f"\n{'=' * 60}")
        print(f"📋 共有 {len(scenarios)} 个场景待执行")
        print(f"{'=' * 60}\n")

        results = {}
        for scenario_id in scenarios:
            success = self.run_scenario(scenario_id, yaml_file)
            results[scenario_id] = success
            time.sleep(6)  # 场景间暂停

        # 打印汇总
        print("\n" + "=" * 60)
        print("📊 执行结果汇总")
        print("=" * 60)
        for sid, success in results.items():
            scenario_name = config["scenarios"][sid]["name"]
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {status} [{sid}] {scenario_name}")

        passed = sum(1 for s in results.values() if s)
        failed = len(results) - passed
        print(f"\n总计: {passed} 通过, {failed} 失败, {len(results)} 个场景")


def main():
    """主函数 - 命令行入口"""
    import sys

    # 获取命令行参数
    scenario_id = sys.argv[1] if len(sys.argv) > 1 else None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        executor = ScenarioExecutor(page)

        try:
            if scenario_id:
                # 执行指定场景
                print("执行指定场景")
                executor.run_scenario(scenario_id)
            else:
                # 执行所有场景
                print("执行所有场景")
                executor.run_all_scenarios()
        except KeyboardInterrupt:
            print("\n\n⏹️ 用户中断")
        finally:
            browser.close()


if __name__ == "__main__":
    main()

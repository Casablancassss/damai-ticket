import asyncio
from playwright.async_api import async_playwright

# --- 核心配置 ---
TARGET_URL = "https://detail.damai.cn/item.htm?id=xxxxxxxx" # 目标票品URL
USER_DATA_DIR = "./user_data"  # 保存登录状态的目录

async def main():
    async with async_playwright() as p:
        # 1. 登录与认证：使用持久化上下文保留登录状态
        # 首次运行时，需要手动登录。之后只要cookie不过期，即可免登录。
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False, # 首次登录需要显示浏览器
            slow_mo=50,      # 减慢操作速度，便于观察
            args=['--start-maximized']
        )
        page = await context.new_page()

        # 检查是否已登录，如果未登录，提示用户手动登录
        await page.goto("https://www.damai.cn")
        try:
            # 通过检查页面上是否存在特定于登录后状态的元素（如用户昵称）来判断
            await page.wait_for_selector('div.user-info span.user-name', timeout=5000)
            print("检测到已登录状态。")
        except:
            print("未检测到登录状态，请在新打开的浏览器中手动完成扫码登录。")
            # 等待用户手动登录成功
            await page.wait_for_selector('div.user-info span.user-name', timeout=60000)
            print("登录成功！")


        # 2. 访问目标页面
        print(f"正在访问目标页面: {TARGET_URL}")
        await page.goto(TARGET_URL)

        try:
            # 3. 循环抢票：Playwright的自动等待机制让代码更简洁
            print("等待 '立即购买' 按钮出现并变为可点击状态...")
            # 定位购买按钮，这里的选择器需要根据实际页面结构调整
            buy_button = page.locator('div.buy-btn') # 注意：这个选择器是示例，需要替换
            await buy_button.wait_for(state='visible', timeout=300000) # 等待按钮可见
            
            print("按钮已出现，准备抢票！")
            while True:
                try:
                    await buy_button.click()
                    # 如果点击成功，大概率会跳转到订单确认页
                    # 等待订单确认页的某个特征元素出现
                    await page.wait_for_selector('div.confirm-order-container', timeout=5000)
                    print("抢票成功！已进入订单确认页面。")
                    break # 跳出循环
                except Exception as e:
                    # 如果按钮无法点击或页面刷新，继续循环
                    # print(f"抢票中... ({e})") # 打印错误信息以供调试
                    pass


            # 4. 确认订单
            print("正在选择观演人并提交订单...")
            # 定位观演人复选框 (示例选择器)
            await page.locator('div.ticket-buyer-item').first.click()
            # 定位提交订单按钮 (示例选择器)
            await page.locator('div.submit-order-button').click()

            # 5. 等待最终结果
            # 可以通过URL变化或特定成功/失败信息来判断最终结果
            print("订单已提交，请尽快在手机App上完成支付！")
            
        except Exception as e:
            print(f"抢票过程中发生错误: {e}")
        
        await asyncio.sleep(30) # 保持浏览器打开一段时间
        await context.close()


if __name__ == "__main__":
    asyncio.run(main())
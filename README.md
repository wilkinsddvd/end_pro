# 端到端功能测试说明文档

## 项目简介

本测试脚本 (`test_system_e2e.py`) 使用 **Selenium 4.x + Microsoft Edge WebDriver** 对工单管理系统进行端到端 (E2E) 综合功能测试，覆盖认证、工单管理、快速回复、数据统计和个性化设置等核心模块。

---

## 测试覆盖范围

| 模块 | 测试项 | 用例数 |
|------|--------|--------|
| **A. 认证测试** | 用户注册、有效登录、错误密码登录、用户登出 | 4 |
| **B. 工单管理** | 创建工单、查看列表（分页）、查看详情、更新状态、搜索、过滤 | 6 |
| **C. 快速回复** | 创建模板、查看列表、在工单中使用、编辑模板 | 4 |
| **D. 数据统计** | Dashboard 统计卡片、趋势图表、状态分布、优先级分布、响应时长 | 5 |
| **E. 个性化设置** | 切换深色模式、修改个人信息、修改密码 | 3 |
| **合计** | | **22** |

---

## 环境要求

### 系统依赖

- Python 3.8+
- Microsoft Edge 浏览器（或 Google Chrome / Chromium）
- 对应版本的 WebDriver（脚本会自动回退到 Chrome）

### Python 依赖

```bash
pip install selenium
```

### 服务依赖

| 服务 | 地址 | 说明 |
|------|------|------|
| 后端 API | http://localhost:8000 | FastAPI 应用 |
| 前端应用 | http://localhost:5173 | Vue 3 应用 |

---

## 启动步骤

### 1. 启动后端

```bash
cd end_pro
pip install -r requirements.txt
uvicorn main:app --reload
# 后端运行在 http://localhost:8000
```

### 2. 启动前端

```bash
cd fronted_pro
npm install
npm run dev
# 前端运行在 http://localhost:5173
```

### 3. 安装测试依赖

```bash
pip install selenium
```

### 4. 运行测试

```bash
cd end_pro
python test_system_e2e.py
```

---

## 输出示例

```
============================================================
  端到端功能测试 - Selenium + Edge WebDriver
  目标: http://localhost:5173
  测试账号: testuser123456
============================================================

共 22 个测试用例，开始执行...

[A. 认证测试]
  ✓ test_01_user_registration          2.3s
  ✓ test_02_user_login_valid           1.8s
  ✓ test_03_login_invalid_credentials  2.1s
  ✓ test_04_user_logout                1.5s

[B. 工单管理测试]
  ✓ test_05_create_ticket              3.2s
  ✓ test_06_ticket_list_pagination     2.0s
  ✓ test_07_ticket_detail              2.5s
  S test_08_update_ticket_status       (跳过)
  ✓ test_09_search_ticket              2.8s
  ✓ test_10_filter_tickets             1.9s

...

============================================================
  测试完成！总耗时: 68.3s
  总计: 22  通过: 19  失败: 0  跳过: 3
  成功率: 86.4%
  报告: test_report.html
============================================================

✅ 测试报告已生成: test_report.html
```

---

## 测试报告

运行完成后自动生成 `test_report.html`，包含：

```
测试执行报告
├─ 摘要卡片
│  ├─ 测试总数
│  ├─ 通过数
│  ├─ 失败数
│  ├─ 跳过数
│  └─ 成功率（进度条）
│
├─ 测试用例详情
│  ├─ 认证测试（4个）
│  ├─ 工单管理（6个）
│  ├─ 快速回复（4个）
│  ├─ 统计分析（5个）
│  └─ 设置功能（3个）
│
├─ 失败用例分析
│  └─ 错误堆栈 + 失败截图（Base64 内嵌）
│
└─ 执行统计
   └─ 总耗时、平均耗时、通过率
```

---

## 截图目录

测试失败时自动截图并保存至 `screenshots/` 目录：

```
screenshots/
├─ test_01_registration_fail_143022.png
├─ test_07_ticket_detail_fail_143156.png
└─ ...
```

截图也会以 Base64 格式内嵌到 HTML 报告中，方便查阅。

---

## 技术实现

### 核心技术

| 技术 | 说明 |
|------|------|
| Selenium 4.x | 浏览器自动化框架 |
| Edge WebDriver | 微软 Edge 驱动（自动回退 Chrome）|
| Python unittest | 测试框架，提供断言和生命周期管理 |
| WebDriverWait | 显式等待，处理异步加载 |
| 隐式等待 (5s) | 全局元素查找等待 |

### 测试数据策略

- **随机用户名**：使用时间戳后缀（如 `testuser234567`）避免重复注册冲突
- **UUID 工单标题**：每次创建工单使用 UUID 生成唯一标题
- **密码规则**：符合系统要求（8-64位，含字母和数字）

### 元素定位策略

测试脚本使用多种定位策略，按优先级依次尝试：

1. `CSS Selector`（最常用）
2. `XPath`（文本内容匹配）
3. `By.ID`
4. 元素位置索引（兜底方案）

### 等待机制

```python
# 显式等待（推荐）
wait = WebDriverWait(driver, 15)
element = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input")))

# 隐式等待（全局）
driver.implicitly_wait(5)

# AJAX 等待（固定时间 + 元素检查）
time.sleep(0.5)
```

---

## 文件结构

```
end_pro/
├─ test_system_e2e.py       # 主测试脚本（单文件）
├─ README.md                # 本说明文档
├─ test_report.html         # 自动生成的测试报告（运行后生成）
└─ screenshots/             # 失败截图目录（运行后生成）
   ├─ test_xx_xxx.png
   └─ ...
```

### 脚本内部结构

```
test_system_e2e.py
├─ 导入和全局配置
├─ _make_driver()            # WebDriver 初始化（Edge → Chrome 自动回退）
├─ TestBase                  # 测试基类（等待/截图/登录等公共方法）
├─ TestAuthentication        # 认证测试（4个用例）
├─ TestTicketManagement      # 工单管理测试（6个用例）
├─ TestQuickReply            # 快速回复测试（4个用例）
├─ TestStatistics            # 数据统计测试（5个用例）
├─ TestSettings              # 设置功能测试（3个用例）
├─ HTMLTestReporter          # HTML 报告生成器
├─ _ReportingTestResult      # 自定义 TestResult，结果路由到报告器
└─ main()                    # 入口函数
```

---

## 常见问题

### Q: Edge WebDriver 不可用怎么办？

脚本会自动回退到 Chrome WebDriver。确保已安装 Chrome 浏览器并将 ChromeDriver 放在 PATH 中，或通过 `pip install webdriver-manager` 自动管理驱动：

```python
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.service import Service
service = Service(EdgeChromiumDriverManager().install())
driver = webdriver.Edge(service=service, options=opts)
```

### Q: 某些测试用例显示"跳过"？

跳过（Skip）通常因为：
- 前端页面 URL 路由与预设路径不符
- 功能模块未启用或页面元素结构不同
- 依赖的前置条件未满足（如登录失败）

这些用例不计为失败，需根据实际前端路由调整 `navigate()` 的路径参数。

### Q: 如何调整前端地址？

修改脚本顶部的配置：

```python
BASE_URL = "http://localhost:5173"   # 前端地址
API_BASE = "http://localhost:8000/api"  # 后端地址
DEFAULT_WAIT = 15   # 显式等待秒数
```

### Q: 如何在有界面模式下运行（非 headless）？

修改 `_make_driver()` 函数，注释掉 headless 参数：

```python
# opts.add_argument("--headless")  # 注释此行即可显示浏览器窗口
```

---

## API 端点覆盖

脚本通过前端 UI 间接测试以下后端 API：

| 方法 | 端点 | 测试用例 |
|------|------|--------|
| POST | /api/register | test_01_user_registration |
| POST | /api/login | test_02_user_login_valid, test_03_login_invalid_credentials |
| POST | /api/logout | test_04_user_logout |
| POST | /api/tickets | test_05_create_ticket |
| GET  | /api/tickets | test_06_ticket_list_pagination, test_09_search_ticket, test_10_filter_tickets |
| GET  | /api/tickets/{id} | test_07_ticket_detail |
| PUT  | /api/tickets/{id} | test_08_update_ticket_status |
| POST | /api/quick-replies | test_11_create_quick_reply |
| GET  | /api/quick-replies | test_12_quick_reply_list |
| PUT  | /api/quick-replies/{id} | test_14_edit_quick_reply |
| GET  | /api/dashboard/stats | test_15_dashboard_stats_cards |
| GET  | /api/dashboard/trend | test_16_ticket_trend_chart |
| GET  | /api/statistics/status-distribution | test_17_status_distribution |
| GET  | /api/statistics/priority-distribution | test_18_priority_distribution |
| GET  | /api/statistics/avg-response-time | test_19_response_time_stats |
| PUT  | /api/user/preferences | test_20_dark_mode_toggle |
| PUT  | /api/user/info | test_21_update_profile |
| PUT  | /api/user/password | test_22_change_password |

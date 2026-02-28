![1772244491726](image/CLAUDE/1772244491726.png)![1772244496840](image/CLAUDE/1772244496840.png)![1772244504957](image/CLAUDE/1772244504957.png)# Af Analyzer — 奥氏体相变温度分析工具

## 项目概述

基于 YY/T 1771-2021 标准第 11 章"相变温度的测定"，使用**切线法**从温度-形变量（位移）数据中计算奥氏体转变温度 As 和 Af-tan 的交互式 Web 分析工具。

## 技术栈

- **语言:** Python 3.10+
- **Web 框架:** Streamlit
- **交互图表:** Plotly
- **数据处理:** Pandas, NumPy, SciPy (savgol_filter, linregress)
- **静态图表/报告图片:** Matplotlib
- **Excel 导出:** openpyxl
- **路径处理:** pathlib（跨平台 Mac/Windows 兼容）
- **浏览器自动化测试:** Playwright MCP（Claude Code 通过 Playwright MCP Server 驱动浏览器进行 UI 验证）

## 项目结构

```
奥氏体变换/
├── CLAUDE.md                  # 本文件 — 项目上下文
├── prd.json                   # Ralph 任务定义
├── requirements.txt           # Python 依赖
├── app.py                     # Streamlit 主入口
├── core/                      # 分析引擎（与 UI 解耦）
│   ├── __init__.py
│   ├── data_loader.py         # 数据加载（JSON/Excel/CSV）
│   ├── preprocessing.py       # 按温度分组、平滑滤波
│   ├── tangent_analysis.py    # 切线法核心算法
│   └── report_export.py       # 报告导出（Excel/图片）
├── ui/                        # Streamlit UI 组件
│   ├── __init__.py
│   ├── sidebar.py             # 侧边栏：文件上传、参数控制
│   ├── overview_chart.py      # 多通道总览图
│   ├── analysis_chart.py      # 单通道切线分析图
│   └── results_panel.py       # 结果显示与导出
├── tests/                     # 测试
│   ├── __init__.py
│   ├── test_data_loader.py
│   ├── test_preprocessing.py
│   └── test_tangent_analysis.py
├── .streamlit/
│   └── config.toml            # Streamlit 主题配色配置
├── design-system/
│   └── af-analyzer/
│       └── MASTER.md          # 全局设计源（深色毛玻璃 + 莫兰迪配色）
├── tasks/                     # PRD 文档
│   └── prd-af-analyzer.md
├── docs/plans/                # 设计与实施计划
├── 标准/                       # 参考标准 PDF
└── 原始数据/                   # 测试数据
    ├── 2026.2.26/
    │   ├── AFReport_SP_20250507_102452.json   # 6通道，-3°C→28°C
    │   └── AFReport_SP_20250519_171458.json   # 1通道，-5.8°C→19°C
    └── 2026.2.28/
        └── data2.xlsx                         # 1通道，-6.5°C→29.4°C，含传感器突刺
```

## 原始数据格式

### 格式 A：设备导出 JSON（完整格式）

JSON 数组，每条记录包含时间戳、温度和最多 6 个通道：

```json
{
 "DateTimeStr": "2025-05-07 10:01:29.111",
 "Temperature": -3.0,
 "Space1": 124.276,
 "Space2": 132.067,
 "Space3": 105.992,
 "Space4": 101.803,
 "Space5": 89.125,
 "Space6": 82.025
}
```

- `Temperature`: 温度（°C），升温过程
- `Space1`~`Space6`: 位移/形变量，无数据时为字符串 `"NaN"`
- 采样频率约 10Hz，同一温度下有大量重复点

### 格式 B：简化 Excel/CSV（仅温度 + 单通道）

Excel 或 CSV 文件，仅包含 `Temperature` 和一个 `SpaceN` 列（无 `DateTimeStr`）：

| Temperature | Space1 |
|-------------|--------|
| -6.5        | 219    |
| -6.5        | 220    |
| -6.4        | 221    |

- 无 `DateTimeStr` 列（分析不依赖时间戳，不影响功能）
- 位移值可能为整数
- 可能只有一个通道（如仅 `Space1`）
- 数据加载器 `load_file()` 已兼容此格式，无需额外处理

## 核心算法：切线法（YY/T 1771-2021 第 11 章）

1. **数据预处理**:
   - 按 Temperature 分组求均值
   - **异常值自动检测与剔除**（滚动中位数 + MAD 阈值法）→ 线性插值修复
   - Savitzky-Golay 平滑
2. **求导**: 计算 dSpace/dTemperature
3. **中间切线**: 找到导数绝对值最大的点，在该点作切线
4. **低温基准线**: 对曲线起始段（马氏体相，平缓区）做线性拟合
5. **高温基准线**: 对曲线末尾段（奥氏体相，平缓区）做线性拟合
6. **交点计算**:
 - 中间切线 ∩ 低温基准线 → **As**（奥氏体转变开始温度）
 - 中间切线 ∩ 高温基准线 → **Af-tan**（切线法奥氏体完成温度）

### 异常值检测算法（Outlier Detection）

实际采集数据中可能存在传感器突刺（spike）——位移值在极短温度区间内剧烈突变后恢复。
这种异常会导致导数计算和最大斜率定位完全失效，必须在平滑之前剔除。

**算法步骤：**

1. 对分组后的位移数据计算**滚动中位数**（rolling median，窗口大小可配）
2. 计算每个点与滚动中位数的**偏差**
3. 计算偏差的**中位绝对偏差（MAD）** 作为鲁棒尺度估计
4. 将偏差超过 `threshold × MAD` 的点标记为异常（默认 threshold=5.0）
5. 用线性插值替代被标记的异常点

**实现位置：** `core/preprocessing.py` 中的 `remove_outliers()` 函数
**调用时机：** `group_by_temperature()` 之后、`smooth_data()` 之前
**配置方式：** 默认自动启用，用户可在侧边栏调整 MAD 阈值（高级参数）

## 编码约定

- 使用 `pathlib.Path` 处理所有文件路径（跨平台）
- UI 文字使用中文
- 代码注释使用英文
- 变量/函数命名使用英文 snake_case
- 所有数值计算在 `core/` 模块中完成，UI 层不包含业务逻辑
- Streamlit 状态管理使用 `st.session_state`
- 图表使用 Plotly，报告导出用 Matplotlib 生成静态图

## UI/UX 设计规范 — 深色毛玻璃 + 莫兰迪配色

**设计系统文件位置：** `design-system/af-analyzer/MASTER.md`
**主题配置文件：** `.streamlit/config.toml`

### 风格定义

**深色毛玻璃（Dark Glassmorphism）+ 莫兰迪色系（Morandi Palette）**

- **背景：** 深色 `#0F0F1A` + 三色径向渐变光晕（莫兰迪蓝/玫/绿）
- **卡片：** 半透明毛玻璃 `rgba(255,255,255,0.07)` + `backdrop-filter: blur(20px)` + 半透明边框
- **配色：** 莫兰迪蓝 `#8B9DC3`、莫兰迪玫 `#C4A4A4`、莫兰迪绿 `#A4B8A4`、莫兰迪杏 `#D4B896`
- **圆角：** 所有组件 ≥ 12px，卡片 20px
- **字体：** Inter（正文）+ JetBrains Mono（数值/代码）
- **文字：** 柔白 `#E8E4E0`（主文字）、`#8A8A9A`（次要文字）

### 实现方式

- **主题基色** → `.streamlit/config.toml` 中 `base = "dark"`，配色使用莫兰迪色值
- **全局样式** → 在 `app.py` 中通过 `st.markdown()` 注入 `MASTER.md` 中定义的完整自定义 CSS
- **图表配色** → Plotly 使用 `MASTER.md` 中的 `PLOTLY_LAYOUT` 配置（透明背景、莫兰迪色线条）
- **数值字体** → `st.metric` 等数值显示使用 JetBrains Mono 等宽字体
- **布局结构** → 侧边栏（控制面板）→ 总览图 → 分析图 → 结果面板

### 设计原则

- **高级沉浸** — 深色背景 + 渐变光晕 + 毛玻璃层次感
- **数据优先** — 图表透明背景融入整体风格，数据线条使用高可见度莫兰迪色
- **高对比度** — 浅色文字 `#E8E4E0` 在深色背景上清晰可读，标注点使用醒目颜色
- **操作直觉** — 滑块调整后结果实时更新，无需点击"计算"按钮
- **大圆角亲和** — 消除工业软件的生硬感

### UI/UX 交付检查清单

每个 UI 故事完成时，对照检查：

- [ ] 已参考 `design-system/af-analyzer/MASTER.md` 的配色和排版方案
- [ ] `.streamlit/config.toml` 配置为 dark 主题 + 莫兰迪色
- [ ] `app.py` 注入了 MASTER.md 中的完整自定义 CSS（渐变背景、毛玻璃卡片等）
- [ ] Plotly 图表使用 MASTER.md 中的 PLOTLY_LAYOUT（透明背景、莫兰迪色线条）
- [ ] 所有圆角 ≥ 12px
- [ ] 文字对比度足够（浅色文字 `#E8E4E0` + 深色背景 `#0F0F1A`）
- [ ] 数值显示使用 JetBrains Mono 等宽字体
- [ ] 交互控件有清晰的标签和提示文字
- [ ] 不同状态有明确的视觉反馈（加载中、错误、成功）

## 关键依赖版本

见 `requirements.txt`

## 运行方式

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 测试数据说明

| 文件 | 通道 | 温度范围 | 特点 |
|------|------|---------|------|
| 原始数据/2026.2.26/AFReport_SP_20250507_102452.json | Space1-6 全部有效 | -3°C → 28°C | 6通道完整数据，JSON 格式 |
| 原始数据/2026.2.26/AFReport_SP_20250519_171458.json | 仅 Space1 | -5.8°C → 19°C | 单通道数据，JSON 格式 |
| 原始数据/2026.2.28/data2.xlsx | 仅 Space1 | -6.5°C → 29.4°C | 简化 Excel 格式（无 DateTimeStr），**含传感器突刺异常**，用于验证异常值检测功能 |

---

## ⚠️ 开发流程强制约束（MANDATORY）

以下规则在执行 `prd.json` 中的任何用户故事时**必须严格遵守**，不可跳过。

### 规则 1：先测试，再推进（Test Before Next）

**每个用户故事完成后，必须通过测试验证才能进入下一个故事。**

执行顺序如下：

1. **编写代码** — 按用户故事的验收标准实现功能
2. **编写/运行测试** — core/ 模块的功能必须有对应的 pytest 测试
3. **确认测试通过** — 执行 `pytest tests/ -v` 确认所有测试通过
4. **验证验收标准** — 逐条检查验收标准是否满足
5. **标记完成** — 只有以上全部通过，才可将故事标记为 `passes: true`
6. **进入下一个故事** — 绝不跳过测试直接开始下一个故事

**对 core/ 模块（US-002 到 US-006）的额外要求：**

- 每个公开函数至少 2 个测试用例（正常路径 + 边界/异常路径）
- 测试文件与源文件一一对应：`core/data_loader.py` → `tests/test_data_loader.py`
- 使用项目中的真实测试数据（`原始数据/2026.2.26/` 下的 JSON 文件）编写集成测试
- 测试命令：`pytest tests/ -v --tb=short`
- 如果测试失败，必须修复后重新运行直到全部通过

### 规则 2：UI 功能必须通过 Playwright MCP 进行浏览器验证（Browser Verification）

**所有涉及 UI 的用户故事（US-007 到 US-014），必须使用 Playwright MCP 自动启动浏览器进行可视化验证。**

**工具要求：必须使用 Playwright MCP 进行浏览器自动化操作，不可手动验证或跳过。**

执行流程：

1. **启动 Streamlit 服务器** — 在后台执行 `streamlit run app.py --server.headless true`
2. **等待服务就绪** — 等待 Streamlit 服务器启动完成（检测到 `http://localhost:8501` 可访问）
3. **通过 Playwright MCP 打开页面** — 使用 `browser_navigate` 导航到 `http://localhost:8501`
4. **自动化交互验证** — 使用 Playwright MCP 的工具逐项验证：
   - `browser_snapshot` — 截取页面快照，检查 UI 元素是否正确渲染
   - `browser_click` — 点击按钮、选择下拉菜单等
   - `browser_type` / `browser_fill` — 输入文本内容
   - `browser_snapshot` — 每次操作后重新截图确认状态变化
5. **文件上传验证** — 使用 Playwright 的文件上传能力，上传 `原始数据/2026.2.26/` 下的真实测试 JSON 文件
6. **截图存档** — 每个 UI 故事验证通过后，使用 `browser_snapshot` 保存页面最终状态作为通过证据

**Playwright MCP 浏览器验证检查清单（每个 UI 故事必须逐项执行）：**

- [ ] `browser_navigate` 到 `http://localhost:8501`，页面正常加载
- [ ] `browser_snapshot` 确认无红色 Streamlit error 错误框
- [ ] `browser_snapshot` 确认所有 UI 元素正确渲染（标题、控件、图表可见）
- [ ] 通过 `browser_click` / `browser_fill` 操作交互控件，`browser_snapshot` 确认响应正确
- [ ] 使用真实测试数据完成一遍完整操作流程（上传 → 选通道 → 调参数 → 查看结果）
- [ ] 最终 `browser_snapshot` 截图作为验证证据，**截图必须显示加载数据后的完整 UI 状态（图表已渲染、结果已显示），空白页面或初始页面截图不算通过**

**⚠️ 浏览器验证强制约束（MANDATORY）：**

1. **禁止替代验证** — 浏览器端到端验证**不可用** Python 脚本、命令行测试、直接调用 core/ 函数或任何非浏览器方式替代。pytest 测试和 Python 脚本只测试核心计算逻辑，不覆盖 UI 层（Streamlit 渲染、组件交互、第三方库兼容性），两者不等价。
2. **禁止使用其他浏览器工具** — 仅使用 Playwright MCP 进行浏览器自动化。禁止使用 `superpowers-chrome`、`puppeteer` 或其他浏览器工具替代。如果 Playwright MCP 不可用，按规则 5 上报阻塞。
3. **诚实报告** — 如果某个验证步骤未能实际完成（如文件上传失败、页面报错、截图未包含预期内容），**必须如实报告为未通过**，不得以其他方式验证后标记为通过。虚假的"验证通过"比"验证失败"危害更大。
4. **文件上传必须成功** — 浏览器验证必须包含成功的文件上传操作。如果 Playwright MCP 无法完成文件上传，属于阻塞场景，按规则 5 上报。

**端口冲突处理：** 如果 8501 端口被占用，使用 `--server.port 8502` 启动并相应修改 Playwright 的导航 URL。

**Streamlit 服务器生命周期管理：**
- UI 开发阶段（US-007 起），首次启动后保持 Streamlit 在后台运行
- 代码修改后 Streamlit 自动热重载，Playwright 只需刷新页面（`browser_navigate` 同一 URL）
- 完成所有 UI 故事后再关闭服务器

### 规则 3：回归测试（Regression Guard）

**每完成一个新故事后，必须运行全量测试确保之前的功能未被破坏。**

```bash
pytest tests/ -v --tb=short
```

- 如果任何已通过的测试出现回归失败，必须先修复再继续
- 不允许注释掉或跳过之前的测试用例

### 规则 4：增量提交（Incremental Commits）

**每个用户故事完成并测试通过后，立即提交一次 git commit。**

提交格式：
```
feat(US-XXX): 简要描述完成的功能

- 验收标准 1 ✓
- 验收标准 2 ✓
- 测试: pytest tests/ 全部通过
```

### 规则 4b：清理临时文件（Cleanup After Work）

**每次完成用户故事、修复 bug 或调试结束后，必须清理过程中产生的临时/垃圾文件。**

需要清理的文件类型：
- 浏览器验证截图（如 `*.png` 截图文件，保存在项目根目录下的）
- 临时测试脚本（如 `test_temp.py`、`debug_*.py` 等一次性脚本）
- Streamlit 缓存（如 `__pycache__/` 下新增的缓存文件）
- 临时数据文件（如调试时生成的 `.csv`、`.xlsx`、`.json` 中间文件）
- 任何不属于项目结构的多余文件（对照 `CLAUDE.md` 项目结构部分检查）

**执行方式：**
1. 在 git commit 之前，运行 `ls` 检查项目根目录和子目录是否有多余文件
2. 删除所有临时文件
3. 确认项目目录只包含 `CLAUDE.md` 项目结构中列出的文件和必要的新增文件
4. 浏览器验证截图如需存档，统一移到 `docs/screenshots/` 目录下，不要散落在项目根目录

**禁止残留：** 不允许把调试过程中的临时文件提交到 git 或留在项目目录中。

### 规则 5：阻塞时上报（Escalate on Block）

如果某个故事遇到以下情况，**停止执行并报告问题**，等待人工指示：

- 测试反复失败无法修复（超过 3 次尝试）
- 验收标准存在歧义或矛盾
- 需要修改之前已通过故事的接口
- 依赖的第三方库行为与预期不符
- 浏览器验证发现设计文档未覆盖的交互问题
- **Playwright MCP 不可用或无法完成所需的浏览器操作**（如文件上传失败、页面交互无响应等）— 不可自行用其他工具或 Python 脚本绕过
- **任何验证步骤无法按要求完成时** — 必须如实报告，不得跳过或替代

### 规则 6：真实数据验证（Real Data Validation）

**在 US-006（切线法核心算法）完成后，必须用两组真实测试数据进行端到端验证：**

1. 加载 `AFReport_SP_20250507_102452.json`，对 Space1 通道执行完整分析流程
2. 加载 `AFReport_SP_20250519_171458.json`，对 Space1 通道执行完整分析流程
3. 打印输出 As 和 Af-tan 结果
4. 结果必须在物理合理范围内（As 在 5°C~25°C 之间，Af-tan 在 As 之上且不超过数据最高温度）
5. 如果结果明显异常，检查算法实现并修复

### 规则 7：Streamlit 开发服务器管理

- UI 开发阶段（US-007 起），保持 Streamlit 服务器在后台运行
- 每次修改 UI 代码后，Streamlit 会自动热重载，刷新浏览器即可看到变更
- 如需重启：先终止旧进程，再执行 `streamlit run app.py`
- 端口冲突时使用 `streamlit run app.py --server.port 8502`

---

### 规则 8：进度持久化 — Planning with Files（跨 Session 记忆）

**使用 planning-with-files 技能在项目目录下维护三个文件，确保跨 session 不丢失进度。**

在开始执行第一个用户故事之前，创建以下文件：

- **`task_plan.md`** — 任务进度追踪（基于 prd.json 生成，标记每个故事的状态）
- **`findings.md`** — 开发过程中的发现和决策记录（如：某个平滑参数效果不好、某个库 API 的坑等）
- **`progress.md`** — 每次 session 的操作日志（做了什么、遇到什么问题、怎么解决的）

**更新规则：**
- 每完成一个用户故事后，更新 `task_plan.md` 的状态
- 遇到重要发现或踩坑时，立即写入 `findings.md`（不要等到后面再补）
- 每次 session 开始时，先读取这三个文件恢复上下文
- 遵循 2-Action Rule：每做 2 次搜索/浏览操作后，立即把关键发现写入文件

### 规则 9：API 文档查询 — 遇到不确定的库 API 时查文档

**不需要每一步都查文档，但遇到以下情况时必须使用 Context7 或 Exa 查询最新文档：**

- Streamlit 组件的参数不确定（如 `st.slider` 的 `step` 参数类型）
- Plotly 图表配置细节（如添加标注、自定义虚线样式、双 Y 轴等）
- SciPy 函数的参数含义不明确（如 `savgol_filter` 的 `deriv` 参数）
- 报错信息指向库版本兼容性问题

**查询方式（按优先级）：**
1. **Context7 MCP** — 优先使用，获取结构化的官方文档片段
2. **Exa 搜索** — Context7 找不到时使用，搜索代码示例和 Stack Overflow 答案

**禁止猜测 API：** 如果不确定某个函数的参数或返回值，必须查文档确认，不要凭记忆编写可能错误的代码。

## 开发流程总览

```
┌─────────────────────────────────────────────────┐
│              每个用户故事的执行流程                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. 阅读用户故事和验收标准                        │
│     │                                           │
│  2. 编写实现代码                                 │
│     │                                           │
│  3. 编写单元测试（core/ 模块）                    │
│     │                                           │
│  4. 运行 pytest tests/ -v                       │
│     │                                           │
│     ├─ FAIL → 修复代码 → 回到 4                  │
│     │                                           │
│     └─ PASS ↓                                   │
│                                                 │
│  5. 是 UI 故事?                                  │
│     │                                           │
│     ├─ YES → 启动 Streamlit                     │
│     │        打开浏览器 http://localhost:8501    │
│     │        逐项验证验收标准                     │
│     │        截图记录                            │
│     │        ├─ FAIL → 修复 → 回到 5             │
│     │        └─ PASS ↓                          │
│     │                                           │
│     └─ NO ↓                                     │
│                                                 │
│  6. 运行全量测试（回归保护）                       │
│     │                                           │
│     ├─ FAIL → 修复回归 → 回到 6                  │
│     └─ PASS ↓                                   │
│                                                 │
│  7. Git commit                                  │
│     │                                           │
│  8. 标记故事 passes: true                        │
│     │                                           │
│  9. 进入下一个用户故事                            │
│                                                 │
└─────────────────────────────────────────────────┘
```

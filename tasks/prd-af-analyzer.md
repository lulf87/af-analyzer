# PRD: 奥氏体相变温度分析工具 (Af Analyzer)

## Introduction

基于 YY/T 1771-2021 标准第 11 章"相变温度的测定"，开发一个交互式 Web 工具，从设备采集的温度-位移（形变量）数据中，使用切线法自动计算奥氏体转变温度 As 和 Af-tan，并支持人工交互调整分析参数。

工具使用 Streamlit 构建，在浏览器中运行，兼容 Mac 和 Windows 平台。

## Goals

- 自动读取设备导出的 JSON/Excel/CSV 格式的温度-位移数据
- 对多通道数据提供总览视图，支持逐通道分析
- 自动完成数据预处理（分组平均、平滑滤波）和切线法计算
- 提供交互式参数调整（平滑参数、基准线范围、中间切线位置），图表实时更新
- 输出 As 和 Af-tan 数值结果，并可导出带切线标注的分析图表和结构化 Excel 报告

## User Stories

### US-001: 项目基础结构搭建
**Description:** 作为开发者，我需要项目的基础目录结构和入口文件，以便后续模块开发。

**Acceptance Criteria:**
- [ ] 创建 `core/` 目录及 `__init__.py`
- [ ] 创建 `ui/` 目录及 `__init__.py`
- [ ] 创建 `tests/` 目录及 `__init__.py`
- [ ] 创建 `app.py` 作为 Streamlit 入口，运行后显示标题 "奥氏体相变温度分析工具"
- [ ] `streamlit run app.py` 可正常启动无报错

### US-002: JSON 数据加载
**Description:** 作为用户，我需要加载设备导出的 JSON 文件，以便分析数据。

**Acceptance Criteria:**
- [ ] 在 `core/data_loader.py` 中实现 `load_json(file_path) -> pd.DataFrame` 函数
- [ ] 返回的 DataFrame 包含 `Temperature`, `Space1`~`Space6` 列
- [ ] 字符串 `"NaN"` 自动转换为 `np.nan`
- [ ] 自动检测哪些 Space 通道有有效数据（非全 NaN），返回有效通道列表
- [ ] Tests pass

### US-003: Excel 和 CSV 数据加载
**Description:** 作为用户，我需要加载 Excel 和 CSV 格式的数据文件。

**Acceptance Criteria:**
- [ ] 在 `core/data_loader.py` 中实现 `load_excel(file_path) -> pd.DataFrame` 函数
- [ ] 在 `core/data_loader.py` 中实现 `load_csv(file_path) -> pd.DataFrame` 函数
- [ ] 实现 `load_file(file_path) -> pd.DataFrame` 统一入口，根据扩展名自动选择加载方式
- [ ] 三种格式返回统一结构的 DataFrame
- [ ] Tests pass

### US-004: 数据预处理 — 按温度分组与平滑
**Description:** 作为用户，我需要原始数据经过预处理后变得平滑可分析。

**Acceptance Criteria:**
- [ ] 在 `core/preprocessing.py` 中实现 `group_by_temperature(df, channel) -> pd.DataFrame` 函数，按 Temperature 分组对指定通道求均值
- [ ] 实现 `smooth_data(temps, values, window_length=51, polyorder=3) -> (smoothed_temps, smoothed_values)` 函数，使用 Savitzky-Golay 滤波
- [ ] window_length 必须为奇数，函数内自动校正
- [ ] 输出数据点数量与输入一致
- [ ] Tests pass

### US-016: 数据预处理 — 异常值自动检测与剔除
**Description:** 作为系统，我需要在平滑之前自动检测和剔除传感器突刺等异常数据点，避免异常值污染导数计算和最大斜率定位。

**Background:** 实际采集数据中位移值可能在极短温度区间内剧烈突变后恢复（传感器抖动/接触不良/样品松动），这种突刺会导致导数计算出现极端值，使最大斜率点被错误定位到突刺处而非真实的相变区域。

**Acceptance Criteria:**
- [ ] 在 `core/preprocessing.py` 中实现 `remove_outliers(temps, values, window=5, threshold=5.0)` 函数
- [ ] 使用滚动中位数 + MAD（中位绝对偏差）阈值法检测异常点
- [ ] 异常点使用线性插值替代（基于前后正常点修复）
- [ ] 返回修复后的 temps、values 以及布尔掩码（True=异常点）
- [ ] 对正常数据不产生误剔除
- [ ] 对含传感器突刺的数据（`原始数据/2026.2.28/data2.xlsx`）能正确检测
- [ ] 在 `analyze_channel()` 中集成：group → remove_outliers → smooth → 切线分析
- [ ] Tests pass

### US-017: 图表设置 — Y 轴范围自适应
**Description:** 作为用户，我需要图表坐标轴范围自动适应数据实际值域，而不是硬编码上限。

**Background:** 当前 Y 轴范围滑块上限固定为 500，但实际数据位移值可达 654+，导致数据显示不全。

**Acceptance Criteria:**
- [ ] Y 轴范围滑块的 min/max 根据当前数据实际值域动态计算（留 10% 余量）
- [ ] X 轴范围滑块同理，根据实际温度范围动态设置
- [ ] 使用 `原始数据/2026.2.28/data2.xlsx` 验证 Y 轴显示完整
- [ ] Verify in browser

### US-005: 切线法核心算法 — 导数与最大斜率点
**Description:** 作为系统，我需要从平滑曲线上找到斜率最大的点。

**Acceptance Criteria:**
- [ ] 在 `core/tangent_analysis.py` 中实现 `compute_derivative(temps, values) -> derivatives` 函数，计算 dValue/dTemperature
- [ ] 实现 `find_max_slope_index(temps, values, derivatives) -> int` 函数，返回绝对斜率最大处的索引
- [ ] 支持通过偏移参数 `offset` 手动微调最大斜率点位置
- [ ] Tests pass

### US-006: 切线法核心算法 — 基准线拟合与交点计算
**Description:** 作为系统，我需要拟合低温和高温基准线，并计算与中间切线的交点温度。

**Acceptance Criteria:**
- [ ] 实现 `fit_baseline(temps, values, start_temp, end_temp) -> (slope, intercept)` 函数，对指定温度区间做线性拟合
- [ ] 实现 `compute_tangent_line(temps, values, derivatives, index) -> (slope, intercept)` 函数，在指定索引处计算切线
- [ ] 实现 `find_intersection(slope1, intercept1, slope2, intercept2) -> temperature` 函数，求两条直线交点的温度值
- [ ] 实现 `analyze_channel(temps, values, low_range, high_range, slope_offset=0) -> dict` 高层接口，返回 `{"As": float, "Af_tan": float, "mid_tangent": (slope, intercept), "low_baseline": (slope, intercept), "high_baseline": (slope, intercept)}`
- [ ] 平行线（无交点）情况返回 NaN 并给出警告
- [ ] Tests pass

### US-007: Streamlit 侧边栏 — 文件上传与通道选择
**Description:** 作为用户，我需要在侧边栏上传数据文件并选择要分析的通道。

**Acceptance Criteria:**
- [ ] 在 `ui/sidebar.py` 中实现侧边栏组件
- [ ] 文件上传支持 `.json`, `.xlsx`, `.csv` 格式
- [ ] 上传后自动检测有效通道，显示通道选择下拉菜单
- [ ] 选择通道后将数据存入 `st.session_state`
- [ ] Verify in browser using dev-browser skill

### US-008: 多通道总览图
**Description:** 作为用户，我需要看到所有有效通道的温度-位移曲线总览。

**Acceptance Criteria:**
- [ ] 在 `ui/overview_chart.py` 中实现总览图组件
- [ ] 使用 Plotly 绘制所有有效通道的 Temperature vs Space 曲线
- [ ] 不同通道用不同颜色区分，带图例
- [ ] 支持缩放和悬停查看数值
- [ ] 当前选中的通道高亮显示
- [ ] Verify in browser using dev-browser skill

### US-009: 平滑参数控制面板
**Description:** 作为用户，我需要调整平滑参数并实时预览效果。

**Acceptance Criteria:**
- [ ] 在侧边栏添加"数据预处理"折叠区域
- [ ] 提供 Savitzky-Golay 窗口大小滑块（范围 5~201，步长 2，默认 51）
- [ ] 提供多项式阶数滑块（范围 1~7，默认 3）
- [ ] 参数变更后图表实时更新，同时显示原始数据和平滑后数据的对比
- [ ] Verify in browser using dev-browser skill

### US-010: 切线调整控制面板
**Description:** 作为用户，我需要手动调整切线参数以获得准确的 As/Af 结果。

**Acceptance Criteria:**
- [ ] 在侧边栏添加"切线调整"折叠区域
- [ ] 提供低温基准线拟合区间的双端滑块（温度范围）
- [ ] 提供高温基准线拟合区间的双端滑块（温度范围）
- [ ] 提供中间切线位置偏移滑块（在自动检测最大斜率点附近 ±5°C 微调）
- [ ] 所有滑块的默认值由自动分析结果填充
- [ ] 参数变更后分析结果和图表实时更新
- [ ] Verify in browser using dev-browser skill

### US-011: 单通道切线分析图
**Description:** 作为用户，我需要看到完整的切线法分析图，包含三条切线和 As/Af 标注。

**Acceptance Criteria:**
- [ ] 在 `ui/analysis_chart.py` 中实现分析图组件
- [ ] 使用 Plotly 绘制：平滑后的温度-位移曲线（主曲线）
- [ ] 叠加显示：低温基准线（虚线）、高温基准线（虚线）、中间切线（虚线）
- [ ] 切线延长至与其他线的交点处
- [ ] 在 As 和 Af-tan 交点处标注圆点和温度数值
- [ ] 图表标题包含通道名称
- [ ] Verify in browser using dev-browser skill

### US-012: 结果显示面板
**Description:** 作为用户，我需要清楚地看到分析结果数值。

**Acceptance Criteria:**
- [ ] 在 `ui/results_panel.py` 中实现结果面板
- [ ] 使用 `st.metric` 组件显示 As 和 Af-tan 温度值（保留 1 位小数）
- [ ] 显示分析参数摘要（平滑窗口、基准线范围、最大斜率点温度）
- [ ] 当参数调整后结果实时更新
- [ ] Verify in browser using dev-browser skill

### US-013: 分析图表导出为图片
**Description:** 作为用户，我需要将分析图表下载为图片文件。

**Acceptance Criteria:**
- [ ] 在结果面板下方添加"导出图片"按钮
- [ ] 使用 Matplotlib 生成静态图（风格接近标准图5，含切线和 As/Af 标注）
- [ ] 点击按钮后自动下载 PNG 文件
- [ ] 图片分辨率不低于 300 DPI
- [ ] Verify in browser using dev-browser skill

### US-014: Excel 分析报告导出
**Description:** 作为用户，我需要导出包含完整分析记录的 Excel 报告。

**Acceptance Criteria:**
- [ ] 在 `core/report_export.py` 中实现 `export_excel_report()` 函数
- [ ] Excel 报告包含 Sheet1"分析结果"：样品文件名、通道、As、Af-tan、分析参数
- [ ] 包含 Sheet2"原始数据"：预处理后的温度-位移数据
- [ ] 包含 Sheet3"分析图表"：嵌入 Matplotlib 生成的分析图
- [ ] 在结果面板添加"导出报告"按钮，点击后下载 .xlsx 文件
- [ ] Verify in browser using dev-browser skill

## Functional Requirements

- FR-1: 支持加载 JSON、Excel (.xlsx)、CSV 三种格式的温度-位移数据
- FR-2: 自动检测数据中的有效通道（Space1~Space6），忽略全 NaN 的通道
- FR-3: 按温度分组对同温度下的多次采样求均值，消除重复采样点
- FR-3b: **自动检测并剔除传感器突刺等异常数据点**（滚动中位数 + MAD 阈值法），用线性插值修复，在平滑之前执行
- FR-4: 使用 Savitzky-Golay 滤波进行数据平滑，窗口大小和多项式阶数可调
- FR-5: 计算位移对温度的导数，定位绝对斜率最大的点作为中间切线位置
- FR-6: 对曲线低温段和高温段分别进行线性拟合，作为基准线
- FR-7: 计算中间切线与两条基准线的交点温度，得到 As 和 Af-tan
- FR-8: 提供交互式滑块调整：平滑参数、基准线拟合区间、中间切线位置偏移
- FR-9: 所有参数调整后图表和结果实时更新
- FR-10: 支持导出分析图表为 PNG 图片（≥300 DPI）
- FR-11: 支持导出 Excel 格式的分析报告（含结果、数据、图表）
- FR-12: **图表坐标轴范围自适应数据实际值域**，Y 轴和 X 轴范围滑块的上下限根据数据动态计算

## Non-Goals (Out of Scope)

- 不支持冷却曲线分析（仅处理升温曲线）
- 不支持两阶段相变分析（标准图6），仅处理单阶段（标准图5）
- 不生成 PDF 格式报告（仅 Excel + PNG）
- 不做自动批量处理多个文件（一次分析一个文件）
- 不做在线部署或多用户并发

## Design Considerations

- **视觉风格：** 深色毛玻璃（Dark Glassmorphism）+ 莫兰迪色系（Morandi Palette）
- **设计系统：** 详见 `design-system/af-analyzer/MASTER.md`
- **背景：** 深色 `#0F0F1A` + 径向渐变彩色光晕
- **卡片：** 半透明毛玻璃效果（`backdrop-filter: blur(20px)`）+ 大圆角（≥16px）
- **配色：** 莫兰迪蓝 `#8B9DC3`、玫 `#C4A4A4`、绿 `#A4B8A4`、杏 `#D4B896`
- **UI 布局：** 左侧边栏（文件上传 + 参数控制），右侧主区域（上方总览图 + 下方分析图 + 底部结果面板）
- **图表风格：** 分析图参考标准图5的风格，切线用莫兰迪色虚线，交点用圆点标记，标注温度值，Plotly 图表透明背景融入深色主题
- **字体：** Inter（正文）+ JetBrains Mono（数值显示）
- 中文界面，适合国内检验人员使用

## Technical Considerations

- Streamlit 的交互式更新通过 `st.session_state` 管理
- 大数据集（14万条记录）的预处理需注意性能，分组平均后数据量大幅减少
- Savitzky-Golay 滤波的 window_length 必须为奇数且大于 polyorder
- 使用 `pathlib.Path` 确保 Mac/Windows 路径兼容
- Plotly 图表用于交互浏览，Matplotlib 用于导出高质量静态图
- 异常值检测使用 MAD（中位绝对偏差）而非标准差，因为 MAD 对异常值更加鲁棒
- 预处理完整流程为：分组求均值 → 异常值检测剔除 → Savitzky-Golay 平滑
- 支持简化 Excel 格式（仅 Temperature + SpaceN，无 DateTimeStr），兼容不同设备导出格式
- UI 中所有坐标轴范围控件应根据实际数据值域动态设置上下限，避免硬编码

## Success Metrics

- 自动分析结果的 As/Af-tan 与人工目测结果偏差不超过 ±1°C
- 参数调整后图表更新延迟 < 1 秒
- 两组测试数据均能正确加载和分析
- 导出的 Excel 报告结构完整，可直接用于归档

## Open Questions

- 是否需要支持保存/加载分析参数配置（便于复现）？
- 后续是否需要支持两阶段相变（标准图6）分析？
- 是否需要支持批量处理多个文件？

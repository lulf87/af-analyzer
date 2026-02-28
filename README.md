# Af Analyzer — 奥氏体相变温度分析工具

基于 **YY/T 1771-2021** 标准第 11 章「相变温度的测定」，使用**切线法**从温度-形变量（位移）数据中计算奥氏体转变温度 As 和 Af-tan。

## 功能概览

- **多格式数据导入** — 支持 JSON、Excel (.xlsx)、CSV 三种格式
- **多通道总览** — 同时展示 Space1~Space6 共 6 个通道的温度-位移曲线
- **自动切线分析** — Savitzky-Golay 平滑 → 数值求导 → 自动定位最大斜率点 → 三线交点求解
- **交互式参数调整** — 平滑窗口/阶数、低温/高温基准线区间、中间切线偏移均可通过侧边栏滑块实时调整
- **结果导出** — 支持导出高清分析图 (PNG 300 DPI) 和结构化报告 (Excel)

## 分析原理

```
位移
 │        ╱‾‾‾‾‾‾‾‾  ← 高温基准线 (奥氏体相)
 │       ╱
 │      ╱  ← 中间切线 (最大斜率点)
 │     ╱
 │____╱               ← 低温基准线 (马氏体相)
 └──────────────────── 温度
      As         Af-tan
```

- **As**：中间切线与低温基准线的交点温度（奥氏体转变开始）
- **Af-tan**：中间切线与高温基准线的交点温度（奥氏体转变完成）

## 快速开始

### 环境要求

- Python >= 3.10
- 支持 macOS、Windows、Linux

### 安装

```bash
# 克隆项目
git clone https://github.com/lulf87/af-analyzer.git
cd af-analyzer

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

# 安装依赖
pip install -r requirements.txt
```

### 运行

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`，即可开始使用。

## 使用流程

1. **上传数据** — 在侧边栏点击「Browse files」上传测试数据文件
2. **选择通道** — 从下拉菜单选择要分析的通道（如 Space1）
3. **查看总览** — 多通道总览图展示所有有效通道，选中通道高亮显示
4. **调整参数**（可选）— 展开「数据预处理」和「切线调整」面板微调参数
5. **查看结果** — 分析图和结果面板自动显示 As、Af-tan 温度值
6. **导出报告** — 点击「导出分析图」或「导出分析报告」下载文件

## 数据格式

工具接受设备导出的标准数据格式，必须包含以下列：

| 列名 | 类型 | 说明 |
|------|------|------|
| `DateTimeStr` | string | 采集时间戳 |
| `Temperature` | float | 温度值 (°C) |
| `Space1` ~ `Space6` | float / "NaN" | 各通道位移值 |

JSON 示例：

```json
[
  {"DateTimeStr": "2025-05-07 10:24:52", "Temperature": 5.2, "Space1": 123.45, "Space2": "NaN", ...},
  {"DateTimeStr": "2025-05-07 10:24:53", "Temperature": 5.3, "Space1": 123.50, "Space2": "NaN", ...}
]
```

## 项目结构

```
.
├── app.py                  # Streamlit 主入口
├── core/
│   ├── data_loader.py      # 数据加载（JSON/Excel/CSV）
│   ├── preprocessing.py    # 数据预处理（分组、平滑）
│   ├── tangent_analysis.py # 切线法分析算法
│   └── report_export.py    # 报告导出（PNG/Excel）
├── ui/
│   ├── sidebar.py          # 侧边栏控件
│   ├── overview_chart.py   # 多通道总览图
│   ├── analysis_chart.py   # 切线分析图
│   └── results_panel.py    # 结果面板与导出
├── tests/
│   ├── test_data_loader.py
│   ├── test_preprocessing.py
│   └── test_tangent_analysis.py
├── design-system/
│   └── af-analyzer/MASTER.md  # UI 设计规范
├── .streamlit/config.toml  # Streamlit 主题配置
├── requirements.txt        # Python 依赖
└── README.md
```

## 算法参数说明

### 数据预处理

| 参数 | 默认值 | 范围 | 说明 |
|------|--------|------|------|
| 窗口大小 | 51 | 5 ~ 201（奇数） | Savitzky-Golay 滤波窗口，越大越平滑 |
| 多项式阶数 | 3 | 1 ~ 7 | 拟合多项式阶数，越大保留越多细节 |

### 切线调整

| 参数 | 默认值 | 说明 |
|------|--------|------|
| 低温基准线区间 | 温度范围前 15% | 马氏体相平缓区域，用于拟合低温基准线 |
| 高温基准线区间 | 温度范围后 15% | 奥氏体相平缓区域，用于拟合高温基准线 |
| 中间切线偏移 | 0 | 最大斜率点索引偏移量（正值→高温方向） |

## 运行测试

```bash
pytest tests/ -v
```

## 参考标准

- **YY/T 1771-2021** — 心血管植入物 镍钛合金管材和板材 奥氏体相变终了温度 Af 的测定

## 许可

本项目仅供内部研发使用。

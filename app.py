"""
Af Analyzer - 奥氏体相变温度分析工具

Main entry point for the Streamlit application.
Based on YY/T 1771-2021 Section 11: Determination of transformation temperatures.
"""

import streamlit as st
from ui.sidebar import render_sidebar, get_session_data
from ui.overview_chart import display_overview_section
from ui.analysis_chart import display_analysis_section, perform_analysis
from ui.results_panel import display_results_panel

# Page configuration
st.set_page_config(
    page_title="Af Analyzer - 奥氏体相变温度分析",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS based on design-system/af-analyzer/MASTER.md
# Style: Dark Glassmorphism + Morandi Palette
# Font: Inter (headings/body) + JetBrains Mono (monospace)
custom_css = """
<style>
/* Google Fonts Import - Inter + JetBrains Mono */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* === 全局深色背景 + 渐变光晕 === */
.stApp {
  background: #0F0F1A;
  background-image:
    radial-gradient(ellipse at 20% 50%, rgba(139, 157, 195, 0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(196, 164, 164, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(164, 184, 164, 0.06) 0%, transparent 50%);
}

/* === 侧边栏深色玻璃 === */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, rgba(26, 26, 46, 0.95) 0%, rgba(22, 22, 42, 0.98) 100%);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

[data-testid="stSidebar"] [data-testid="stMarkdown"] {
  color: #E8E4E0;
}

/* === 主区域文字颜色 === */
.stApp [data-testid="stMarkdown"] h1,
.stApp [data-testid="stMarkdown"] h2,
.stApp [data-testid="stMarkdown"] h3 {
  color: #F0ECE8 !important;
}

.stApp [data-testid="stMarkdown"] p,
.stApp [data-testid="stMarkdown"] li {
  color: #C8C0B8 !important;
}

/* === 毛玻璃卡片（用于包裹图表和结果区域）=== */
[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255, 255, 255, 0.05) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08) !important;
  border-radius: 20px !important;
  padding: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

/* === Expander 折叠面板 === */
[data-testid="stExpander"] {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
}

[data-testid="stExpander"] summary {
  color: #E8E4E0;
}

/* === Metric 数值卡片 === */
[data-testid="stMetric"] {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 20px;
  padding: 20px;
  text-align: center;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
  font-family: 'JetBrains Mono', monospace;
  color: #F0ECE8;
}

[data-testid="stMetric"] [data-testid="stMetricLabel"] {
  color: #8A8A9A;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-size: 0.8rem;
}

/* === 按钮 === */
.stButton > button {
  background: linear-gradient(135deg, rgba(139,157,195,0.3) 0%, rgba(139,157,195,0.15) 100%) !important;
  color: #E8E4E0 !important;
  border: 1px solid rgba(139,157,195,0.3) !important;
  border-radius: 12px !important;
  backdrop-filter: blur(10px);
  transition: all 250ms ease;
}

.stButton > button:hover {
  background: linear-gradient(135deg, rgba(139,157,195,0.4) 0%, rgba(139,157,195,0.25) 100%) !important;
  border-color: rgba(139,157,195,0.5) !important;
  box-shadow: 0 4px 16px rgba(139,157,195,0.2);
}

/* === 文件上传区域 === */
[data-testid="stFileUploader"] {
  border-radius: 16px;
}

[data-testid="stFileUploader"] > div {
  background: rgba(255,255,255,0.03);
  border: 2px dashed rgba(255,255,255,0.12);
  border-radius: 16px;
}

/* === 选择框 === */
[data-testid="stSelectbox"] > div > div {
  background: rgba(255,255,255,0.05);
  border-color: rgba(255,255,255,0.12);
  border-radius: 12px;
  color: #E8E4E0;
}

/* === 滑块 === */
[data-testid="stSlider"] label {
  color: #C8C0B8 !important;
}

/* === 分割线 === */
hr {
  border-color: rgba(255,255,255,0.06) !important;
}

/* === 隐藏 Streamlit 默认的 header/footer === */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* === Info/Warning/Success boxes === */
[data-testid="stAlert"] {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

[data-testid="stAlert"] p {
  color: #C8C0B8 !important;
}

/* === Typography === */
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #E8E4E0;
}

h1, h2, h3, h4, h5, h6 {
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  color: #F0ECE8;
}
</style>
"""

# Inject custom CSS
st.markdown(custom_css, unsafe_allow_html=True)

# Render sidebar (handles file upload and channel selection)
file_name, selected_channel = render_sidebar()

# Main content area
st.title("奥氏体相变温度分析工具")
st.markdown("---")

# Show welcome or analysis interface based on state
if file_name and selected_channel:
    # Data is loaded - show analysis interface
    _, _, df = get_session_data()
    valid_channels = st.session_state.get("valid_channels", [])

    st.subheader("数据分析")

    # Display data summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("数据文件", file_name[:20] + "..." if len(file_name) > 20 else file_name)
    with col2:
        st.metric("选中通道", selected_channel)
    with col3:
        temp_min, temp_max = df["Temperature"].min(), df["Temperature"].max()
        st.metric("温度范围", f"{temp_min:.1f}°C ~ {temp_max:.1f}°C")

    st.markdown("---")

    # Overview chart showing all channels
    display_overview_section(df, valid_channels, selected_channel)

    st.markdown("---")

    # Single-channel tangent analysis chart
    display_analysis_section(df, selected_channel)

    st.markdown("---")

    # Results panel with detailed metrics
    # Get analysis result from session state
    result = st.session_state.get("analysis_result")
    if result is not None:
        display_results_panel(result, selected_channel)

    st.markdown("---")

else:
    # No data loaded - show welcome message
    st.markdown("### 欢迎使用奥氏体相变温度分析工具")
    st.markdown("""
    本工具基于 **YY/T 1771-2021** 标准第 11 章「相变温度的测定」，使用**切线法」
    从温度-形变量（位移）数据中计算奥氏体转变温度 As 和 Af-tan。

    #### 功能说明

    - 支持多通道温度-位移数据导入
    - 自动数据预处理（分组、平滑滤波）
    - 交互式切线法分析
    - 分析结果导出（Excel/PNG）

    #### 使用流程

    1. 在侧边栏上传测试数据文件
    2. 选择要分析的通道
    3. 调整分析参数
    4. 查看分析结果
    5. 导出分析报告

    ---
    **请在侧边栏上传数据文件开始分析**
    """)

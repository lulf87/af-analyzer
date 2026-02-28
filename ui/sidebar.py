"""
Sidebar component for Af Analyzer.

Handles file upload, channel selection, and preprocessing parameters.
"""

import numpy as np
import streamlit as st
from pathlib import Path
from typing import Optional

from core.data_loader import load_file, detect_valid_channels, SUPPORTED_EXTENSIONS


# Default preprocessing parameters
DEFAULT_WINDOW_LENGTH = 51
DEFAULT_POLYORDER = 3


def render_sidebar() -> tuple[Optional[str], Optional[str]]:
    """
    Render the sidebar with file upload and channel selection.

    This function manages:
    - File upload (JSON, Excel, CSV)
    - Data loading and validation
    - Channel selection
    - Session state management

    Session state keys used:
    - uploaded_file: The uploaded file object
    - df: Loaded DataFrame
    - valid_channels: List of valid channel names
    - selected_channel: Currently selected channel

    Returns:
        Tuple of (file_name, selected_channel) or (None, None) if not ready

    Example:
        >>> file_name, channel = render_sidebar()
        >>> if file_name and channel:
        >>>     # Proceed with analysis
        """
    with st.sidebar:
        st.header("控制面板")

        # Data Import Section
        st.subheader("数据导入")

        # File upload with support for JSON, Excel, CSV
        uploaded_file = st.file_uploader(
            label="上传测试数据文件",
            type=list(SUPPORTED_EXTENSIONS.keys()),
            label_visibility="collapsed",
            help="支持 JSON、Excel (.xlsx)、CSV 格式"
        )

        # Handle file upload
        if uploaded_file is not None:
            # Check if file has changed
            if ("uploaded_file_name" not in st.session_state or
                st.session_state.uploaded_file_name != uploaded_file.name):

                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.uploaded_file = uploaded_file

                try:
                    # Load data based on file type (pass file name for format detection)
                    file_bytes = uploaded_file.read()
                    df = load_file(file_bytes, file_name=uploaded_file.name)

                    # Validate required columns
                    if "Temperature" not in df.columns:
                        st.error(f"文件缺少必需的 'Temperature' 列")
                        return None, None

                    # Detect valid channels
                    valid_channels = detect_valid_channels(df)

                    if not valid_channels:
                        st.error("未找到有效的通道数据（Space1~Space6 全为空）")
                        return None, None

                    # Store in session state
                    st.session_state.df = df
                    st.session_state.valid_channels = valid_channels

                    # Set default selected channel
                    if "selected_channel" not in st.session_state:
                        st.session_state.selected_channel = valid_channels[0]

                    st.success(f"成功加载 {len(valid_channels)} 个通道")

                except Exception as e:
                    st.error(f"文件加载失败: {str(e)}")
                    return None, None

            # Show file info
            st.info(f"已加载: `{st.session_state.uploaded_file_name}`")

        # Channel Selection Section
        st.subheader("通道选择")

        if "valid_channels" in st.session_state and st.session_state.valid_channels:
            valid_channels = st.session_state.valid_channels

            # Find current index
            current_idx = 0
            if "selected_channel" in st.session_state:
                try:
                    current_idx = valid_channels.index(st.session_state.selected_channel)
                except ValueError:
                    current_idx = 0

            # Channel selector
            selected_channel = st.selectbox(
                label="选择要分析的通道",
                options=valid_channels,
                index=current_idx,
                label_visibility="collapsed",
                key="channel_selector"
            )

            # Update session state
            st.session_state.selected_channel = selected_channel

            # Show channel info
            df = st.session_state.df
            temp_range = df["Temperature"].min(), df["Temperature"].max()
            data_points = len(df)

            st.caption(
                f"温度范围: {temp_range[0]:.1f}°C ~ {temp_range[1]:.1f}°C\n"
                f"数据点: {data_points} 个"
            )

        else:
            st.info("请先上传数据文件")
            return None, None

        # Analysis Parameters Section
        st.markdown("---")
        st.subheader("分析参数")

        # Data Preprocessing Section (US-010)
        with st.expander("数据预处理", expanded=False):
            st.caption("Savitzky-Golay 平滑滤波参数")

            # Window length slider (5-201, step 2, default 51)
            # Initialize session state if not exists
            if "smooth_window" not in st.session_state:
                st.session_state.smooth_window = DEFAULT_WINDOW_LENGTH

            smooth_window = st.slider(
                label="窗口大小",
                min_value=5,
                max_value=201,
                value=st.session_state.smooth_window,
                step=2,
                help="滤波窗口长度，必须为奇数。值越大平滑效果越强。"
            )

            # Update session state
            if smooth_window != st.session_state.smooth_window:
                st.session_state.smooth_window = smooth_window
                # Trigger re-analysis by clearing cached results
                if "smoothed_data" in st.session_state:
                    del st.session_state.smoothed_data

            # Polyorder slider (1-7, default 3)
            if "smooth_polyorder" not in st.session_state:
                st.session_state.smooth_polyorder = DEFAULT_POLYORDER

            # Ensure window_length > polyorder for validation
            max_polyorder = min(7, smooth_window - 2)
            default_polyorder = min(DEFAULT_POLYORDER, max_polyorder)

            smooth_polyorder = st.slider(
                label="多项式阶数",
                min_value=1,
                max_value=max_polyorder,
                value=default_polyorder,
                step=1,
                help="拟合多项式阶数。值越大保留更多细节，但可能过拟合。"
            )

            # Update session state
            if smooth_polyorder != st.session_state.smooth_polyorder:
                st.session_state.smooth_polyorder = smooth_polyorder
                # Trigger re-analysis
                if "smoothed_data" in st.session_state:
                    del st.session_state.smoothed_data

            # Display current values
            st.caption(f"当前参数: 窗口={smooth_window}, 阶数={smooth_polyorder}")

            # Add info about the filter
            with st.container():
                st.info("""
                **Savitzky-Golay 滤波器**

                通过滑动窗口多项式拟合进行数据平滑，保留峰形特征。

                - **窗口大小**: 控制平滑强度，值越大越平滑
                - **多项式阶数**: 控制拟合复杂度，通常 2-4
                """)

        # Tangent Adjustment Section (US-011)
        with st.expander("切线调整", expanded=False):
            st.caption("基准线范围和中间切线偏移控制")

            # Get temperature range for default values
            temp_min = df["Temperature"].min()
            temp_max = df["Temperature"].max()
            temp_span = temp_max - temp_min

            # Initialize session state for tangent parameters
            if "low_temp_range" not in st.session_state:
                # Default: first 15% of temperature range
                low_default_start = temp_min
                low_default_end = temp_min + temp_span * 0.15
                st.session_state.low_temp_range = (low_default_start, low_default_end)

            if "high_temp_range" not in st.session_state:
                # Default: last 15% of temperature range
                high_default_start = temp_max - temp_span * 0.15
                high_default_end = temp_max
                st.session_state.high_temp_range = (high_default_start, high_default_end)

            if "slope_offset" not in st.session_state:
                st.session_state.slope_offset = 0

            # Low-temperature baseline range slider (dual-ended)
            low_range = st.slider(
                label="低温基准线区间 (°C)",
                min_value=float(temp_min),
                max_value=float(temp_max),
                value=st.session_state.low_temp_range,
                step=0.1,
                help="马氏体相区域的温度范围，用于拟合低温基准线"
            )

            # Update session state
            if low_range != st.session_state.low_temp_range:
                st.session_state.low_temp_range = low_range
                # Clear analysis cache
                if "analysis_result" in st.session_state:
                    del st.session_state.analysis_result

            # High-temperature baseline range slider (dual-ended)
            high_range = st.slider(
                label="高温基准线区间 (°C)",
                min_value=float(temp_min),
                max_value=float(temp_max),
                value=st.session_state.high_temp_range,
                step=0.1,
                help="奥氏体相区域的温度范围，用于拟合高温基准线"
            )

            # Update session state
            if high_range != st.session_state.high_temp_range:
                st.session_state.high_temp_range = high_range
                # Clear analysis cache
                if "analysis_result" in st.session_state:
                    del st.session_state.analysis_result

            # Middle tangent offset slider
            slope_offset = st.slider(
                label="中间切线偏移",
                min_value=-20,
                max_value=20,
                value=st.session_state.slope_offset,
                step=1,
                help="最大斜率点的索引偏移。正值向高温方向偏移，负值向低温方向偏移。"
            )

            # Update session state
            if slope_offset != st.session_state.slope_offset:
                st.session_state.slope_offset = slope_offset
                # Clear analysis cache
                if "analysis_result" in st.session_state:
                    del st.session_state.analysis_result

            # Display current values
            st.caption(f"低温区间: {low_range[0]:.1f}°C ~ {low_range[1]:.1f}°C")
            st.caption(f"高温区间: {high_range[0]:.1f}°C ~ {high_range[1]:.1f}°C")
            st.caption(f"切线偏移: {slope_offset:+d}")

            # Add info about the tangent method
            with st.container():
                st.info("""
                **切线法参数说明**

                - **低温基准线**: 马氏体相平缓区域的线性拟合
                - **高温基准线**: 奥氏体相平缓区域的线性拟合
                - **中间切线偏移**: 手动调整最大斜率点位置

                As = 中间切线 ∩ 低温基准线
                Af-tan = 中间切线 ∩ 高温基准线
                """)

        # Chart Settings Section
        with st.expander("图表设置", expanded=False):
            st.caption("调整分析图表的坐标轴显示")

            # Get temperature range for defaults
            temp_min = df["Temperature"].min()
            temp_max = df["Temperature"].max()

            # Get value range from valid channels for Y-axis
            # Find all Space columns and get the overall min/max
            space_cols = [col for col in df.columns if col.startswith("Space")]
            if space_cols:
                # Get valid values (non-NaN) from all space columns
                all_values = df[space_cols].values.flatten()
                all_values = all_values[~np.isnan(all_values)]
                if len(all_values) > 0:
                    value_min = float(np.min(all_values))
                    value_max = float(np.max(all_values))
                    # Add 10% margin
                    value_margin = (value_max - value_min) * 0.1
                    value_min_with_margin = value_min - value_margin
                    value_max_with_margin = value_max + value_margin
                else:
                    value_min_with_margin = 0.0
                    value_max_with_margin = 500.0
            else:
                value_min_with_margin = 0.0
                value_max_with_margin = 500.0

            # Initialize session state for axis tick parameters
            if "x_axis_tick" not in st.session_state:
                st.session_state.x_axis_tick = 0  # 0 means auto
            if "y_axis_tick" not in st.session_state:
                st.session_state.y_axis_tick = 0  # 0 means auto
            if "x_axis_range" not in st.session_state:
                st.session_state.x_axis_range = None  # None means auto
            if "y_axis_range" not in st.session_state:
                st.session_state.y_axis_range = None  # None means auto

            # X-axis tick interval
            x_tick_options = {
                "自动": 0,
                "1 °C": 1,
                "2 °C": 2,
                "5 °C": 5,
                "10 °C": 10,
            }
            x_tick_labels = list(x_tick_options.keys())
            x_tick_current_idx = 0
            for i, (label, val) in enumerate(x_tick_options.items()):
                if st.session_state.x_axis_tick == val:
                    x_tick_current_idx = i
                    break

            x_tick_selection = st.selectbox(
                label="X轴刻度间隔",
                options=x_tick_labels,
                index=x_tick_current_idx,
                help="选择温度轴的刻度间隔，'自动'由 Plotly 自动选择最佳间隔"
            )
            x_axis_tick = x_tick_options[x_tick_selection]
            if x_axis_tick != st.session_state.x_axis_tick:
                st.session_state.x_axis_tick = x_axis_tick

            # Y-axis tick interval
            y_tick_options = {
                "自动": 0,
                "10": 10,
                "20": 20,
                "50": 50,
                "100": 100,
                "200": 200,
            }
            y_tick_labels = list(y_tick_options.keys())
            y_tick_current_idx = 0
            for i, (label, val) in enumerate(y_tick_options.items()):
                if st.session_state.y_axis_tick == val:
                    y_tick_current_idx = i
                    break

            y_tick_selection = st.selectbox(
                label="Y轴刻度间隔",
                options=y_tick_labels,
                index=y_tick_current_idx,
                help="选择位移轴的刻度间隔，'自动'由 Plotly 自动选择最佳间隔"
            )
            y_axis_tick = y_tick_options[y_tick_selection]
            if y_axis_tick != st.session_state.y_axis_tick:
                st.session_state.y_axis_tick = y_axis_tick

            st.markdown("---")
            st.markdown("**坐标轴范围**")

            # X-axis range with dynamic bounds
            x_range_enabled = st.checkbox(
                "自定义X轴范围",
                value=st.session_state.x_axis_range is not None,
                help="勾选后可手动设置X轴的最小值和最大值"
            )

            # Calculate X-axis bounds with margin
            temp_margin = (temp_max - temp_min) * 0.1
            x_slider_min = float(temp_min) - temp_margin
            x_slider_max = float(temp_max) + temp_margin

            if x_range_enabled:
                default_x_range = st.session_state.x_axis_range or [float(temp_min), float(temp_max)]
                x_range = st.slider(
                    label="X轴范围 (°C)",
                    min_value=x_slider_min,
                    max_value=x_slider_max,
                    value=default_x_range,
                    step=0.5,
                    help="拖动设置温度轴的显示范围"
                )
                st.session_state.x_axis_range = x_range
            else:
                st.session_state.x_axis_range = None

            # Y-axis range with dynamic bounds based on actual data
            y_range_enabled = st.checkbox(
                "自定义Y轴范围",
                value=st.session_state.y_axis_range is not None,
                help="勾选后可手动设置Y轴的最小值和最大值"
            )

            if y_range_enabled:
                default_y_range = st.session_state.y_axis_range or [value_min_with_margin, value_max_with_margin]
                y_range = st.slider(
                    label="Y轴范围",
                    min_value=value_min_with_margin,
                    max_value=value_max_with_margin,
                    value=default_y_range,
                    step=10.0,
                    help="拖动设置位移轴的显示范围"
                )
                st.session_state.y_axis_range = y_range
            else:
                st.session_state.y_axis_range = None

            # Auto-fit button
            if st.button("🔄 自动适应数据范围", help="自动缩放到曲线的有效数据范围"):
                # Get analysis result to calculate optimal range
                if "analysis_result" in st.session_state and st.session_state.analysis_result:
                    result = st.session_state.analysis_result
                    temps = result.get("temps_smooth", [])
                    values = result.get("values_smooth", [])
                    if len(temps) > 0 and len(values) > 0:
                        # Calculate range with 5% margin
                        x_min, x_max = float(temps.min()), float(temps.max())
                        y_min, y_max = float(values.min()), float(values.max())
                        x_margin = (x_max - x_min) * 0.05
                        y_margin = (y_max - y_min) * 0.1
                        st.session_state.x_axis_range = [x_min - x_margin, x_max + x_margin]
                        st.session_state.y_axis_range = [y_min - y_margin, y_max + y_margin]
                        st.session_state.x_axis_range_enabled = True
                        st.session_state.y_axis_range_enabled = True
                        st.rerun()
                else:
                    st.warning("请先完成数据分析")

            # Display current settings
            x_display = "自动" if x_axis_tick == 0 else f"{x_axis_tick} °C"
            y_display = "自动" if y_axis_tick == 0 else str(y_axis_tick)
            st.caption(f"刻度: X={x_display} | Y={y_display}")

        # Return current state
        file_name = st.session_state.get("uploaded_file_name")
        selected_channel = st.session_state.get("selected_channel")

        return file_name, selected_channel


def get_session_data() -> tuple[Optional[str], Optional[str], Optional["pd.DataFrame"]]:
    """
    Get current session data (file name, channel, DataFrame).

    Returns:
        Tuple of (file_name, selected_channel, df) or (None, None, None)
    """
    file_name = st.session_state.get("uploaded_file_name")
    selected_channel = st.session_state.get("selected_channel")
    df = st.session_state.get("df")

    return file_name, selected_channel, df


def get_smooth_params() -> tuple[int, int]:
    """
    Get current smoothing parameters from session state.

    Returns:
        Tuple of (window_length, polyorder)
    """
    window_length = st.session_state.get("smooth_window", DEFAULT_WINDOW_LENGTH)
    polyorder = st.session_state.get("smooth_polyorder", DEFAULT_POLYORDER)
    return window_length, polyorder


def get_tangent_params() -> tuple[tuple[float, float], tuple[float, float], int]:
    """
    Get current tangent adjustment parameters from session state.

    Returns:
        Tuple of (low_range, high_range, slope_offset)
        - low_range: (t_start, t_end) for low-temperature baseline
        - high_range: (t_start, t_end) for high-temperature baseline
        - slope_offset: Index offset for max slope point
    """
    low_range = st.session_state.get("low_temp_range", (0.0, 5.0))
    high_range = st.session_state.get("high_temp_range", (20.0, 25.0))
    slope_offset = st.session_state.get("slope_offset", 0)
    return low_range, high_range, slope_offset


def get_axis_tick_params() -> tuple[float, float]:
    """
    Get current axis tick interval parameters from session state.

    Returns:
        Tuple of (x_axis_tick, y_axis_tick)
        - x_axis_tick: Temperature axis tick interval (0 = auto)
        - y_axis_tick: Displacement axis tick interval (0 = auto)
    """
    x_axis_tick = st.session_state.get("x_axis_tick", 0)
    y_axis_tick = st.session_state.get("y_axis_tick", 0)
    return x_axis_tick, y_axis_tick


def get_axis_range_params() -> tuple[Optional[tuple[float, float]], Optional[tuple[float, float]]]:
    """
    Get current axis range parameters from session state.

    Returns:
        Tuple of (x_axis_range, y_axis_range)
        - x_axis_range: (min, max) for X axis or None for auto
        - y_axis_range: (min, max) for Y axis or None for auto
    """
    x_axis_range = st.session_state.get("x_axis_range")
    y_axis_range = st.session_state.get("y_axis_range")
    return x_axis_range, y_axis_range

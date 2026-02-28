"""
Results panel component for Af Analyzer.

Displays analysis results with metrics and parameter summary.
"""

import streamlit as st
import numpy as np
from ui.sidebar import get_smooth_params, get_tangent_params
from core.report_export import generate_analysis_figure, figure_to_png_bytes, export_excel_report


def display_results_panel(result: dict, channel: str):
    """
    Display the analysis results panel with metrics and parameter summary.

    Args:
        result: Analysis result dictionary from perform_analysis
        channel: Channel name for display
    """
    st.subheader("分析结果")

    if result is None:
        st.warning("暂无分析结果，请等待分析完成")
        return

    # Check for incomplete analysis
    as_valid = "As" in result and not np.isnan(result["As"])
    af_valid = "Af_tan" in result and not np.isnan(result["Af_tan"])

    if not as_valid or not af_valid:
        missing = []
        if not as_valid:
            missing.append("As")
        if not af_valid:
            missing.append("Af-tan")
        st.warning(f"⚠ 部分分析结果缺失: {', '.join(missing)}。请尝试调整切线参数。")

    # Main metrics row
    col1, col2, col3 = st.columns(3)

    with col1:
        if "As" in result and not np.isnan(result["As"]):
            st.metric(
                label="As (奥氏体开始)",
                value=f"{result['As']:.1f} °C",
                help="奥氏体转变开始温度 - 中间切线与低温基准线的交点"
            )
        else:
            st.metric("As (奥氏体开始)", "N/A")

    with col2:
        if "Af_tan" in result and not np.isnan(result["Af_tan"]):
            st.metric(
                label="Af-tan (奥氏体完成)",
                value=f"{result['Af_tan']:.1f} °C",
                help="奥氏体转变完成温度（切线法）- 中间切线与高温基准线的交点"
            )
        else:
            st.metric("Af-tan (奥氏体完成)", "N/A")

    with col3:
        if "max_slope_temp" in result and not np.isnan(result["max_slope_temp"]):
            delta = result.get("Af_tan", np.nan) - result.get("As", np.nan)
            if not np.isnan(delta):
                st.metric(
                    label="转变区间 (ΔT)",
                    value=f"{delta:.1f} °C",
                    help=f"奥氏体转变温度范围: Af-tan - As"
                )
            else:
                st.metric("最大斜率点", f"{result['max_slope_temp']:.1f} °C")
        else:
            st.metric("最大斜率点", "N/A")

    st.markdown("---")

    # Analysis parameters summary
    st.subheader("分析参数")

    # Get current parameters
    smooth_window, smooth_polyorder = get_smooth_params()
    low_range, high_range, slope_offset = get_tangent_params()

    # Display parameters in a structured format
    param_col1, param_col2 = st.columns(2)

    with param_col1:
        st.markdown("**数据预处理**")
        st.caption(f"平滑窗口: {smooth_window}")
        st.caption(f"多项式阶数: {smooth_polyorder}")

    with param_col2:
        st.markdown("**切线调整**")
        st.caption(f"低温基准线: {low_range[0]:.1f}°C ~ {low_range[1]:.1f}°C")
        st.caption(f"高温基准线: {high_range[0]:.1f}°C ~ {high_range[1]:.1f}°C")
        st.caption(f"切线偏移: {slope_offset:+d}")

    st.markdown("---")

    # Additional info
    if not np.isnan(result.get("As", np.nan)) and not np.isnan(result.get("Af_tan", np.nan)):
        as_temp = result["As"]
        af_temp = result["Af_tan"]
        max_slope_temp = result.get("max_slope_temp", np.nan)

        info_text = f"""
        **分析说明**

        - **As = {as_temp:.1f}°C**: 中间切线与低温基准线（马氏体相）的交点温度
        - **Af-tan = {af_temp:.1f}°C**: 中间切线与高温基准线（奥氏体相）的交点温度
        """

        if not np.isnan(max_slope_temp):
            info_text += f"- **最大斜率点 = {max_slope_temp:.1f}°C**: 曲线斜率绝对值最大的温度点\n"

        st.info(info_text)

    st.markdown("---")

    # Export section
    st.subheader("导出")

    # Generate PNG figure for download
    try:
        fig = generate_analysis_figure(
            temps=result.get("temps_smooth", np.array([])),
            values=result.get("values_smooth", np.array([])),
            As=result.get("As", np.nan),
            Af_tan=result.get("Af_tan", np.nan),
            max_slope_temp=result.get("max_slope_temp", np.nan),
            low_baseline=result.get("low_baseline", (0, 0)),
            high_baseline=result.get("high_baseline", (0, 0)),
            tangent=result.get("tangent", (0, 0)),
            channel_name=channel
        )

        # Convert to PNG bytes
        png_bytes = figure_to_png_bytes(fig, dpi=300)

        # Download button
        filename = f"{channel}_analysis.png"
        st.download_button(
            label="导出分析图 (PNG)",
            data=png_bytes,
            file_name=filename,
            mime="image/png",
            help="下载 300 DPI 高清分析图"
        )

        # Close figure to free memory
        import matplotlib.pyplot as plt
        plt.close(fig)

    except Exception as e:
        st.warning(f"PNG 导出功能暂时不可用: {str(e)}")

    # Excel export
    try:
        # Get file name from session state
        file_name = st.session_state.get("uploaded_file_name", "data")

        excel_bytes = export_excel_report(
            file_name=file_name,
            channel=channel,
            result=result,
            smooth_params=(smooth_window, smooth_polyorder),
            low_range=low_range,
            high_range=high_range,
            slope_offset=slope_offset
        )

        # Download button
        excel_filename = f"{channel}_report.xlsx"
        st.download_button(
            label="导出分析报告 (Excel)",
            data=excel_bytes,
            file_name=excel_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="下载包含分析结果和处理数据的 Excel 报告"
        )

    except Exception as e:
        st.warning(f"Excel 导出功能暂时不可用: {str(e)}")

"""
Analysis chart component for Af Analyzer.

Displays the single-channel tangent analysis chart with:
- Smoothed temperature-displacement curve
- Three tangent lines (low baseline, high baseline, middle tangent)
- As and Af-tan intersection points with annotations
- Zoom state persistence across parameter changes
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_plotly_events import plotly_events

from core.preprocessing import group_by_temperature, smooth_data, remove_outliers
from core.tangent_analysis import analyze_channel
from ui.sidebar import get_smooth_params, get_tangent_params, get_axis_tick_params, get_axis_range_params

# Chart colors from design-system/af-analyzer/MASTER.md (Morandi Palette)
CHART_COLORS = {
    "primary": "#8B9DC3",      # Morandi Blue - main curve
    "highlight": "#E8E4E0",    # Light white for selected
    "anomaly": "#C4A4A4",      # Morandi Rose
    "grid": "rgba(255,255,255,0.06)",
    "axis_text": "#8A8A9A",
    "text": "#E8E4E0",
}

# Tangent line colors (Morandi series)
TANGENT_COLORS = {
    "low_baseline": "#A4B8A4",   # Morandi Green - low temperature baseline
    "high_baseline": "#D4B896",  # Morandi Apricot - high temperature baseline
    "middle_tangent": "#C4A4A4", # Morandi Rose - middle tangent line
}

# As/Af marker colors
MARKER_COLORS = {
    "as_marker": "#A4B8A4",      # Green for As
    "af_marker": "#D4B896",      # Apricot for Af-tan
}

# Plotly layout configuration for dark glassmorphism theme
PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(255,255,255,0.03)',
    font=dict(
        family='Inter, sans-serif',
        color='#E8E4E0',
        size=13
    ),
)

# Annotation style for As/Af labels
ANNOTATION_STYLE = dict(
    font=dict(
        family='JetBrains Mono, monospace',
        size=13,
        color='#F0ECE8',
    ),
    bgcolor='rgba(26, 26, 46, 0.85)',
    bordercolor='rgba(255,255,255,0.15)',
    borderwidth=1,
    borderpad=6,
)

MARKER_STYLE = dict(
    size=10,
    line=dict(width=2, color='rgba(255,255,255,0.6)'),
)


def perform_analysis(df: pd.DataFrame, channel: str):
    """
    Perform complete tangent analysis on a channel.

    Args:
        df: Raw DataFrame with Temperature and channel columns
        channel: Channel name to analyze

    Returns:
        Dictionary with analysis results or None if failed
    """
    try:
        # Get parameters from sidebar
        smooth_window, smooth_polyorder = get_smooth_params()
        low_range, high_range, slope_offset = get_tangent_params()

        # Step 1: Group by temperature
        grouped = group_by_temperature(df, channel)
        temps = grouped["Temperature"].values
        values = grouped[channel].values

        # Step 2: Perform analysis (internally: remove_outliers → smooth → tangent)
        result = analyze_channel(
            temps=temps,
            values=values,
            low_range=low_range,
            high_range=high_range,
            smooth_params=(smooth_window, smooth_polyorder),
            slope_offset=slope_offset
        )

        # Step 3: Generate plotting data using the SAME pipeline as analyze_channel
        # Must go through outlier removal first to avoid Savitzky-Golay ringing artifacts
        temps_clean, values_clean, outlier_mask = remove_outliers(temps, values)
        temps_smooth, values_smooth = smooth_data(
            temps_clean, values_clean, smooth_window, smooth_polyorder
        )
        result["temps_smooth"] = temps_smooth
        result["values_smooth"] = values_smooth
        result["temps_raw"] = temps
        result["values_raw"] = values
        result["outlier_mask"] = outlier_mask

        return result

    except Exception as e:
        st.error(f"分析失败: {str(e)}")
        return None


def render_analysis_chart(result: dict, channel: str) -> go.Figure:
    """
    Render the tangent analysis chart with all lines and annotations.

    Args:
        result: Analysis result dictionary from perform_analysis
        channel: Channel name for title

    Returns:
        Plotly Figure object
    """
    if result is None:
        # Return empty chart
        fig = go.Figure()
        fig.add_annotation(
            text="分析失败 - 请检查参数或数据",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color=CHART_COLORS["axis_text"])
        )
        return fig

    # Extract data
    temps = result["temps_smooth"]
    values = result["values_smooth"]
    temp_min, temp_max = temps.min(), temps.max()
    temp_margin = (temp_max - temp_min) * 0.1

    # Extract line parameters
    low_slope, low_intercept = result["low_baseline"]
    high_slope, high_intercept = result["high_baseline"]
    tangent_slope, tangent_intercept = result["tangent"]

    # Calculate intersection temperatures
    As = result["As"]
    Af_tan = result["Af_tan"]
    max_slope_temp = result["max_slope_temp"]

    # Create figure
    fig = go.Figure()

    # 1. Main curve (smoothed) - solid line, Morandi Blue
    fig.add_trace(go.Scatter(
        x=temps,
        y=values,
        mode="lines",
        name="平滑曲线",
        line=dict(color=CHART_COLORS["primary"], width=3),
        hovertemplate="<b>平滑曲线</b><br>" +
                     "Temperature: %{x:.2f}°C<br>" +
                     "Displacement: %{y:.2f}<br>" +
                     "<extra></extra>"
    ))

    # 2. Low-temperature baseline - dashed line, Morandi Green
    # Extend from min temperature to As intersection
    if not np.isnan(As):
        low_x = np.array([temp_min, As])
    else:
        low_x = np.array([temp_min, temp_min + temp_margin])
    low_y = low_slope * low_x + low_intercept

    fig.add_trace(go.Scatter(
        x=low_x,
        y=low_y,
        mode="lines",
        name="低温基准线",
        line=dict(color=TANGENT_COLORS["low_baseline"], width=2, dash="dash"),
        hovertemplate="<b>低温基准线</b><br>" +
                     "Temperature: %{x:.2f}°C<br>" +
                     "Value: %{y:.2f}<br>" +
                     "<extra></extra>"
    ))

    # 3. High-temperature baseline - dashed line, Morandi Apricot
    # Extend from Af-tan to max temperature
    if not np.isnan(Af_tan):
        high_x = np.array([Af_tan, temp_max])
    else:
        high_x = np.array([temp_max - temp_margin, temp_max])
    high_y = high_slope * high_x + high_intercept

    fig.add_trace(go.Scatter(
        x=high_x,
        y=high_y,
        mode="lines",
        name="高温基准线",
        line=dict(color=TANGENT_COLORS["high_baseline"], width=2, dash="dash"),
        hovertemplate="<b>高温基准线</b><br>" +
                     "Temperature: %{x:.2f}°C<br>" +
                     "Value: %{y:.2f}<br>" +
                     "<extra></extra>"
    ))

    # 4. Middle tangent line - dashed line, Morandi Rose
    # Extend through all temperature range
    tangent_x = np.array([temp_min, temp_max])
    tangent_y = tangent_slope * tangent_x + tangent_intercept

    fig.add_trace(go.Scatter(
        x=tangent_x,
        y=tangent_y,
        mode="lines",
        name="中间切线",
        line=dict(color=TANGENT_COLORS["middle_tangent"], width=2, dash="dash"),
        hovertemplate="<b>中间切线</b><br>" +
                     "Temperature: %{x:.2f}°C<br>" +
                     "Value: %{y:.2f}<br>" +
                     "<extra></extra>"
    ))

    # 5. As intersection point marker - Morandi Green
    if not np.isnan(As):
        as_y = tangent_slope * As + tangent_intercept
        fig.add_trace(go.Scatter(
            x=[As],
            y=[as_y],
            mode="markers+text",
            name="As 点",
            marker=dict(
                size=15,
                color=MARKER_COLORS["as_marker"],
                symbol="circle",
                line=dict(color="rgba(255,255,255,0.6)", width=2)
            ),
            text=[f"As = {As:.2f}°C"],
            textposition="top left",
            textfont=dict(size=12, color=MARKER_COLORS["as_marker"], family="JetBrains Mono"),
            hovertemplate="<b>As (奥氏体开始)</b><br>" +
                         "Temperature: %{x:.2f}°C<br>" +
                         "<extra></extra>"
        ))

    # 6. Af-tan intersection point marker - Morandi Apricot
    if not np.isnan(Af_tan):
        af_y = tangent_slope * Af_tan + tangent_intercept
        fig.add_trace(go.Scatter(
            x=[Af_tan],
            y=[af_y],
            mode="markers+text",
            name="Af-tan 点",
            marker=dict(
                size=15,
                color=MARKER_COLORS["af_marker"],
                symbol="circle",
                line=dict(color="rgba(255,255,255,0.6)", width=2)
            ),
            text=[f"Af-tan = {Af_tan:.2f}°C"],
            textposition="top right",
            textfont=dict(size=12, color=MARKER_COLORS["af_marker"], family="JetBrains Mono"),
            hovertemplate="<b>Af-tan (奥氏体完成)</b><br>" +
                         "Temperature: %{x:.2f}°C<br>" +
                         "<extra></extra>"
        ))

    # 7. Max slope point marker - Morandi Rose diamond
    if not np.isnan(max_slope_temp):
        max_slope_y = tangent_slope * max_slope_temp + tangent_intercept
        fig.add_trace(go.Scatter(
            x=[max_slope_temp],
            y=[max_slope_y],
            mode="markers",
            name="最大斜率点",
            marker=dict(
                size=10,
                color=TANGENT_COLORS["middle_tangent"],
                symbol="diamond",
                line=dict(color="rgba(255,255,255,0.6)", width=1)
            ),
            hovertemplate="<b>最大斜率点</b><br>" +
                         "Temperature: %{x:.2f}°C<br>" +
                         "<extra></extra>",
            showlegend=False
        ))

    # Get axis tick parameters
    x_axis_tick, y_axis_tick = get_axis_tick_params()
    x_axis_range, y_axis_range = get_axis_range_params()

    # Get saved zoom state from session_state (if any)
    zoom_state = st.session_state.get("chart_zoom_state", None)

    # Build axis config with optional dtick and range
    # Priority: sidebar settings > saved zoom state > auto
    xaxis_config = dict(
        title=dict(text="Temperature (°C)", font=dict(size=14, color='#8A8A9A')),
        gridcolor='rgba(255,255,255,0.06)',
        showgrid=True,
        zeroline=False,
        tickfont=dict(size=12, color='#8A8A9A'),
    )
    if x_axis_tick > 0:
        xaxis_config['dtick'] = x_axis_tick

    # Apply range: sidebar setting takes priority, then saved zoom state
    if x_axis_range is not None:
        xaxis_config['range'] = list(x_axis_range)
    elif zoom_state and "xaxis.range[0]" in zoom_state:
        xaxis_config['range'] = [zoom_state["xaxis.range[0]"], zoom_state["xaxis.range[1]"]]

    yaxis_config = dict(
        title=dict(text="Displacement", font=dict(size=14, color='#8A8A9A')),
        gridcolor='rgba(255,255,255,0.06)',
        showgrid=True,
        zeroline=False,
        tickfont=dict(size=12, color='#8A8A9A'),
    )
    if y_axis_tick > 0:
        yaxis_config['dtick'] = y_axis_tick

    # Apply range: sidebar setting takes priority, then saved zoom state
    if y_axis_range is not None:
        yaxis_config['range'] = list(y_axis_range)
    elif zoom_state and "yaxis.range[0]" in zoom_state:
        yaxis_config['range'] = [zoom_state["yaxis.range[0]"], zoom_state["yaxis.range[1]"]]

    # Update layout using dark glassmorphism theme
    fig.update_layout(
        title=dict(
            text=f"<b>{channel} 切线分析</b>",
            font=dict(size=18, color='#F0ECE8'),
            x=0.5,
            xanchor="center"
        ),
        xaxis=xaxis_config,
        yaxis=yaxis_config,
        hovermode="closest",
        hoverdistance=50,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.02,
            bgcolor='rgba(255,255,255,0.05)',
            bordercolor='rgba(255,255,255,0.1)',
            font=dict(size=11, color='#C8C0B8')
        ),
        margin=dict(l=60, r=20, t=50, b=60),
        height=550,
        plot_bgcolor='rgba(255,255,255,0.03)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif")
    )

    # Add annotation for results with dark background
    if not np.isnan(As) and not np.isnan(Af_tan):
        fig.add_annotation(
            text=f"<b>分析结果:</b> As = {As:.2f}°C, Af-tan = {Af_tan:.2f}°C",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.02,
            showarrow=False,
            font=dict(size=13, color='#E8E4E0'),
            bgcolor='rgba(26, 26, 46, 0.85)',
            bordercolor='rgba(255,255,255,0.15)',
            borderwidth=1,
            borderpad=5
        )

    return fig


def display_analysis_section(df: pd.DataFrame, channel: str):
    """
    Display the tangent analysis chart section with zoom state persistence.

    Args:
        df: Raw DataFrame with Temperature and channel columns
        channel: Channel name to analyze
    """
    st.subheader("单通道切线分析")

    # Initialize zoom state in session_state if not exists
    if "chart_zoom_state" not in st.session_state:
        st.session_state["chart_zoom_state"] = None

    # Perform analysis (with caching to avoid recomputation)
    cache_key = f"analysis_{channel}_{st.session_state.get('smooth_window', 51)}_{st.session_state.get('smooth_polyorder', 3)}_{st.session_state.get('low_temp_range', (0, 0))}_{st.session_state.get('high_temp_range', (0, 0))}_{st.session_state.get('slope_offset', 0)}"

    if cache_key not in st.session_state or "analysis_result" not in st.session_state:
        with st.spinner("正在分析..."):
            result = perform_analysis(df, channel)
            st.session_state["analysis_result"] = result
    else:
        result = st.session_state["analysis_result"]

    if result is None:
        st.warning("分析失败，请调整参数或检查数据")
        return

    # Generate chart
    fig = render_analysis_chart(result, channel)

    # Display chart - temporarily using st.plotly_chart to debug trace rendering
    # TODO: Switch back to plotly_events once trace rendering issue is resolved
    st.plotly_chart(fig, use_container_width=True)

    # Placeholder for zoom event capture (disabled for debugging)
    chart_events = None

    # Capture zoom/pan events and save to session_state
    if chart_events:
        for event in chart_events:
            if event and "relayout" in str(event):
                # This is a relayout event (zoom, pan, etc.)
                # Extract the range information
                if "xaxis.range[0]" in event or "yaxis.range[0]" in event:
                    st.session_state["chart_zoom_state"] = event

    # Add reset zoom button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("恢复原状", help="重置图表缩放到默认范围"):
            st.session_state["chart_zoom_state"] = None
            st.rerun()

    # Display detailed results
    if "As" in result and "Af_tan" in result:
        col1, col2 = st.columns(2)
        with col1:
            if not np.isnan(result["As"]):
                st.metric("As (奥氏体开始)", f"{result['As']:.1f} °C")
        with col2:
            if not np.isnan(result["Af_tan"]):
                st.metric("Af-tan (奥氏体完成)", f"{result['Af_tan']:.1f} °C")

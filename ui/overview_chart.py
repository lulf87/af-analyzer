"""
Overview chart component for Af Analyzer.

Displays all valid channels' temperature-displacement curves in a single Plotly chart.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Chart colors from design-system/af-analyzer/MASTER.md (Morandi Palette)
CHART_COLORS = {
    "primary": "#8B9DC3",      # Morandi Blue
    "highlight": "#E8E4E0",    # Light white for selected
    "anomaly": "#C4A4A4",      # Morandi Rose
    "secondary_1": "#C4A4A4",  # Morandi Rose (Space2)
    "secondary_2": "#A4B8A4",  # Morandi Green (Space3)
    "secondary_3": "#D4B896",  # Morandi Apricot (Space4)
    "secondary_4": "#B4A4C4",  # Morandi Purple (Space5)
    "secondary_5": "#9CB8C4",  # Morandi Cyan (Space6)
    "grid": "rgba(255,255,255,0.06)",
    "axis_text": "#8A8A9A",
    "text": "#E8E4E0",
}

# Color palette for up to 6 channels (Morandi series)
CHANNEL_COLORS = [
    "#8B9DC3",  # Space1 - Morandi Blue
    "#C4A4A4",  # Space2 - Morandi Rose
    "#A4B8A4",  # Space3 - Morandi Green
    "#D4B896",  # Space4 - Morandi Apricot
    "#B4A4C4",  # Space5 - Morandi Purple
    "#9CB8C4",  # Space6 - Morandi Cyan
]

# Plotly layout configuration for dark glassmorphism theme
PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(255,255,255,0.03)',
    font=dict(
        family='Inter, sans-serif',
        color='#E8E4E0',
        size=13
    ),
    xaxis=dict(
        gridcolor='rgba(255,255,255,0.06)',
        zerolinecolor='rgba(255,255,255,0.1)',
        title_font=dict(size=14, color='#8A8A9A'),
        tickfont=dict(size=12, color='#8A8A9A'),
    ),
    yaxis=dict(
        gridcolor='rgba(255,255,255,0.06)',
        zerolinecolor='rgba(255,255,255,0.1)',
        title_font=dict(size=14, color='#8A8A9A'),
        tickfont=dict(size=12, color='#8A8A9A'),
    ),
    legend=dict(
        bgcolor='rgba(255,255,255,0.05)',
        bordercolor='rgba(255,255,255,0.1)',
        font=dict(color='#C8C0B8', size=12),
    ),
    margin=dict(l=60, r=20, t=50, b=50),
)

# Channel order mapping
CHANNEL_ORDER = ["Space1", "Space2", "Space3", "Space4", "Space5", "Space6"]


def get_channel_color(channel_name: str) -> str:
    """
    Get the color for a specific channel based on design system.

    Args:
        channel_name: Name of the channel (e.g., "Space1")

    Returns:
        Hex color code
    """
    if channel_name in CHANNEL_ORDER:
        idx = CHANNEL_ORDER.index(channel_name)
        return CHANNEL_COLORS[idx % len(CHANNEL_COLORS)]
    return CHART_COLORS["primary"]


def render_overview_chart(df: pd.DataFrame, valid_channels: list[str], selected_channel: str) -> go.Figure:
    """
    Render the overview chart showing all valid channels.

    Features:
    - All channels plotted on the same chart
    - Different colors per channel (from design system)
    - Selected channel highlighted with thicker line
    - Interactive zoom, pan, hover

    Args:
        df: DataFrame with Temperature and Space columns
        valid_channels: List of valid channel names
        selected_channel: Currently selected channel to highlight

    Returns:
        Plotly Figure object
    """
    if df.empty or not valid_channels:
        # Return empty chart with message
        fig = go.Figure()
        fig.add_annotation(
            text="暂无数据 - 请先上传文件",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color=CHART_COLORS["axis_text"])
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            margin=dict(l=0, r=0, t=0, b=0),
            height=400
        )
        return fig

    # Create figure
    fig = go.Figure()

    # Sort channels by standard order
    sorted_channels = sorted(valid_channels, key=lambda x: CHANNEL_ORDER.index(x) if x in CHANNEL_ORDER else 999)

    # Add each channel as a trace
    for channel in sorted_channels:
        if channel not in df.columns:
            continue

        # Get data for this channel (drop NaN values)
        channel_data = df[["Temperature", channel]].dropna()

        if len(channel_data) == 0:
            continue

        is_selected = (channel == selected_channel)

        # Determine line properties
        color = get_channel_color(channel)
        # Selected channel uses brighter white color and thicker line
        if is_selected:
            line_color = CHART_COLORS["highlight"]  # Bright white
            line_width = 4
            opacity = 1.0
        else:
            line_color = color
            line_width = 2
            opacity = 0.7

        # Add trace
        fig.add_trace(go.Scatter(
            x=channel_data["Temperature"],
            y=channel_data[channel],
            mode="lines",
            name=channel,
            line=dict(
                color=line_color,
                width=line_width
            ),
            opacity=opacity,
            hovertemplate=f"<b>{channel}</b><br>" +
                         "Temperature: %{x:.2f}°C<br>" +
                         "Displacement: %{y:.2f}<br>" +
                         "<extra></extra>",
            hoverlabel=dict(
                bgcolor="rgba(26, 26, 46, 0.9)",
                bordercolor=color,
                font=dict(color="#E8E4E0", size=12)
            )
        ))

    # Update layout using PLOTLY_LAYOUT configuration
    layout = PLOTLY_LAYOUT.copy()
    layout.update(
        title=dict(
            text="<b>多通道温度-位移曲线</b>",
            font=dict(size=18, color='#F0ECE8'),
            x=0.5,
            xanchor="center"
        ),
        xaxis=dict(
            title=dict(text="Temperature (°C)", font=dict(size=14, color='#8A8A9A')),
            gridcolor='rgba(255,255,255,0.06)',
            showgrid=True,
            zeroline=False,
            tickfont=dict(size=12, color='#8A8A9A'),
        ),
        yaxis=dict(
            title=dict(text="Displacement", font=dict(size=14, color='#8A8A9A')),
            gridcolor='rgba(255,255,255,0.06)',
            showgrid=True,
            zeroline=False,
            tickfont=dict(size=12, color='#8A8A9A'),
        ),
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
            font=dict(color='#C8C0B8', size=12)
        ),
        margin=dict(l=60, r=20, t=50, b=60),
        height=500,
    )
    fig.update_layout(layout)

    return fig


def display_overview_section(df: pd.DataFrame, valid_channels: list[str], selected_channel: str):
    """
    Display the overview chart section in the main area.

    Args:
        df: DataFrame with Temperature and Space columns
        valid_channels: List of valid channel names
        selected_channel: Currently selected channel
    """
    st.subheader("多通道总览")

    # Generate chart
    fig = render_overview_chart(df, valid_channels, selected_channel)

    # Display chart
    st.plotly_chart(fig, use_container_width=True, key="overview_chart")

    # Show info about selected channel
    if valid_channels and selected_channel:
        st.info(f"""
        **当前选中**: {selected_channel}

        - 普通线条: 未选中的通道 (半透明显示)
        - **加粗线条**: 当前选中的通道 (高亮显示)
        - 悬停查看详细数值
        - 使用鼠标滚轮或拖动进行缩放
        """)

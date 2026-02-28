# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Af Analyzer
**Generated:** 2026-02-27 (Updated)
**Category:** Scientific Analysis Dashboard
**Style:** Dark Glassmorphism + Morandi Palette

---

## Design Philosophy

**关键词：** 高级、沉浸、科技感、有机（Organic）

- 深色背景衬托数据，减少视觉疲劳
- 毛玻璃卡片浮于渐变光影之上，营造层次感和空间感
- 莫兰迪配色（低饱和度灰调彩色）替代刺眼的纯色，既有色彩又不喧宾夺主
- 大圆角消除工业软件的生硬感，增加亲和力
- 图表数据始终保持最高对比度和可读性

---

## Global Rules

### Color Palette — Morandi Dark

| Role | Hex | CSS Variable | 说明 |
|------|-----|--------------|------|
| Background (深层) | `#0F0F1A` | `--color-bg-deep` | 页面最底层深色 |
| Background (表层) | `#1A1A2E` | `--color-bg-surface` | 侧边栏、主区域底色 |
| Glass Card | `rgba(255,255,255,0.07)` | `--color-glass` | 毛玻璃卡片填充色 |
| Glass Border | `rgba(255,255,255,0.12)` | `--color-glass-border` | 毛玻璃卡片边框 |
| Primary (莫兰迪蓝) | `#8B9DC3` | `--color-primary` | 主强调色、选中状态 |
| Secondary (莫兰迪玫) | `#C4A4A4` | `--color-secondary` | 辅助强调、悬停 |
| Accent (莫兰迪绿) | `#A4B8A4` | `--color-accent` | 成功状态、As 标记 |
| Warm (莫兰迪杏) | `#D4B896` | `--color-warm` | 警告、Af 标记 |
| Text Primary | `#E8E4E0` | `--color-text` | 主文字（柔白） |
| Text Muted | `#8A8A9A` | `--color-text-muted` | 次要文字 |
| Text Heading | `#F0ECE8` | `--color-text-heading` | 标题文字 |

### Gradient Backgrounds

```css
/* 页面背景 — 深色 + 彩色径向光晕 */
.stApp {
  background: #0F0F1A;
  background-image:
    radial-gradient(ellipse at 20% 50%, rgba(139, 157, 195, 0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(196, 164, 164, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(164, 184, 164, 0.06) 0%, transparent 50%);
}

/* 侧边栏背景 — 略浅的深色 + 微妙光晕 */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #1A1A2E 0%, #16162A 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}
```

### Typography

- **Heading Font:** Inter (clean, modern)
- **Body Font:** Inter
- **Monospace (数值):** JetBrains Mono
- **Mood:** 科学、精密、高级、现代

**CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
```

### Spacing Variables

| Token | Value | Usage |
|-------|-------|-------|
| `--space-xs` | `4px` | 紧凑间距 |
| `--space-sm` | `8px` | 图标间距 |
| `--space-md` | `16px` | 标准内边距 |
| `--space-lg` | `24px` | 区块内边距 |
| `--space-xl` | `32px` | 大间距 |

### Border Radius — 大圆角

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | `8px` | 小元素（按钮内部） |
| `--radius-md` | `12px` | 输入框、小卡片 |
| `--radius-lg` | `16px` | 标准卡片 |
| `--radius-xl` | `20px` | 大卡片、面板 |
| `--radius-2xl` | `24px` | 特大容器 |

---

## Component Specs

### Glassmorphism Card (核心组件)

```css
.glass-card {
  background: rgba(255, 255, 255, 0.07);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px;
  padding: 24px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  transition: all 300ms ease;
}

.glass-card:hover {
  background: rgba(255, 255, 255, 0.10);
  border-color: rgba(255, 255, 255, 0.18);
  box-shadow:
    0 12px 40px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}
```

### Metric Card (As/Af 温度显示)

```css
.metric-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 20px;
  padding: 20px 24px;
  text-align: center;
}

.metric-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 2.2rem;
  font-weight: 600;
  color: #E8E4E0;
  letter-spacing: -0.02em;
}

.metric-label {
  font-size: 0.85rem;
  color: #8A8A9A;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-top: 4px;
}
```

### Sidebar Controls

```css
/* Expander sections */
[data-testid="stExpander"] {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  margin-bottom: 12px;
}

/* Sliders — Morandi 蓝色轨道 */
[data-testid="stSlider"] .st-emotion-cache-1inwz65 {
  background: #8B9DC3;
}

/* Select box */
[data-testid="stSelectbox"] > div {
  border-radius: 12px;
  border-color: rgba(255, 255, 255, 0.12);
}
```

### Buttons

```css
/* Primary button */
.stButton > button {
  background: linear-gradient(135deg, #8B9DC3 0%, #7B8DB3 100%);
  color: #F0ECE8;
  border: none;
  border-radius: 12px;
  padding: 10px 24px;
  font-weight: 500;
  transition: all 200ms ease;
  box-shadow: 0 4px 12px rgba(139, 157, 195, 0.3);
}

.stButton > button:hover {
  box-shadow: 0 6px 20px rgba(139, 157, 195, 0.4);
  transform: translateY(-1px);
}

/* Download button */
.stDownloadButton > button {
  background: rgba(164, 184, 164, 0.2);
  color: #A4B8A4;
  border: 1px solid rgba(164, 184, 164, 0.3);
  border-radius: 12px;
}
```

---

## Chart Specifications (Plotly)

### Chart Theme — Dark Morandi

```python
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
```

### Chart Color Palette — Morandi Series

| Role | Hex | Usage |
|------|-----|-------|
| 主曲线 | `#8B9DC3` | 平滑后的温度-位移曲线 |
| 低温基准线 | `#A4B8A4` | 绿调虚线 |
| 高温基准线 | `#D4B896` | 杏调虚线 |
| 中间切线 | `#C4A4A4` | 玫调虚线 |
| As 标记点 | `#A4B8A4` | 绿色圆点 + 文本 |
| Af-tan 标记点 | `#D4B896` | 杏色圆点 + 文本 |
| 通道1 | `#8B9DC3` | Space1 |
| 通道2 | `#C4A4A4` | Space2 |
| 通道3 | `#A4B8A4` | Space3 |
| 通道4 | `#D4B896` | Space4 |
| 通道5 | `#B4A4C4` | Space5 (莫兰迪紫) |
| 通道6 | `#9CB8C4` | Space6 (莫兰迪青) |
| 选中通道高亮 | `#E8E4E0` | 加粗 + 亮白 |

### Annotation Style

```python
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
```

---

## Streamlit Custom CSS (注入到 app.py)

以下 CSS 通过 `st.markdown(css, unsafe_allow_html=True)` 注入：

```css
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
```

---

## Anti-Patterns (Do NOT Use)

- ❌ **纯白背景** — 与深色玻璃风格冲突
- ❌ **高饱和度纯色** — 使用莫兰迪色（带灰调的低饱和色）
- ❌ **方角/小圆角** — 统一使用 12px 以上的大圆角
- ❌ **粗重边框** — 使用半透明细边框（1px, rgba）
- ❌ **不透明卡片** — 卡片必须有透明度 + backdrop-filter
- ❌ **Emojis 作为图标** — 不使用 emoji
- ❌ **过度动画** — Streamlit 不支持复杂动效，不要尝试 hack

---

## Pre-Delivery Checklist

- [ ] 深色背景 + 渐变光晕正确渲染
- [ ] 毛玻璃卡片有可见的模糊效果和半透明边框
- [ ] 所有文字在深色背景上清晰可读（对比度 ≥ 4.5:1）
- [ ] 图表背景透明，融入整体深色风格
- [ ] Metric 数值使用等宽字体（JetBrains Mono）
- [ ] 所有圆角 ≥ 12px
- [ ] 配色使用莫兰迪色系（无高饱和纯色）
- [ ] Plotly 图表使用 PLOTLY_LAYOUT 配置
- [ ] 侧边栏控件在深色背景上可见可操作

# Visual Report HTML Templates

在开始写具体 HTML 组件前，先看：

- `references/layout-rules.md`
- `references/ppt-styles.md`（仅 PPT 模式）
- `references/pdf-export.md`（仅 PDF 模式）
- `references/visual-patterns.md`（逻辑图 / 导图 / 路线图 / 决策树等）

先决定页面骨架和模块配对，再选择本文件里的组件。
不要跳过布局判断，直接把表格、流程卡、图表硬拼到双栏里。

## 设计风格：Dark Glass Morphism

参考 Gemini Canvas / Napkin 风格，采用深色背景 + 玻璃拟态 + 丰富图表。

## 使用顺序

1. 先判断内容类型：数据复盘 / 叙事复盘 / 对比决策 / 卡片展示
2. 再根据 `layout-rules.md` 选择页面骨架
3. 最后从本文件挑选适合的组件

如果版式不平衡：
- 优先改骨架
- 不要靠增加空白、拉大容器或强行双栏解决

如果内容核心是“关系”而不是“数字”：
- 优先参考 `references/visual-patterns.md`
- 不要只用普通卡片硬讲逻辑

## 基础报告结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
/* 打印时保留颜色 */
@media print {
  @page { size: A4; margin: 12mm; }
  * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; color-adjust: exact !important; }
  html, body { margin: 0 !important; padding: 0 !important; overflow: visible !important; min-height: auto !important; }
  body { background: #0f172a !important; -webkit-print-color-adjust: exact; }
  .no-print { display: none !important; }
  .avoid-break, .glass, table, img, canvas, svg, section { break-inside: avoid !important; page-break-inside: avoid !important; }
  .print-stack { display: block !important; }
  .grid, .flex, .print-stack { display: block !important; }
  .grid > *, .flex > *, .print-stack > * { width: 100% !important; max-width: none !important; margin-bottom: 10mm !important; }
  .glass { backdrop-filter: none !important; box-shadow: none !important; background: rgba(15,23,42,0.85) !important; }
  [class*="bg-clip-text"], [class*="text-transparent"] { background: none !important; -webkit-text-fill-color: #ffffff !important; color: #ffffff !important; }
  .slide, .ppt-slide { display: block !important; visibility: visible !important; }
  .pdf-page-break { break-before: page; page-break-before: always; }
}
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }
.glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
.vr-page { max-width: 1120px; margin: 0 auto; padding: 32px 24px; }
.vr-section { margin-bottom: 32px; }
.vr-grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; }
.vr-grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }
.vr-grid-4 { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px; }
.vr-card { border-radius: 24px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); padding: 24px; }
.vr-title { font-size: 34px; font-weight: 800; line-height: 1.15; }
.vr-muted { color: #cbd5e1; line-height: 1.7; }
</style>
</head>
<body class="text-white p-8">
<div class="max-w-5xl mx-auto">
  <!-- 内容 -->
</div>
<script>
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255,255,255,0.1)';
// 图表代码
</script>
</body>
</html>
```

如果用户明确要 PDF：
- 不要只依赖这个基础 `@media print`
- 额外参考 `references/pdf-export.md`
- 优先给关键模块加 `.avoid-break`
- 对多列布局容器加 `.print-stack`
- 在需要强制换页的 section 前加 `.pdf-page-break`
- 对关键结构优先补一层语义类：`.vr-page`、`.vr-grid-2`、`.vr-grid-4`、`.vr-card`
- 不要把可读性完全押注在 Tailwind utility 上

为了让 `Cmd/Ctrl + P` 更稳定，建议在页面底部补充：

```html
<script>
(() => {
  const enterPrint = () => document.documentElement.classList.add('print-mode');
  const exitPrint = () => document.documentElement.classList.remove('print-mode');
  window.addEventListener('beforeprint', enterPrint);
  window.addEventListener('afterprint', exitPrint);
  if (window.matchMedia) {
    const media = window.matchMedia('print');
    const handler = event => event.matches ? enterPrint() : exitPrint();
    if (media.addEventListener) media.addEventListener('change', handler);
    else if (media.addListener) media.addListener(handler);
  }
})();
</script>
```

## 核心组件

### 1. Header 标题区

```html
<header class="text-center mb-12">
  <div class="inline-flex items-center gap-2 bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-sm px-4 py-2 rounded-full mb-4">
    <span class="w-2 h-2 bg-indigo-400 rounded-full animate-pulse"></span>
    {{副标题/日期}}
  </div>
  <h1 class="text-4xl font-bold bg-gradient-to-r from-white via-indigo-200 to-purple-200 bg-clip-text text-transparent">{{主标题}}</h1>
</header>
```

### 2. 渐变指标卡片

```html
<div class="grid grid-cols-3 gap-4">
  <!-- 粉红渐变 -->
  <div class="bg-gradient-to-br from-pink-500 to-rose-600 rounded-2xl p-6 relative overflow-hidden">
    <div class="absolute top-0 right-0 w-24 h-24 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2"></div>
    <div class="relative">
      <div class="text-pink-100 text-sm">{{标签}}</div>
      <div class="text-4xl font-bold mt-1">{{数值}}</div>
      <div class="inline-flex items-center bg-white/20 px-2 py-1 rounded-full text-sm mt-2">+{{增长}}%</div>
    </div>
  </div>
  <!-- 橙色渐变 -->
  <div class="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-6">...</div>
  <!-- 青色渐变 -->
  <div class="bg-gradient-to-br from-teal-500 to-cyan-600 rounded-2xl p-6">...</div>
</div>
```

### 3. 玻璃表格

```html
<div class="glass rounded-2xl overflow-hidden">
  <table class="w-full">
    <thead class="bg-gradient-to-r from-indigo-600 to-purple-600">
      <tr><th class="px-5 py-4 text-left">列1</th><th class="px-5 py-4 text-right">列2</th></tr>
    </thead>
    <tbody class="divide-y divide-white/10">
      <tr class="hover:bg-white/5"><td class="px-5 py-3">数据</td><td class="px-5 py-3 text-right text-emerald-400">数据</td></tr>
    </tbody>
  </table>
</div>
```

### 4. 章节标题

```html
<h2 class="text-xl font-bold mb-6 flex items-center">
  <span class="w-1 h-6 bg-gradient-to-b from-indigo-500 to-purple-500 rounded mr-3"></span>
  {{章节名}}
</h2>
```

### 5. 玻璃信息卡片

```html
<div class="glass rounded-2xl p-5">
  <h3 class="font-bold text-lg">{{标题}}</h3>
  <p class="text-slate-400 text-sm mt-2">{{内容}}</p>
</div>
```

### 6. 带图标的列表项

```html
<div class="flex items-start gap-4 p-4 bg-white/5 rounded-xl">
  <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">🎯</div>
  <div>
    <div class="font-bold">{{标题}}</div>
    <div class="text-sm text-slate-400">{{描述}}</div>
    <div class="flex gap-2 mt-2">
      <span class="text-purple-300 font-semibold">{{数值}}</span>
      <span class="bg-purple-500/30 text-purple-200 px-2 py-0.5 rounded text-xs">{{标签}}</span>
    </div>
  </div>
</div>
```

## 结构图 / 逻辑图入口

如果要表达流程、树状关系、导图、路线图、SWOT、四象限，不要只靠基础卡片拼。

请改读：
- `references/visual-patterns.md`

## 图表组件（Chart.js）

### 柱状图 - 适合对比数据

```html
<div class="glass rounded-2xl p-5">
  <h3 class="text-base font-semibold mb-3 text-slate-300">{{标题}}</h3>
  <div class="h-48"><canvas id="barChart"></canvas></div>
</div>
<script>
new Chart(document.getElementById('barChart'), {
  type: 'bar',
  data: {
    labels: ['A', 'B', 'C'],
    datasets: [{ data: [100, 200, 150], backgroundColor: ['rgba(99,102,241,0.8)', 'rgba(168,85,247,0.8)', 'rgba(236,72,153,0.8)'], borderRadius: 6 }]
  },
  options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
});
</script>
```

### 横向条形图 - 适合排名/增长率

```html
new Chart(ctx, {
  type: 'bar',
  data: { labels: [...], datasets: [{ data: [...], borderRadius: 6 }] },
  options: { indexAxis: 'y', ... }
});
```

### 环形图 - 适合占比

```html
new Chart(ctx, {
  type: 'doughnut',
  data: {
    labels: ['A', 'B'],
    datasets: [{ data: [70, 30], backgroundColor: ['rgba(6,182,212,0.9)', 'rgba(100,116,139,0.6)'], borderWidth: 0 }]
  },
  options: { cutout: '70%', plugins: { legend: { position: 'bottom' } } }
});
```

### 折线图 - 适合趋势

```html
new Chart(ctx, {
  type: 'line',
  data: {
    labels: ['1月', '2月', '3月'],
    datasets: [{ data: [10, 25, 40], borderColor: 'rgba(99,102,241,1)', backgroundColor: 'rgba(99,102,241,0.1)', fill: true, tension: 0.4 }]
  }
});
```

### SVG 进度环 - 适合单一占比指标

```html
<div class="relative w-28 h-28">
  <svg class="w-28 h-28 -rotate-90" viewBox="0 0 120 120">
    <circle cx="60" cy="60" r="50" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="10"/>
    <circle cx="60" cy="60" r="50" fill="none" stroke="url(#g1)" stroke-width="10" stroke-linecap="round" stroke-dasharray="314" stroke-dashoffset="{{314 - 314*百分比}}"/>
    <defs><linearGradient id="g1"><stop offset="0%" stop-color="#10b981"/><stop offset="100%" stop-color="#06b6d4"/></linearGradient></defs>
  </svg>
  <div class="absolute inset-0 flex flex-col items-center justify-center">
    <span class="text-2xl font-bold">{{百分比}}%</span>
  </div>
</div>
```

## 图表选择指南

| 数据类型 | 推荐图表 |
|---------|---------|
| 多项对比（3-6项） | 柱状图 |
| 增长率/排名 | 横向条形图 |
| 占比（2-3项） | 环形图 |
| 单一占比指标 | SVG进度环 |
| 时间趋势 | 折线图 |
| 分布/相关性 | 散点图 |

## 配色方案

```
渐变卡片：
- 粉红: from-pink-500 to-rose-600
- 橙色: from-amber-500 to-orange-600
- 青色: from-teal-500 to-cyan-600
- 紫色: from-indigo-500 to-purple-600

图表颜色：
- rgba(99,102,241,0.8)  // 靛蓝
- rgba(168,85,247,0.8)  // 紫色
- rgba(236,72,153,0.8)  // 粉红
- rgba(6,182,212,0.9)   // 青色
- rgba(251,146,60,0.8)  // 橙色
- rgba(16,185,129,0.8)  // 绿色
```

---

## PPT 模式（交互式幻灯片）

当用户要求生成 PPT 时，使用以下模板：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
@media print { * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; } }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  margin: 0;
  background:
    radial-gradient(circle at top left, rgba(56,189,248,.18), transparent 28%),
    radial-gradient(circle at top right, rgba(168,85,247,.18), transparent 24%),
    linear-gradient(135deg, #0f172a 0%, #111827 55%, #1e293b 100%);
}
.slide {
  width: 100vw;
  height: 100vh;
  display: none;
  padding: 56px 64px;
  box-sizing: border-box;
  position: relative;
  overflow: hidden;
}
.slide.active { display: block; }
.slide::before {
  content: "";
  position: absolute;
  inset: 24px;
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 28px;
  pointer-events: none;
}
.slide::after {
  content: "";
  position: absolute;
  top: 32px;
  left: 32px;
  width: 6px;
  height: 96px;
  border-radius: 999px;
  background: linear-gradient(180deg, #22d3ee 0%, #a855f7 100%);
}
.glass { background: rgba(255,255,255,.05); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,.08); }
.ppt-kicker { letter-spacing: .24em; text-transform: uppercase; font-size: 12px; color: #67e8f9; margin-bottom: 16px; }
.ppt-subtitle, .ppt-summary { color: #cbd5e1; line-height: 1.7; }
.ppt-metric-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 18px; margin-top: 32px; }
.ppt-metric-card { border-radius: 24px; padding: 24px; color: white; box-shadow: 0 20px 40px rgba(15,23,42,.25); }
.ppt-metric-card[data-accent="cyan"] { background: linear-gradient(135deg, #0891b2 0%, #2563eb 100%); }
.ppt-metric-card[data-accent="violet"] { background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%); }
.ppt-metric-card[data-accent="amber"] { background: linear-gradient(135deg, #f97316 0%, #f43f5e 100%); }
.ppt-metric-card[data-accent="emerald"] { background: linear-gradient(135deg, #059669 0%, #14b8a6 100%); }
.ppt-metric-label { font-size: 14px; color: rgba(255,255,255,.82); }
.ppt-metric-value { font-size: 40px; font-weight: 800; margin-top: 16px; }
.ppt-metric-note { font-size: 14px; color: rgba(255,255,255,.88); margin-top: 12px; line-height: 1.6; }
.ppt-two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 28px; }
.ppt-panel { border-radius: 24px; padding: 28px; background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.08); }
.ppt-panel h3 { font-size: 28px; margin: 0 0 16px; }
.ppt-panel p, .ppt-panel li { font-size: 22px; color: #e2e8f0; line-height: 1.7; }
.ppt-bullets { margin: 0; padding-left: 22px; }
.ppt-section-title { font-size: 64px; font-weight: 800; margin-top: 120px; }
.ppt-closing-points { margin-top: 28px; display: grid; gap: 12px; font-size: 22px; color: #e2e8f0; }
.slide-nav { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); display: flex; gap: 8px; z-index: 100; }
.slide-dot { width: 12px; height: 12px; border-radius: 50%; background: rgba(255,255,255,0.3); cursor: pointer; transition: all 0.3s; }
.slide-dot.active { background: #6366f1; transform: scale(1.2); }
.slide-counter { position: fixed; bottom: 30px; right: 40px; color: rgba(255,255,255,0.5); font-size: 14px; }
@media print {
  @page { size: 13.333in 7.5in; margin: 0; }
  html, body { margin: 0 !important; padding: 0 !important; overflow: visible !important; }
  .slide, .ppt-slide { display: block !important; width: 13.333in !important; height: 7.5in !important; break-after: page !important; page-break-after: always !important; }
  .slide:last-of-type, .ppt-slide:last-of-type { break-after: auto !important; page-break-after: auto !important; }
  .slide-nav, .slide-counter, .no-print { display: none !important; }
}
</style>
</head>
<body class="text-white" data-ppt-theme="summit-dark">

<section class="slide ppt-slide active" data-slide="1" data-slide-type="cover" data-accent="cyan">
  <div class="ppt-kicker">{{场景 / 日期 / 场合}}</div>
  <h1 class="text-6xl font-black leading-tight max-w-5xl">{{标题}}</h1>
  <p class="ppt-subtitle text-2xl mt-6 max-w-3xl">{{副标题}}</p>
  <div class="glass rounded-[28px] p-6 mt-10 max-w-xl">
    <div class="text-sm text-slate-300">开场提示</div>
    <div class="mt-3 text-lg leading-8 text-slate-100">{{1-2 句开场摘要}}</div>
  </div>
</section>

<section class="slide ppt-slide" data-slide="2" data-slide-type="section" data-accent="violet">
  <div class="ppt-kicker">Section 01</div>
  <div class="ppt-section-title">{{章节标题}}</div>
  <p class="ppt-subtitle text-2xl mt-6 max-w-3xl">{{这一章要回答的问题}}</p>
</section>

<section class="slide ppt-slide" data-slide="3" data-slide-type="metrics" data-accent="amber">
  <div class="ppt-kicker">Key Metrics</div>
  <h2 class="text-4xl font-bold">{{指标页标题}}</h2>
  <p class="ppt-summary text-xl mt-4 max-w-4xl">{{一句总结}}</p>
  <div class="ppt-metric-grid">
    <div class="ppt-metric-card" data-accent="cyan">
      <div class="ppt-metric-label">{{指标标签}}</div>
      <div class="ppt-metric-value">{{指标数值}}</div>
      <div class="ppt-metric-note">{{指标说明}}</div>
    </div>
    <div class="ppt-metric-card" data-accent="violet">...</div>
    <div class="ppt-metric-card" data-accent="amber">...</div>
    <div class="ppt-metric-card" data-accent="emerald">...</div>
  </div>
</section>

<section class="slide ppt-slide" data-slide="4" data-slide-type="two-column" data-accent="cyan">
  <div class="ppt-kicker">Argument</div>
  <h2 class="text-4xl font-bold">{{双栏页标题}}</h2>
  <div class="ppt-two-col">
    <div class="ppt-panel">
      <h3>{{左侧标题}}</h3>
      <ul class="ppt-bullets">
        <li>{{要点 1}}</li>
        <li>{{要点 2}}</li>
        <li>{{要点 3}}</li>
      </ul>
    </div>
    <div class="ppt-panel">
      <h3>{{右侧标题}}</h3>
      <p>{{右侧说明}}</p>
    </div>
  </div>
</section>

<section class="slide ppt-slide" data-slide="5" data-slide-type="table" data-accent="violet">
  <div class="ppt-kicker">Data Table</div>
  <h2 class="text-4xl font-bold">{{表格页标题}}</h2>
  <p class="ppt-summary text-xl mt-4">{{一句解释}}</p>
  <div class="glass rounded-[28px] overflow-hidden mt-8">
    <table class="w-full text-left">
      <thead class="bg-white/10">
        <tr><th class="px-5 py-4">列 1</th><th class="px-5 py-4">列 2</th><th class="px-5 py-4">列 3</th></tr>
      </thead>
      <tbody class="divide-y divide-white/10">
        <tr><td class="px-5 py-4">{{数据}}</td><td class="px-5 py-4">{{数据}}</td><td class="px-5 py-4">{{数据}}</td></tr>
      </tbody>
    </table>
  </div>
</section>

<section class="slide ppt-slide" data-slide="6" data-slide-type="closing" data-accent="amber">
  <div class="ppt-kicker">Closing</div>
  <h2 class="text-5xl font-black leading-tight max-w-4xl">{{结尾标题}}</h2>
  <div class="ppt-closing-points">
    <div>{{结论 1}}</div>
    <div>{{结论 2}}</div>
    <div>{{结论 3}}</div>
  </div>
</section>

<div class="slide-nav" id="slideNav"></div>
<div class="slide-counter"><span id="currentSlide">1</span> / <span id="totalSlides">1</span></div>

<script>
const slides = document.querySelectorAll('.slide');
const nav = document.getElementById('slideNav');
const currentEl = document.getElementById('currentSlide');
const totalEl = document.getElementById('totalSlides');
let current = 0;

totalEl.textContent = slides.length;
slides.forEach((_, i) => {
  const dot = document.createElement('div');
  dot.className = 'slide-dot' + (i === 0 ? ' active' : '');
  dot.onclick = () => goTo(i);
  nav.appendChild(dot);
});

function goTo(n) {
  slides[current].classList.remove('active');
  nav.children[current].classList.remove('active');
  current = (n + slides.length) % slides.length;
  slides[current].classList.add('active');
  nav.children[current].classList.add('active');
  currentEl.textContent = current + 1;
}

document.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight' || e.key === ' ') goTo(current + 1);
  if (e.key === 'ArrowLeft') goTo(current - 1);
});
document.addEventListener('click', e => {
  if (!e.target.closest('.slide-nav')) goTo(current + 1);
});
</script>
</body>
</html>
```

**PPT 交互功能**：
- 左右箭头键切换幻灯片
- 空格键下一页
- 点击页面任意位置下一页
- 底部导航点可跳转任意页
- 显示当前页码/总页数

**PPT 模式要求**：
- 优先参考 `references/ppt-styles.md` 先选主题，再写具体 slide
- 使用语义类名：`.ppt-slide`、`.ppt-panel`、`.ppt-metric-card`
- 给每一页设置 `data-slide-type` 和 `data-accent`
- 不要整套 PPT 只用一种页面

**如果同时要 PDF**：
- 保留上面的 `@media print`
- 优先调用 `scripts/export_pdf.py`
- 不要让 slide 在打印时继续 `display: none`

---

## 表格模式（交互式数据表格）

当用户要求生成表格时，使用以下模板：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
@media print { * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; } }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); min-height: 100vh; }
.glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
.sortable { cursor: pointer; user-select: none; }
.sortable:hover { background: rgba(255,255,255,0.1); }
.sortable::after { content: '↕'; margin-left: 8px; opacity: 0.5; }
.sortable.asc::after { content: '↑'; opacity: 1; }
.sortable.desc::after { content: '↓'; opacity: 1; }
tr.highlight { background: rgba(99,102,241,0.2) !important; }
</style>
</head>
<body class="text-white p-8">
<div class="max-w-6xl mx-auto">
  <header class="mb-8">
    <h1 class="text-3xl font-bold">{{标题}}</h1>
    <div class="flex gap-4 mt-4">
      <input type="text" id="searchInput" placeholder="搜索..." class="bg-white/10 border border-white/20 rounded-lg px-4 py-2 text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500">
      <button onclick="exportCSV()" class="bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-lg transition">导出 CSV</button>
    </div>
  </header>

  <div class="glass rounded-2xl overflow-hidden">
    <table class="w-full" id="dataTable">
      <thead class="bg-gradient-to-r from-indigo-600 to-purple-600">
        <tr>
          <th class="px-5 py-4 text-left sortable" data-col="0">列1</th>
          <th class="px-5 py-4 text-right sortable" data-col="1">列2</th>
          <th class="px-5 py-4 text-right sortable" data-col="2">列3</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-white/10" id="tableBody">
        <tr class="hover:bg-white/5 transition"><td class="px-5 py-3">数据1</td><td class="px-5 py-3 text-right">100</td><td class="px-5 py-3 text-right text-emerald-400">+10%</td></tr>
        <!-- 更多行... -->
      </tbody>
    </table>
  </div>

  <div class="mt-4 text-slate-400 text-sm">共 <span id="rowCount">0</span> 条记录</div>
</div>

<script>
const table = document.getElementById('dataTable');
const tbody = document.getElementById('tableBody');
const searchInput = document.getElementById('searchInput');
const rowCountEl = document.getElementById('rowCount');
let originalRows = [...tbody.querySelectorAll('tr')];

// 搜索过滤
searchInput.addEventListener('input', e => {
  const term = e.target.value.toLowerCase();
  originalRows.forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(term) ? '' : 'none';
  });
  updateCount();
});

// 排序
document.querySelectorAll('.sortable').forEach(th => {
  th.addEventListener('click', () => {
    const col = parseInt(th.dataset.col);
    const asc = !th.classList.contains('asc');
    document.querySelectorAll('.sortable').forEach(t => t.classList.remove('asc', 'desc'));
    th.classList.add(asc ? 'asc' : 'desc');

    const rows = [...tbody.querySelectorAll('tr')];
    rows.sort((a, b) => {
      const aVal = a.cells[col].textContent;
      const bVal = b.cells[col].textContent;
      const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
      const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
      if (!isNaN(aNum) && !isNaN(bNum)) return asc ? aNum - bNum : bNum - aNum;
      return asc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
    });
    rows.forEach(row => tbody.appendChild(row));
  });
});

// 行点击高亮
tbody.addEventListener('click', e => {
  const row = e.target.closest('tr');
  if (row) row.classList.toggle('highlight');
});

// 导出 CSV
function exportCSV() {
  const rows = [...table.querySelectorAll('tr')];
  const csv = rows.map(row => [...row.cells].map(cell => '"' + cell.textContent + '"').join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'data.csv';
  a.click();
}

function updateCount() {
  rowCountEl.textContent = [...tbody.querySelectorAll('tr')].filter(r => r.style.display !== 'none').length;
}
updateCount();
</script>
</body>
</html>
```

**表格交互功能**：
- 搜索过滤
- 点击表头排序（支持数字和文本）
- 点击行高亮
- 导出 CSV
- 显示记录数

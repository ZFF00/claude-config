# PDF Export Rules

仅在 **PDF 模式** 下读取本文件。

目标是让导出的 PDF 成为一个稳定、可读、分页合理的成品，而不是“把网页硬打印出来”。

## 1. 先判断 PDF 类型

### A. 报告型 PDF

适合：
- 会议纪要
- 数据复盘
- 策略报告
- 可滚动网页报告

目标：
- A4 纵向为主
- 打印时自动重排为单栏或更稳定布局
- 避免双栏碎裂、表格断页、图表挤压

### B. 幻灯片型 PDF

适合：
- 演示稿
- keynotes
- 逐页汇报 deck

目标：
- 16:9 横向
- 一张 slide 对应一页 PDF
- 打印时隐藏交互控件

## 2. 打印重排原则

### 报告型 PDF

打印时优先做这些事：
- 把复杂 grid / 双栏 / 卡片矩阵重排成更稳定的单栏
- 保持卡片、图表、表格完整，不要在中间被切断
- 缩短横向布局，避免 A4 上出现过宽的内容
- 对长表格保持表头重复

### 幻灯片型 PDF

打印时优先做这些事：
- 让所有 `.slide` / `.ppt-slide` 变为 `display: block`
- 强制每页换页
- 保持固定宽高比
- 隐藏导航点、页码控件、悬浮按钮

## 3. 推荐辅助类

生成 HTML 时，优先给关键模块加这些类：

- `.avoid-break`
  - 作用：卡片、图表、表格、图片避免被分页切开

- `.print-stack`
  - 作用：打印时把双栏、多列改成纵向堆叠

- `.pdf-page-break`
  - 作用：在重要章节前强制换页

- `.vr-page` / `.vr-grid-2` / `.vr-grid-4` / `.vr-card`
  - 作用：为关键结构提供不依赖 Tailwind utility 的打印安全兜底

## 4. 报告型 PDF 推荐打印 CSS

```css
@media print {
  @page { size: A4; margin: 12mm; }
  html, body {
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
    min-height: auto !important;
  }
  .no-print, .slide-nav, .slide-counter {
    display: none !important;
  }
  .avoid-break, .glass, .ppt-panel, .ppt-metric-card, table, img, canvas, svg, section {
    break-inside: avoid !important;
    page-break-inside: avoid !important;
  }
  .print-stack,
  .grid,
  .ppt-two-col,
  .ppt-metric-grid,
  [class*="grid-cols-"],
  [class*="lg:grid-cols"],
  [class*="md:grid-cols"] {
    display: block !important;
  }
  .print-stack > *,
  .grid > *,
  .ppt-two-col > *,
  .ppt-metric-grid > * {
    width: 100% !important;
    margin-bottom: 10mm !important;
  }
  .pdf-page-break {
    break-before: page;
    page-break-before: always;
  }
  thead {
    display: table-header-group !important;
  }
}
```

## 5. 幻灯片型 PDF 推荐打印 CSS

```css
@media print {
  @page { size: 13.333in 7.5in; margin: 0; }
  html, body {
    margin: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }
  .slide, .ppt-slide {
    display: block !important;
    width: 13.333in !important;
    height: 7.5in !important;
    break-after: page !important;
    page-break-after: always !important;
    overflow: hidden !important;
  }
  .slide:last-of-type, .ppt-slide:last-of-type {
    break-after: auto !important;
    page-break-after: auto !important;
  }
  .slide-nav, .slide-counter, .no-print {
    display: none !important;
  }
}
```

## 6. 什么时候必须重排

遇到以下情况，不要直接打印原网页：

- 左右双栏高度明显失衡
- 页面中有 3 列以上卡片矩阵
- 表格列太多，A4 纵向无法正常阅读
- 图表和文字被塞在同一行，打印后会互相挤压
- slide 模式下，非 active 的 slide 仍然是 `display: none`

## 7. 兼容 `Cmd/Ctrl + P`

如果用户直接在浏览器里 `Cmd/Ctrl + P`：

- 页面本身也必须具备 print-safe CSS
- 不能把稳定导出只寄托在 `scripts/export_pdf.py`
- 需要兼容以下常见问题：
  - `display: none` 的 slide 在打印预览里仍然隐藏
  - 渐变文字使用 `text-transparent + bg-clip-text`，打印时变成不可见
  - `backdrop-filter` 在打印时异常，造成卡片内容发虚或丢失
  - 多列 grid 在 A4 上直接碎裂

推荐补一段兼容脚本：

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

## 8. 默认导出方式

当用户明确要 PDF：

1. 先生成 HTML
2. 再运行 `scripts/export_pdf.py`
3. 不要把“请按 Cmd + P”当作默认答案

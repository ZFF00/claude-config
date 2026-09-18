# PPT Style System

仅在 **PPT 模式** 下读取本文件。

目标不是把网页“顺便导出”成 PPT，而是先按幻灯片思维组织内容，再生成 HTML，最后让导出器把视觉层级映射到 `.pptx`。

## 1. 先选主题家族

### `summit-dark`

适合：
- 金融、董事会、战略、年度总结
- 需要稳重、权威、偏高层汇报的内容

视觉关键词：
- 深海军蓝背景
- 青色 / 琥珀色强调色
- 大标题、强对比、较少装饰

### `signal-grid`

适合：
- AI、硬科技、产品路线、数据洞察
- 需要更科技、更数据感的内容

视觉关键词：
- 石墨黑背景
- 蓝紫色电感强调
- 网格、线条、信息密度略高

### `editorial-stage`

适合：
- 演讲稿、观点输出、复盘分享、思考型内容
- 希望更像 keynote，而不是 dashboard

视觉关键词：
- 墨色背景
- 大留白、大字号、强标题
- 标题像杂志封面，正文更克制

### `ember-premium`

适合：
- 高端路演、商业叙事、品牌战略
- 需要更有“质感”和“温度”的场景

视觉关键词：
- 深炭黑背景
- 橙金 / 红铜强调
- 暖色高光、较强舞台感

## 2. 幻灯片节奏

PPT 不要整份都用一种页面。

推荐基本节奏：

```text
封面页
↓
章节过渡页
↓
关键指标页 / 关键结论页
↓
论点展开页（双栏 / 卡片 / 表格）
↓
章节过渡页
↓
下一章节内容
↓
结尾页
```

### 最少应包含

- 1 张封面页
- 1 张结尾页
- 重要章节之间至少有 1 张节奏明显不同的页

### 不要这样做

- 连续 4 页都是标题 + 大段正文
- 连续 3 页都是完全相同的双栏
- 一页里同时放表格、流程、6 个卡片和长段落

## 3. 单页信息密度

### 强制约束

- 每页只讲 **一个主结论**
- 标题尽量控制在 8-16 个字
- 正文单段最好控制在 40-90 个中文字符
- 列表页建议 3-5 个要点
- 指标页建议 3-4 张卡片
- 表格页一页 1 张表，最好不超过 6 行

### 拆页判断

出现以下任一情况时，必须拆页：
- 标题之外还有 2 段长文 + 1 张表
- 同时有 6 个以上 bullet
- 同时想讲“事实、原因、建议”三个层次
- 双栏内容高度明显不平衡

## 4. 幻灯片类型

### `cover`

用途：
- 开场页

内容：
- 大标题
- 副标题 / 场景说明
- 可选元信息卡

### `section`

用途：
- 章节过渡

内容：
- 章节标题
- 一句本章要回答的问题

### `metrics`

用途：
- 关键数字
- 市场温度
- 核心摘要

内容：
- 1 个标题
- 3-4 张指标卡
- 可选一段结论

### `two-column`

用途：
- 左右对照
- 两类观点
- 主结论 + 支撑说明

内容：
- 左右各 1-2 个 `.ppt-panel`

### `bullets`

用途：
- 观点拆解
- 建议
- 行动项

内容：
- 1 个标题
- 3-5 条要点
- 可选结论卡

### `table`

用途：
- 关键数据表
- 对比矩阵

内容：
- 一张表
- 可选一句解释

### `closing`

用途：
- 收束结论
- ending

内容：
- 收束标题
- 2-3 句 closing points

## 5. 语义 HTML 约定

PPT 模式下，优先使用以下语义结构：

```html
<body data-ppt-theme="summit-dark">
  <section class="slide ppt-slide" data-slide-type="cover" data-accent="cyan">
    <div class="ppt-kicker">Keynote</div>
    <h1>主标题</h1>
    <p class="ppt-subtitle">副标题</p>
  </section>

  <section class="slide ppt-slide" data-slide-type="metrics" data-accent="violet">
    <h2>关键指标</h2>
    <p class="ppt-summary">一句解释</p>
    <div class="ppt-metric-grid">
      <div class="ppt-metric-card" data-accent="cyan">
        <div class="ppt-metric-label">标签</div>
        <div class="ppt-metric-value">4400 亿美元</div>
        <div class="ppt-metric-note">补充说明</div>
      </div>
    </div>
  </section>

  <section class="slide ppt-slide" data-slide-type="two-column" data-accent="amber">
    <h2>章节标题</h2>
    <div class="ppt-two-col">
      <div class="ppt-panel">
        <h3>左侧标题</h3>
        <ul class="ppt-bullets"><li>要点</li></ul>
      </div>
      <div class="ppt-panel">
        <h3>右侧标题</h3>
        <p>说明</p>
      </div>
    </div>
  </section>
</body>
```

优先使用的类名：
- `.ppt-kicker`
- `.ppt-subtitle`
- `.ppt-summary`
- `.ppt-metric-card`
- `.ppt-metric-label`
- `.ppt-metric-value`
- `.ppt-metric-note`
- `.ppt-panel`
- `.ppt-bullets`

## 6. 美观规则

### 标题层级

- 封面标题要足够大
- 页面标题要短、狠、可被一眼扫到
- 不要把长句直接塞进标题

### 视觉锚点

每页至少有一个视觉锚点：
- 一组大数字
- 一块强强调色卡片
- 一个高对比标题区
- 一张表格或一组卡片

### 页面变化

控制重复：
- 同一种 slide type 不要连续出现超过 2 页
- 如果上一页是双栏，这一页优先切到指标页、表格页或章节页

### 风格一致

整套 deck 内：
- 主题家族保持一致
- 强调色控制在 2-3 个以内
- 卡片圆角、边框、阴影强度要统一

## 7. 生成前快速检查

在真正写 PPT HTML 前，先检查：

- 这套内容更适合哪一个主题家族？
- 哪几页必须做成“章节页”来打断节奏？
- 哪些长段落应该拆成 2 页？
- 有没有某一页同时承载了过多信息？
- 哪一页的视觉锚点最弱，需要补一个强卡片或大数字？

# Visual Patterns Library

当普通卡片、表格、图表不足以表达信息结构时，读取本文件。

目标：让 skill 不只会做“卡片 + 图表 + 表格”，还会做结构化视觉表达。

## 1. 当前适用场景

优先使用本文件的情况：
- 需要表达因果关系
- 需要表达流程顺序
- 需要表达树状逻辑
- 需要表达多象限决策
- 需要表达路线图、阶段目标、里程碑
- 需要表达组织关系、职责关系、协作关系

## 2. 内置结构样式清单

### A. 时间线 / 里程碑

适合：
- 项目进展
- 战略阶段
- 发展历程

```html
<section class="glass rounded-[28px] p-6">
  <h2 class="section-title text-2xl font-bold mb-6">项目里程碑</h2>
  <div class="space-y-5">
    <div class="flex gap-4">
      <div class="w-16 text-sm text-cyan-200">Q1</div>
      <div class="flex-1 rounded-2xl bg-white/5 border border-white/10 p-4">
        <div class="font-semibold">需求确认与方案定稿</div>
        <div class="text-slate-300 text-sm mt-2">明确功能边界、预算与交付节奏。</div>
      </div>
    </div>
  </div>
</section>
```

### B. 过程流 / 流程带

适合：
- 操作流程
- 执行路径
- 业务流

```html
<div class="grid md:grid-cols-4 gap-4">
  <div class="glass rounded-2xl p-5">
    <div class="text-cyan-300 text-xs tracking-[0.2em] uppercase">Step 1</div>
    <div class="text-xl font-bold mt-3">需求梳理</div>
    <div class="text-slate-300 text-sm mt-2">先做范围确认与优先级判断。</div>
  </div>
</div>
```

### C. 逻辑树 / Issue Tree

适合：
- 原因拆解
- 结论支撑
- 决策分层

```html
<section class="glass rounded-[28px] p-6">
  <h2 class="section-title text-2xl font-bold mb-6">问题拆解</h2>
  <div class="grid lg:grid-cols-3 gap-4">
    <div class="rounded-2xl bg-cyan-500/15 border border-cyan-400/20 p-5">
      <div class="font-bold">核心问题</div>
      <div class="text-slate-200 mt-2">当前最优开发路径是什么？</div>
    </div>
    <div class="rounded-2xl bg-white/5 border border-white/10 p-5">
      <div class="font-bold">变量 1</div>
      <div class="text-slate-300 mt-2">预算与报价差距</div>
    </div>
    <div class="rounded-2xl bg-white/5 border border-white/10 p-5">
      <div class="font-bold">变量 2</div>
      <div class="text-slate-300 mt-2">管理与交付稳定性</div>
    </div>
  </div>
</section>
```

### D. 导图 / Cluster Map

适合：
- 主题发散
- 会议脑图
- 能力地图

```html
<section class="glass rounded-[28px] p-6">
  <h2 class="section-title text-2xl font-bold mb-6">主题导图</h2>
  <div class="grid lg:grid-cols-[1fr_2fr] gap-6 items-center">
    <div class="rounded-full w-44 h-44 mx-auto bg-gradient-to-br from-fuchsia-500 to-violet-600 flex items-center justify-center text-center font-bold">
      核心议题
    </div>
    <div class="grid sm:grid-cols-2 gap-4">
      <div class="rounded-2xl bg-white/5 border border-white/10 p-4">预算</div>
      <div class="rounded-2xl bg-white/5 border border-white/10 p-4">资源</div>
      <div class="rounded-2xl bg-white/5 border border-white/10 p-4">周期</div>
      <div class="rounded-2xl bg-white/5 border border-white/10 p-4">风险</div>
    </div>
  </div>
</section>
```

### E. 决策树

适合：
- 方案选择
- 分支判断
- go / no-go

```html
<section class="glass rounded-[28px] p-6">
  <h2 class="section-title text-2xl font-bold mb-6">决策树</h2>
  <div class="space-y-4">
    <div class="rounded-2xl bg-amber-500/15 border border-amber-400/20 p-5 font-semibold">是否有可信技术负责人长期跟进？</div>
    <div class="grid md:grid-cols-2 gap-4 pl-4">
      <div class="rounded-2xl bg-white/5 border border-white/10 p-5">有：可考虑外包 + 顾问模式</div>
      <div class="rounded-2xl bg-white/5 border border-white/10 p-5">没有：优先仅外包公司</div>
    </div>
  </div>
</section>
```

### F. SWOT 2x2

适合：
- 战略评估
- 项目优劣势梳理

```html
<div class="grid md:grid-cols-2 gap-4">
  <div class="glass rounded-2xl p-5"><div class="font-bold text-emerald-300">Strength</div></div>
  <div class="glass rounded-2xl p-5"><div class="font-bold text-cyan-300">Opportunity</div></div>
  <div class="glass rounded-2xl p-5"><div class="font-bold text-amber-300">Weakness</div></div>
  <div class="glass rounded-2xl p-5"><div class="font-bold text-rose-300">Threat</div></div>
</div>
```

### G. 四象限矩阵

适合：
- 优先级排序
- 风险 / 收益判断
- 复杂度 / 价值对照

```html
<section class="glass rounded-[28px] p-6">
  <h2 class="section-title text-2xl font-bold mb-6">优先级矩阵</h2>
  <div class="grid md:grid-cols-2 gap-4">
    <div class="rounded-2xl bg-emerald-500/15 border border-emerald-400/20 p-5">高价值 / 低复杂度</div>
    <div class="rounded-2xl bg-cyan-500/15 border border-cyan-400/20 p-5">高价值 / 高复杂度</div>
    <div class="rounded-2xl bg-slate-500/15 border border-slate-300/20 p-5">低价值 / 低复杂度</div>
    <div class="rounded-2xl bg-rose-500/15 border border-rose-400/20 p-5">低价值 / 高复杂度</div>
  </div>
</section>
```

### H. 对比矩阵

适合：
- 供应商对比
- 产品方案对比
- 能力对比

推荐：
- 3-6 个维度时，优先用矩阵，不要只写散点描述

### I. 路线图 / Roadmap

适合：
- 阶段目标
- 上线节奏
- 资源投入计划

```html
<section class="glass rounded-[28px] p-6">
  <h2 class="section-title text-2xl font-bold mb-6">阶段路线图</h2>
  <div class="grid md:grid-cols-3 gap-4">
    <div class="rounded-2xl bg-white/5 border border-white/10 p-5">
      <div class="text-cyan-300 text-sm">阶段一</div>
      <div class="text-xl font-bold mt-2">需求与设计</div>
    </div>
  </div>
</section>
```

### J. 漏斗 / Funnel

适合：
- 用户转化
- 商机推进
- 销售阶段流失

### K. 组织图 / 协作关系图

适合：
- 团队分工
- 外部合作方关系
- 职责边界说明

```html
<div class="grid md:grid-cols-3 gap-4">
  <div class="glass rounded-2xl p-5 text-center">业务负责人</div>
  <div class="glass rounded-2xl p-5 text-center">外包公司</div>
  <div class="glass rounded-2xl p-5 text-center">技术顾问</div>
</div>
```

### L. 闭环 / Flywheel

适合：
- 用户增长闭环
- 经营循环
- 产品迭代飞轮

## 3. 组合建议

### 决策型汇报

推荐组合：
- 对比矩阵 + 决策树 + 风险卡片

### 战略型汇报

推荐组合：
- SWOT + 四象限 + 路线图

### 项目推进型汇报

推荐组合：
- 时间线 + 流程带 + 里程碑卡片

### 会议纪要型汇报

推荐组合：
- 导图 + 逻辑树 + 行动项表格

## 4. 使用规则

- 不要为了炫技每页都上结构图
- 结构图应服务于“把复杂关系讲清楚”
- 一页只放 1 种主结构
- 如果逻辑图已经清晰，就不要再堆大量段落

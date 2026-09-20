# Professional Daily Report Requirements

## Professional-Work Filter

Include a work item when the day's evidence shows at least one of the following:

- a created or materially updated code, data, report, document, model, figure, pipeline, or other reusable artifact;
- a multi-step professional analysis or computation with concrete results;
- an implementation, model iteration, data-processing run, or experimental workflow with verification evidence;
- a substantial in-progress project with measurable progress, an explicit checkpoint, or a material blocker;
- a decision that changes a professional project's method, scope, priority, architecture, or release status.

Exclude items that are only:

- simple factual questions, one-record lookups, or brief exploratory chat;
- casual conversation, arithmetic, personal advice, or general knowledge;
- wording polish, short message rewriting, or isolated copyediting without a professional deliverable;
- a trivial action whose effort and output do not justify task-level reporting;
- the act of generating the daily report itself.

Judge the event, not the session title or thread length. A session can contain both substantive and trivial turns; retain only the substantive work. A technically detailed answer is not automatically a professional task if it is still a one-off lookup with no meaningful project output.

Merge related turns, retries, and substeps into one project-level work item. Do not split a single project into many bullets merely because several modules or commands were involved.

## Executive Writing Style

Write for a manager or colleague who needs to understand what moved forward, why it matters, and what happens next. The report is not a technical execution log.

Use this information order inside each item:

`professional outcome or decision value -> material scope or impact -> verification or next status`

### Keep

- completed professional outcomes and the problem they solve;
- changes in project readiness, coverage, quality, decision confidence, or delivery status;
- methods or framework changes when they materially affect correctness or downstream use;
- validation expressed in plain language, such as `完成 327 项测试并全部通过`;
- blockers only when they require coordination, change priorities, or materially affect delivery;
- a small number of metrics only when a non-specialist can understand their decision value.

### Omit Or Translate

- file counts, byte sizes, checksums, query counts, row counts, process counts, or snapshot counts when they merely prove routine execution;
- internal commit hashes, session IDs, build IDs, temporary paths, script names, or model-stage labels that an external reader cannot interpret;
- raw benchmark values, excessive decimal precision, fold names, intermediate model codes, or technical abbreviations unless they drive a decision;
- mechanical artifact inventories such as `PPT、Excel、TSV、HTML` or `详细 PPT 和单页 PPT`;
- implementation narration such as copying files, retrying commands, rebuilding manifests, or running hash checks;
- developer jargon a non-engineer manager may not know: 主分支、分支、合并/merge、commit、worktree、vendor、回归测试、NVML/procfs 等底层接口名。Translate to plain outcomes: 「已合并回主分支」→「改动已全部提交生效」；「在独立分支待合并」→「改动已提交，待并入正式版本」；「回归测试通过」→「经自动化测试确认」；version strings and branch names are internal identifiers and stay out;
- unexplained before/after numbers such as answer character counts when the reader cannot tell what content was improved.

Translate low-level evidence into its professional meaning. Examples:

- Instead of `复制 71 个文件并完成 SHA-256 核验`, write `完成空间转录组数据整合与完整性审计，为后续统一计算提供可靠输入`.
- Instead of listing output formats, write `形成可用于汇报和后续分析的数据覆盖比较材料`.
- Instead of a commit hash, write `相关改动已完成验证并发布`.
- Instead of raw model performance, write `阶段训练结果优于现有基线` only when the comparison is supported and useful.

### Negative Or Incomplete Results

Do not foreground routine negative findings in the concise version. Handle them as follows:

- If the negative result changes a decision, express the positive decision value: `完成公开来源增量评估，确认当前应转向受控数据申请`.
- If it is a material blocker requiring action, place it in `阻塞与失败` or the plan, not in the headline achievement.
- If it is routine monitoring with no impact, omit it from the concise version.
- Never hide a material risk, failed validation, or incomplete status. State it briefly and in the section where it affects decisions.

### Numbers

Use numbers selectively. Keep them when they communicate scale, coverage, delivery confidence, or a decision boundary. Round or verbalize when precision adds no value.

- Prefer `覆盖约三分之二的目标范围` over a long fraction when the exact value is not decision-critical.
- Prefer `完成 327 项测试并全部通过` over `327/327`.
- Omit raw scores such as `PU-AUC 0.938703` unless the report is specifically for model-performance review.
- Do not combine more than two or three numbers in one bullet unless the comparison itself is the result.

### Length

- `今日概览`: normally 2-3 short sentences.
- Each detailed bullet: normally one sentence; use two only when status or impact needs clarification.
- Each concise bullet: one sentence focused on the main outcome.
- Prefer 3-6 substantive work items over exhaustive coverage of every session.

## Task Titles

Never copy a vague or mismatched session title without checking it against the day's actual work. Derive a concise semantic title using:

`specific object or project + version/module/dataset when useful + work type or outcome`

The title must make sense to a reader who has not seen the conversation and must accurately cover the content after the colon.

Good titles:

- `RDC 靶点评估 v1.25 框架重构与排名总分优化`
- `RDC Target Agent 回答去冗余与质量评测`
- `泛癌蛋白组受控数据获取计划与缺口补齐`
- `单细胞/空间转录组数据导入审计与 D3 计算方案`

Avoid generic titles such as:

- `评估最新框架`
- `特征比较和探索`
- `数据补充`
- `总结说明`
- `评估并优化回答`

When the original title and actual activity do not match, use the activity-derived title. Do not create a task bullet from a simple lookup merely to make the title fit.

## Output Path

Default to:

`/home/zhangfengfeng/reports/daily/YYYY/MM/YYYY-MM-DD.md`

Requirements:

- one Markdown file per local calendar day;
- year and month archive levels;
- ASCII-only path components;
- title date and filename date must match;
- inspect and preserve clearly user-authored notes when refreshing an existing report.

## Detailed Report

Follow the base daily-report schema in [report-schema.md](report-schema.md) and keep this section order:

1. `# Claude 日报 - YYYY-MM-DD`
2. metadata with timezone, generation time, and coverage accounting
3. `## 今日概览`
4. `## 已完成`
5. `## 进行中`
6. `## 阻塞与失败`
7. `## 关键决策`
8. `## 产物与文件`
9. `## 验证结果`
10. `## 下一步建议`
11. `## 简略版`
12. `## 可复制版本`

Never place weekly content in the daily report. Friday daily reports use the same section order as every other daily report; the weekly report is a separate file governed by [weekly-report-requirements.md](weekly-report-requirements.md).

Only professional work belongs in the detailed sections. Preserve meaningful versions, validation conclusions, artifact references, incomplete status, and blockers, but present them through the executive-writing rules above. Do not claim a final ranking, release, score, download, or completed test while the corresponding computation is still running.

Group related implementation or computation under the same project identity. For example, D1 repair, D6 mapping repair, missing-aware training, and constrained ranking can be reported as stages of one RDC evaluation-framework iteration rather than unrelated tasks.

## Concise Version

The concise version follows the detailed report and uses this structure:

```markdown
## 简略版

**日期：YYYY-MM-DD**

### 今日任务

- **具体对象 + 工作类型：** 用一句话说明核心产出及其项目价值；仅在影响决策时补充状态。

### 明日计划

- **具体对象 + 下一动作：** 写明下一步动作及预期检查点或产物。
```

Each bullet must follow `标题：任务内容`. Use a specific object in every title. Do not use the original session title when it fails to summarize the work.

The concise version is not a second transcript or a compressed technical log. Include only substantive professional tasks, normally one bullet per project or coherent workstream. Remove routine negative monitoring, internal identifiers, raw technical scores, mechanical artifact lists, and low-value verification counts. Keep incomplete status only when it materially changes the reader's understanding or next action.

## Copy-Ready Plain-Text Version

Place `## 可复制版本` after the concise version and make it the final section of the file. Inside it, add one fenced `text` code block that repeats the concise version's date, subsection labels, task titles, and task content without changing their meaning.

Inside the code block:

- use plain text only: no Markdown headings, bullets, bold markers, backticks, or links;
- number `今日任务` from 1 using `1、2、3……`, then restart `明日计划` from 1;
- keep subsection labels such as `今日任务` and `明日计划` as unmarked plain-text lines;
- prefix every numbered daily item with one priority label and keep the `序号、优先级 标题：任务内容` form, for example `1、VVV 具体对象：任务内容`;
- within `今日任务` and `明日计划` separately, sort items by `VVV` first, then `VV`, then `V`; preserve the subsection boundary and number each subsection independently from 1;
- use `VVV` for work that directly affects a core deliverable, major decision, release/readiness gate, or time-sensitive blocker; use `VV` for material supporting work; use `V` for lower-urgency follow-up that is still professionally report-worthy;
- in each subsection, assign at most three `VVV` items and normally one or two items for each of `VV` and `V`; do not force every tier when there are too few supported items;
- preserve every concise item semantically, although priority sorting may change its order within the same subsection;
- do not add explanations, coverage notes, or content absent from the concise version.

Example:

````markdown
## 可复制版本

```text
日期：YYYY-MM-DD

今日任务
1、VVV 具体对象 + 工作类型：核心产出及其项目价值。

明日计划
1、VV 具体对象 + 下一动作：下一步动作及预期检查点或产物。
```
````

## Tomorrow's Plan

Derive tomorrow's plan from explicit next actions, unfinished professional work, active blockers, and the detailed report's next-step recommendations.

- Use the same `specific title: content` format.
- Make each workday plan specific enough to be checked at the next report. It should normally state: `action + concrete object or scope + expected deliverable, decision, or checkpoint`.
- Add a material dependency or sequence only when it changes whether the action can be completed.
- Prefer concrete verbs such as `整理、补齐、提交、完成、核查、冻结、形成、发布` over vague verbs such as `推进、跟进、持续优化` used alone.
- Keep plans at the professional-deliverable level. Do not expand into commands, scripts, internal IDs, file counts, or step-by-step execution notes.
- Do not add personal reminders, trivial follow-ups, simple questions, or invented commitments.
- If an action is only a recommendation rather than an agreed commitment, say `建议` or `拟` in the content.
- Respect the configured work schedule (run `scripts/work_schedule.py` for tomorrow's status). If tomorrow is a rest day or statutory holiday, keep `明日计划` and write only `- **休息安排：** 明日为休息日，不安排工作任务。`（节假日可注明节日名称）; do not move future work into the rest day.

Weak plan:

`- **RDC 靶点评估框架：** 继续推进模型优化。`

Preferred plan:

`- **RDC 靶点评估框架：** 完成安全约束优化及历史版本对照，形成统一排名与总分是否可冻结的结论。`

Weak plan:

`- **泛癌蛋白组数据获取：** 跟进受控数据。`

Preferred plan:

`- **泛癌蛋白组数据获取：** 补齐 UK Biobank 与 ARIC 申请材料清单，明确待用户或机构提供的信息，并形成可提交版本。`

## Final Quality Check

Before saving, verify:

- the base skill's session coverage counts (indexed/candidate/read/in-day activity/unreadable) are present;
- every reported outcome has same-day evidence;
- trivial conversations and simple lookups are absent from both detailed and concise sections;
- related work is merged rather than fragmented;
- every concise title identifies the concrete object and matches its content;
- every concise bullet leads with outcome and project value rather than process evidence;
- routine negative results, internal IDs, raw benchmark values, hashes, file counts, and format inventories are absent from the concise version;
- any retained number is understandable and decision-relevant;
- every workday plan contains a concrete action, object or scope, and an expected deliverable or decision point;
- the concise version contains both `今日任务` and `明日计划`;
- Friday daily reports contain no weekly summary or next-cycle plan; those belong only in the separate weekly file;
- `可复制版本` is the final section and contains exactly one `text` code block;
- the daily copy-ready block matches the concise version semantically, contains no Markdown markers, and starts both `今日任务` and `明日计划` numbering from 1;
- every daily copy-ready item has a VVV/VV/V label; each subsection is sorted from VVV to V, has no more than three VVV items, and normally has no more than two VV or two V items;
- the output path contains no Chinese directory or filename components;
- the saved file exists and its title date matches its filename.

Read the concise version once as a manager with no conversation context. If a bullet is unclear, too trivial, or titled too generically, rewrite or remove it.

# Friday Weekly Report Requirements

## Work Schedule

Use `Asia/Shanghai` local dates.

- Regular week: Monday through Friday are workdays; Saturday and Sunday are rest days (双休).
- First week of each month — the Monday-to-Sunday week that contains the 1st of a month: Monday through Friday and Sunday are workdays; Saturday is a rest day. That Sunday's work belongs to the FOLLOWING Friday's weekly report; the Saturday-to-Friday cycle below guarantees this automatically.
- Chinese statutory holidays override the base schedule: official holiday dates are rest days even on weekdays, and State Council makeup workdays (调休补班日) are workdays even on weekends.

Run `scripts/work_schedule.py YYYY-MM-DD` instead of calculating the schedule mentally. Treat its dates as local calendar dates. If the output reports `holiday_data_year_covered: false`, the holiday table for that year has not been added yet: state this limitation in the report and update the `HOLIDAYS`/`MAKEUP_WORKDAYS` tables in the script from the State Council notice (国务院办公厅关于该年部分节假日安排的通知) before relying on holiday classification.

## Friday Reporting Cycle

Every Friday, create a weekly Markdown file separate from that day's daily report. Never append the weekly report, weekly concise summary, or next-cycle plan to the daily file.

The weekly evidence interval is the preceding Saturday at `00:00:00` through the next Saturday at `00:00:00`, start-inclusive and end-exclusive. In displayed form, label it as `previous Saturday - current Friday`.

This Saturday-to-Friday cycle is intentional:

- a working Sunday from a month's first week is included in the following Friday report;
- no Sunday work is lost merely because it occurs after that week's Friday;
- the same event must not appear in two weekly reporting cycles.

List the scheduled workdays that fall inside the reporting interval (from `weekly_scheduled_workdays`). Also state the current week's type (常规双休 or 本月首周) and any statutory holidays or makeup workdays inside the interval (from `weekly_holidays` and `weekly_makeup_workdays`).

If the reporting Friday itself is a statutory holiday, still produce the weekly report on request; note that the Friday was a holiday. When a holiday makes the user unavailable on Friday, the next daily-report request after the cycle end may also trigger the missed weekly report — ask only if the user's intent is unclear.

## Evidence Collection

Keep the base `claude-daily-report` evidence rules, but apply them to the weekly interval.

1. Run the bundled collector once per local day in the interval (seven runs of `collect_sessions.py --date <day> --utc-offset "+08:00"`), and merge the results by session.
2. Keep only events explicitly timestamped inside the interval.
3. Read raw transcripts only when a specific claim needs confirmation, with targeted `grep`/`jq` on a single session file.
4. Optionally collect git evidence over the interval with the `git-daily-report` collector (`--since`/`--until`).
5. Apply the same professional-work filter as the daily report.
6. Deduplicate work already repeated across turns or days and merge it at the project/workstream level.

Apply the daily executive-writing style to the weekly report. Weekly bullets should emphasize accumulated outcomes, decisions, and project movement rather than summing technical counts from individual days.

Maintain separate weekly coverage counts: indexed sessions, candidates, successfully read sessions, sessions with in-interval activity, and unreadable/truncated sessions. Do not reuse daily counts as weekly counts.

## Weekly Output Path And Naming

Write the weekly report to:

`/home/zhangfengfeng/reports/weekly/YYYY/MM/month-MM-week-NN.md`

- Use the reporting Friday's calendar year and month for `YYYY/MM`.
- Repeat the reporting month as `MM` in the filename and derive `NN` from the Friday's day of month: 1-7 is week 1, 8-14 week 2, 15-21 week 3, 22-28 week 4, and 29-31 week 5.
- Assign a Saturday-to-Friday cycle to the month containing its reporting Friday. This also resolves cycles that cross a month boundary.
- Title the document `# M 月第 N 周周报`; do not use an annual or ISO week number in the title.
- Keep all directory and filename components ASCII-only.
- Write one weekly report per reporting cycle. Inspect and preserve clearly user-authored notes when refreshing an existing file.

## Detailed Weekly Report

Use this structure:

````markdown
# M 月第 N 周周报

> 统计周期：YYYY-MM-DD 至 YYYY-MM-DD  
> 本周班型：常规双休 或 本月首周（周日上班）  
> 周期内计划工作日：YYYY-MM-DD、...  
> 周期内节假日/调休：如有则列出日期和名称，否则写 无  
> 周报覆盖：索引 N 个会话，读取 M 个候选会话；必要时注明范围限制。

## 本周概览

用 2-4 句话概括本周期最重要的专业成果、进展和风险。

## 本周核心成果

- **具体对象 + 工作类型：** 合并一周内相关子步骤，用一句话说明核心成果、影响和交付状态。

## 本周进行中与阻塞

- **具体对象 + 当前状态：** 说明剩余工作、阻塞及影响。

## 反思与改善

用一个简短段落综合说明本周最值得反思的问题、影响和下一周期的改善动作，不使用项目符号或按任务拆分。

## 下周期计划

- **具体对象 + 下一动作：** 写明下一周期的具体动作、工作范围及预期交付物或决策点。

## 简略版

**周期：YYYY-MM-DD 至 YYYY-MM-DD**

### 本周总结

- **具体对象 + 周度成果：** 用一句话概括本周专业成果、项目价值和必要状态。

### 反思与改善

用 1-2 句话综合说明本周关键经验及对应改进动作，不使用项目符号或按任务拆分。

### 下周期计划

- **具体对象 + 周期动作：** 写明下一报告周期的重点动作、范围和预期检查点。

## 可复制版本

周期：YYYY-MM-DD 至 YYYY-MM-DD

本周总结

```text
1、具体对象 + 周度成果：本周专业成果、项目价值和必要状态。
```

反思与改善

```text
本周关键经验及对应改进动作，不使用序号。
```

下周期计划

```text
1、具体对象 + 周期动作：下一报告周期的重点动作、范围和预期检查点。
```
````

Use `无已识别项` when a required weekly subsection has no supported item.

The weekly concise section contains `本周总结`, `反思与改善`, and `下周期计划`; daily items and tomorrow's plan remain in the separate Friday daily report. The daily and weekly files may mention the same project because they cover different scopes, but do not copy identical text.

The next-cycle plan must respect the schedule: do not plan work onto statutory holidays or rest days in the coming cycle; when a holiday materially shortens the cycle, say so in the plan.

Reflection must be evidence-based, improvement-oriented, and concise. Synthesize the most important cross-workstream lesson into one paragraph of normally 1-3 sentences using `observed issue or pattern -> impact -> concrete improvement`. Do not use bullets, numbered items, task-by-task headings, generic self-criticism, blame, personality judgments, routine negative results, or unsupported causal claims.

The final `可复制版本` must repeat the weekly concise content with one fenced `text` code block per subsection (`本周总结`, `反思与改善`, `下周期计划`). Write the cycle dates and subsection labels as plain lines outside the blocks; each block starts directly at its content — numbered items from 1 for `本周总结` and `下周期计划`, an unnumbered paragraph for `反思与改善` — so the user can copy one module in one selection (user-confirmed preference, 2026-09-22). Remove all Markdown markers inside blocks. Do not add content that is absent from the concise version.

## Weekly Quality Check

Verify that:

- the target date is Friday;
- the weekly interval is exactly previous Saturday through current Friday;
- the interval contains seven local dates and has no overlap with the prior weekly cycle;
- the week type, scheduled workdays, holidays, and makeup workdays agree with `scripts/work_schedule.py` output;
- all weekly claims have evidence inside the weekly interval;
- daily and weekly coverage counts remain separate;
- the weekly report exists as a separate file and no weekly sections remain in the Friday daily report;
- the weekly filename identifies the reporting month and its two-digit month-relative week number;
- the weekly title states the matching month and month-relative week number, not an annual week number;
- the detailed and concise sections both include `反思与改善` before `下周期计划`;
- reflection is one short, evidence-based paragraph with a concrete improvement and no bullets, numbering, or task-by-task split;
- the concise section orders `本周总结`, `反思与改善`, then `下周期计划`;
- `可复制版本` is last, matches the concise version semantically, uses one plain-text code block per subsection with labels outside the blocks, starts `本周总结` and `下周期计划` numbering from 1 at the top of their blocks, and leaves the reflection paragraph unnumbered;
- no trivial conversations, simple lookups, or daily-report-generation activity appear as weekly work.

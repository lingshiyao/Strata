# Strata 智商 / 速度调优再审计与方案 (Re-audit & Proposal)

> 日期：2026-10-04　状态：**待评审（未执行任何改动）**
> 审计对象：`my-256k` 分支上 `strata-coder-iq1_m-ultra.*`（V4/V5 生产版）
> 证据来源：`strata-coder-iq1_m-ultra.log`（27 次真实会话）、`src/program/generate.cpp`（引擎 help 与参数解析）、`serve/server.py`（#123 预算实现）、`E:\Strata-data\packs\coder-iq1_m\tokenizer\`（双模模板）、三份配置 JSON。

---

## 第一部分：审计

### 1.1 方法说明

本次审计**不采信交接文档的结论数字**，而是回到两个一手证据源重新取证：

1. **生产日志**（`strata-coder-iq1_m-ultra.log`，434 KB，27 次引擎启动）：文档中的性能数字全部来自「干净环境下的 3 题基准」，而日志记录的是真实使用中的每一条请求。两者系统性偏离。
2. **引擎源码**：`generate.cpp` 的 `usage()` 列出了引擎暴露的**全部**可调参数。逐条比对当前配置，找出从未被触及的杠杆。

---

### 1.2 速度审计：文档声称 vs 生产实测

| 指标 | 交接文档声称 | 生产日志实测（27 次会话） | 判定 |
| :--- | :--- | :--- | :--- |
| 日常解码速度 | 54 ~ 71.7 tok/s，均值 **73.8** | **40.7 ~ 94.5**，中位约 **66** | 文档偏乐观 |
| 峰值解码 | 80.2 tok/s | 94.5（个别），常见 70~80 | 基本吻合 |
| 专家缓存命中率 | **85% ~ 90%** | **61% ~ 84%**，中位约 **73%** | 文档偏高约 12 个点 |
| MTP 投机接受率 | 引用「91.7% / 84.4%」 | MTP 实际 **44% ~ 65%** | **概念混淆**（见 1.2.2） |
| 显存安全余量 | 95 MiB，称「最优稳健点」 | 引擎 **22 次**报 LOW，建议 reserve **799~892**；**1 次 0 MiB** | **危险，判错** |
| Windows 大页 | 「已消除 CPU TLB 缺失」 | **27 次** `large pages refused`，实际跑 **4 KB 页** | **未生效** |
| KV 流式 VRAM 命中 | 97.01% @247K | 98.2% ~ 99.0% @60K | 吻合 |

#### 1.2.1 显存安全垫判错（最高优先级）

文档 §5.1 把 `--vram-reserve-mib 380` 定为「最优稳健点」，理由是「剩余显存 95 MiB，净增 164 个专家槽位」。但引擎自己在每次启动后都给出警告：

```
strata serve: 93 MiB of VRAM free with everything loaded - LOW: requests may stall;
              add --vram-reserve-mib 799 to the config's args (or lower --max-context)
strata generate: only 0 MiB free once the slots are written (reserve 380 MiB); shrinking the expert cache
```

27 次会话中，**22 次**触发 LOW 警告，**27 次**触发槽位回缩，甚至有 1 次落到 `0 MiB free`。引擎的建议值稳定落在 **799 ~ 892**。

**结论**：当前配置不是「稳健点」，而是**贴着 OOM 红线运行**。95 MiB 的余量连一次 KV 流式回填或视觉请求的临时缓冲都扛不住。这属于稳定性缺陷，优先级高于任何性能收益。

#### 1.2.2 MTP 接受率被「suffix 草稿」数字掩盖

文档 §5.4 / §8 引用「Suffix 草稿接受率 91.7% (11/12)」「84.4% (65/77)」。但日志显示这是**两套完全不同的机制**：

- **suffix draft**（`--suffix-draft`，prompt 内查找重复片段）→ 接受率确实很高：`suffix drafts: 89 windows, 251 of 313 drafts accepted`（80%）。
- **MTP 投机头**（`--spec 5`，模型自己预测）→ 接受率低得多：

```
drafts accepted 233 of 526   → 44.3%
drafts accepted 460 of 738   → 62.3%
drafts accepted 396 of 873   → 45.4%
drafts accepted 920 of 1780  → 51.7%
drafts accepted 676 of 785   → 86.1%
```

**结论**：真实 MTP 接受率中位约 **55%**，且波动极大。文档用 suffix 的高数字暗示投机很有效，掩盖了 MTP 只有一半命中这一事实。`--spec 5` 相比 `--spec 4` 的收益（文档称 +0.7 tok/s）本来就落在噪声内，值得重测。

#### 1.2.3 大页优化从未生效

文档 §5.4 声称 `tools/enable-large-pages.ps1` 把 25 GB 专家池「从 629 万个 4 KB 页压缩为 1.2 万个 2 MB 页，消除 CPU TLB 缺失」。日志打脸：

```
strata generate: expert arena: cudaHostRegister PORTABLE ok;
  large pages refused for 25149046784 B (GetLargePageMinimum=2097152,
  VirtualAlloc error 1450); using 4 KB pages
```

27 次全部拒绝，错误码两种：
- **1314 = ERROR_PRIVILEGE_NOT_HELD** → `SeLockMemoryPrivilege` 根本没拿到（脚本没跑 / 没重启 / 组策略覆盖）。
- **1450 = ERROR_NO_SYSTEM_RESOURCES** → 即使有权限，25 GB 连续大页也分配不出来（内存碎片）。

**结论**：这条优化目前是「文档里的胜利」。要么真正打通（先解决 1314 权限），要么从文档撤下。

#### 1.2.4 CPU 侧的硬天花板

```
strata generate: this CPU has no AVX-512: the expert kernels run on AVX-2
```

Core Ultra 7 270K（Arrow Lake）无 AVX-512，专家 kernel 跑 AVX-2。这是硬件限制，不可调，但意味着**CPU 专家池是当前主要瓶颈之一**——这也解释了为什么显存专家槽位（把计算搬上 GPU）的命中率如此关键。

---

### 1.3 智商审计

#### 1.3.1 【高危】双模 System Prompt 在 Hermes 路径下被静默关闭

这是本次审计**最严重的发现**。

`chat_template.jinja` 中，推理指令的注入逻辑是：

```jinja
{%- set resolved_reasoning_effort = reasoning_effort|default('xhigh') %}
{%- if resolved_reasoning_effort == 'high' %}{%- set resolved_reasoning_effort = 'xhigh' %}{%- endif %}
{%- if resolved_reasoning_effort == 'xhigh' %}
    {%- set reasoning_instructions = '<长提示词：Mode 1 或 Mode 2>' %}
{%- elif resolved_reasoning_effort == 'low' %}
    {%- set reasoning_instructions = '<low 提示词>' %}
{%- endif %}
```

**只有 `xhigh` 和 `low` 两个分支，没有 `medium`。**

而 `hermes-coder-ultra.bat` 第 13/40 行：

```bat
set "EFFORT=medium"
call hermes config set agent.reasoning_effort %EFFORT% --force
```

若 Hermes 把这个 `medium` 透传进请求体（`serve/server.py:800` 只在请求**没有**该字段时才用 shared-settings 覆盖），则 `reasoning_instructions` 为空字符串 → **Mode 1 和 Mode 2 注入的都是空** → 整个 V4 双模提示词工程在 Hermes 下完全失效。

旁证：`strata-coder-iq1_m-ultra.shared-settings.json` 里写的是 `"reasoning_effort": "high"`（→ xhigh）。所以**直接用 curl 测是好的，走 Hermes 就可能是坏的**——这正好能解释为什么基准测试有效、真实使用体感打折。

> **验证成本极低**：抓一次 Hermes 实际发出的请求体，或对比 medium/xhigh 两种情况下服务端构造的 prompt token 数（xhigh 应多出约 60 个 token）。

#### 1.3.2 推理预算 16384 是「硬截断」，不是「自然收敛」

`serve/server.py` 的 #123 实现：到达预算时，服务端**强制注入一段英文**并闭合思考：

```python
REASONING_WRAP_UP = "\n\nI have thought about this long enough; time to give my answer.\n</think>\n\n"
```

两个问题：
1. **语言错配**：模型的中文思考链里被塞进一句英文转折，可能打断连贯性、污染最终答案。
2. **文档自相矛盾**：文档 §7.1 引用「模型在 **23,105** token 顺利实现主动自然收敛」来论证 rep 1.08 的价值——但 23,105 > 16,384，说明那个结论来自**无预算或更高预算**的实验，与当前 16384 硬顶不是一回事。把两种条件下的观察混在一条结论里。

#### 1.3.3 统计效力不足（n=1）

文档 §8 的核心结论「Mode 2 语法通过率 72.2% vs Baseline 66.7%」= **13/18 vs 12/18**。差 1 道题，每题仅 1 次采样，无重复、无置信区间、无显著性检验。这类「+5.5%」在 n=18、单样本下完全可能是随机波动。

同时 Mode 2 仍有 **5 题 FAIL**（04 体素宝塔、07 赛博追击、08 鹈鹕飞行、15 吸血鬼幸存者、16 跳棋动画），失败模式清一色是低级缺陷：括号缺失、局部变量重名、正文混入草稿注释。也就是说**近三成任务仍交付不可运行的代码**，而文档的措辞偏向「重大突破」。

#### 1.3.4 ultra 的防循环比 256k 基线更弱（无实验支撑）

| 参数 | 256k 基线 | ultra（日常主力） |
| :--- | :--- | :--- |
| temperature | 0.5 | **0.6** |
| top_k | 40 | **20** |
| penalty_last_n | **512** | **256** |
| frequency_penalty | 0.15 | **无** |
| presence_penalty | 0.1 | **无** |
| min_p | 0.08 | 0.08 |
| repetition_penalty | 1.08 | 1.08 |

文档 §3 用整章论证「防死循环是生死线」，但日常使用的 ultra 反而把循环检测窗口砍半、去掉了两个惩罚项。**没有任何实验记录解释这个决定**。要么补实验，要么补齐防御。

---

### 1.4 从未被触及的引擎杠杆

从 `generate.cpp` 的 `usage()` 提取，当前 ultra 配置**完全没用**、也**没测过**的参数：

| 参数 | 当前状态 | 潜在收益 | 代价 / 约束 |
| :--- | :--- | :--- | :--- |
| `--expert-cache-per-layer` | 关闭 | 文档源码自述：默认共享计数策略在 256 槽时仅 **2.97%** 命中，per-layer 可达 21~70% | 有 profile 时效果待验证（见下） |
| `--kv k8v4` | 未用 | KV **816 vs 1056 B/cell**，省约 23% KV 显存 → 可多换约 300+ 专家槽位 | **与 `--kv-resident` 互斥**，要放弃 32K 常驻 |
| `--ple-row-cache N` | 默认 1,048,576 行 | PLE 表 **320,001,536 行**，当前仅缓存 0.33%；加大可减少 SSD 随机读 | 90 B/行，4M 行≈360 MB，16M 行≈1.4 GB |
| `--ple-inflight N` | 默认 64 | 提高 PLE 并发读深度 | — |
| `--ple-io mmap` | `direct`（默认） | 借 OS page cache 兜 PLE 热行 | 表 28.8 GB，不能整表驻留 |
| `--conversation-cache-mib N` | **0（关闭）** | 多轮会话免重复 prefill；日志显示长 prompt 冷读一次要 **19.4 s** | RAM（当前余量约 21 GB） |
| `--mtp-max-t M` | 未设 | 限制 MTP 窗口长度，抑制低接受率下的回退惩罚 | — |
| `--suffix-draft N` | 默认 3 | 扫描（该机制接受率高，值得加大） | — |
| `--adapt-every` / `--adapt-swaps` | 未设 | 自适应槽位交换 | 行为未知 |

**关于 `--expert-cache-per-layer` 的重要澄清**：日志显示当前策略并非「到达顺序」而是 profile 驱动：

```
strata generate: expert cache 3793 slots, 7.23 GiB of VRAM; policy is
                 PROFILE, ranked by routing frequency, no eviction.
strata generate: pre-filled 3793 of 3793 slots from the profile
```

因为配了 `--expert-profile`，槽位按全局路由频率排名填充。所以源码里那个 2.97% 的惨况**不适用于当前配置**——但反过来也说明：**文档「85~90% 命中」的声称与实际 73% 的差距，根源可能在 profile 的覆盖度（3793/12288 = 30.9% 的 pair 驻留）**，而不是 admission 策略。`--expert-cache-per-layer` 在 profile 模式下是否仍有增益，需要实测。

---

### 1.5 三个 benchmark 目录取证（新增）

对 `benchmark_prompts/`（18 题题面）、`benchmark_results/`（认知审计报告 + 6 个自主探针）、`benchmark_runs/`（47 次实验运行原始数据）做了取证。

#### 1.5.1 先说好话：聚合数字是诚实且可复现的

我用 PROGRESS.md 的逐题数据重算了文档 §8.1 的四个关键聚合值，**全部精确吻合**：

| 指标 | 文档声称 | 我从 PROGRESS.md 重算 |
| :--- | :--- | :--- |
| Baseline 总墙钟 | 173.9 min | 10,431.2 s = **173.85 min** ✓ |
| Mode 2 总墙钟 | 116.2 min | 6,972.8 s = **116.21 min** ✓ |
| Baseline 总思考 | 482,383 | **482,383** ✓ |
| Mode 2 总思考 | 288,233 | **288,233** ✓ |

**结论：文档没有编造数字。** 问题出在**实验设计**，不在数据。

#### 1.5.2 【关键】矩阵只对比了「截断 vs 截断」，从未测过不截断

`tools/run_comprehensive_matrix.py` 的组定义（第 27~104 行）：

```python
baseline    : budget=32000, penalty_last_n=256, repetition_penalty=1.08
group_a     : budget=16000, penalty_last_n=256, repetition_penalty=1.08
group_b     : budget=16000, penalty_last_n=1536, repetition_penalty=1.05
group_mode2 : budget=16000, ...（+ 终极提示词）
```

对照 PROGRESS.md 的思考 token 列：

- **Baseline 组 01~12 题的思考全部落在 31,966 ~ 32,006** → 说明它们**全部被 32K 预算截断**，不是自然收敛。
- **Mode 2 组 17/18 题的思考全部落在 16,358 ~ 16,399**（仅 16 题是 9,697）→ 说明它们**全部被 16,384 预算截断**。

**所以这 18 题矩阵本质上是在比较「截断在 32K」和「截断在 16K」哪个更不痛——而不是「哪个预算最优」。** 结论「16K 更好」实际是「16K 截断比 32K 截断省时」。

#### 1.5.3 审计报告自己的结论与最终配置冲突

同一目录下的 `REASONING_BUDGET_AUDIT_REPORT.md`（10-03）用 6 个**不设预算**（`reasoning_budget_tokens: 0`）的自主探针，得出的是完全不同的数字：

| 探针 | 自然收敛思考 token |
| :--- | :--- |
| Star Odyssey 3D | 37,095 |
| Pelican Flight | 38,272 |
| CyberDrive 2099 | 50,847 |
| Singularity 黑洞 | 54,200 |
| Realm of Titans | 54,486 |
| Voxel Pagoda | 59,948 |
| **均值** | **49,141（100% 无死循环、100% 自然闭合 `</think>`）** |

报告 §1.1 的结论是：**多轮 Agent 场景甜蜜点 24K~32K；单轮原始生成 36K~54K**。
报告 §4 Tier 2 明确写着：**「8,000~16,000 是复杂生产任务的『最低可用』预算」**。

**而最终固化的配置是 16,384 —— 恰好落在报告自己定义的「最低可用」档，而不是它推荐的甜蜜点。**

> 注：我原先猜测 baseline 组因缺少惩罚项而自毁，**该猜测已被证伪**——baseline 同样带 `rep 1.08 + min_p 0.08`。所以 32K vs 16K 的对比在采样上是公平的，差异只在预算与提示词。

#### 1.5.4 任务 02（Balatro）的产物无法被该 harness 度量

| 组 | `artifact.html` 实际大小 | metrics 里的 `code_bytes` |
| :--- | :--- | :--- |
| baseline/02 | **665 B** | 640 |
| group_mode2/02 | **572 B** | 551 |

打开 `group_mode2/02/artifact.html` 全文，它只是一个外壳：

```html
<link rel="stylesheet" href="./css/main.css" />   <!-- 不存在 -->
<script type="module"> import { initialize } from './js/main.js'; </script>  <!-- 不存在 -->
```

原因：题面 02 要求「**严格 ES6 模块化多文件工程**」，而 harness 只保存单个 `artifact.html` → 多文件产出未被回收。**这是 harness 的能力缺口，不是模型失败。**

同时暴露出文档 §8.2 的「Mode 2 体积」列口径问题：task 02 标称 **45.1 KB**，而实际产物是 572 B。验算可知该列 ≈ `content_tokens × 3.2`（13,696 × 3.2 ≈ 45 KB），即**「生成了多少字节文本」而非「落盘产物多大」**。文档 §8.1「正文体量稳定（271K vs 290K）」同理，是 token 数而非产物体积。

#### 1.5.5 一个仍然存在的风险：客户端采样可以击穿服务端防线

审计报告 §2.3 对 OpenCode 死循环的根因判定是：

> *"OpenCode connected to Strata with standard greedy/low-temperature sampling **without `repetition_penalty` or `min_p`**"*，叠加 `opencode.jsonc` 里 `"limit": { "output": 163840 }`。

而 `serve/server.py:1013` 的合并顺序是 `{**sampling_defaults, **shared}`，**再被请求自带字段覆盖**（`req_values` 优先级最高）。**只要客户端显式传了采样值，服务端配置里的防循环参数就会被顶掉。** 这条风险至今没有防护。

#### 1.5.6 附带确认

- 服务端强制收尾串 `"I have thought about this long enough; time to give my answer."` 在真实 OpenCode 会话（TEST8B/TEST9B Turn 3）中被实际观测到 → 印证 §1.3.2 的硬截断机制真实生效。
- 全部 47 次运行 `loop_detected: false` → 在这批评测里死循环已不复现，文档 §3 的死循环叙事属于历史故障。
- `baseline/` 每题目录含 `cognitive_analysis.md`（法医级审计），`group_mode2/` 没有 → 认知分析只对基线做过。

---

## 第二部分：方案（按优先级排序）

> 前提：**现状可用，这是调优不是修 bug**。排序依据 = 杠杆大小 × 证据强度 ÷ 风险。
> 总原则：不动任何基准文件（`*-256k.*`）；实验全部派生新命名文件；劣化即删；不劣化既有资产。

### 2.0 排序逻辑：瓶颈到底在哪

速度的**主导项是专家缓存命中率**。GPU 只驻留 3793 / 12288 个 (layer, expert) 对，未命中的专家落到 CPU 池，而本机 **CPU 无 AVX-512**（引擎日志自述跑 AVX-2，见 §1.2.4）。命中率每提升 1 个点，都直接减少落在慢 CPU 上的专家计算量。

实测命中率中位 **73%**，文档以为 **85~90%**——**这 12 个点就是当前最大的可回收空间**。

**本轮补充取证的三条新证据**（改写了优先级）：

1. `thinking budget reached` 在 27 次会话日志中出现 **0 次** → 16384 预算在生产中**从未触发**，模型真实思考从未达到 16384。**所以预算不是日常瓶颈**，调它收益有限（它只对基准类硬任务有意义）。
2. 日志显示 **prefill 阶段会借走 2470 / 3793 个缓存槽（4.68 GiB）** → 长 prompt 之后留给 decode 的常驻专家只剩约 **1323** 个。这极可能是命中率只有 73% 的直接原因，而**从未被调过**。
3. `--kv k8v4` 在 256K 下**不可用**（与 `--kv-resident` 互斥，而 256K 必须靠 resident 流式）→ 原方案中的 KV 形态实验作废。

---

### 第一优先：专家缓存命中率线（速度主导项）

> ## ⛔ 已判决：**T1 取消**（2026-10-04）
>
> 本节的推理**漏掉了一个关键事实**：引擎的专家缓存**不是静态的**，它带一个自适应层
> （`generate.cpp:5703-5756`，每 4 轮按对话实际路由频率淘汰/调入专家）。日志里的
> "no eviction" 只指 profile 层，自适应层**确实会淘汰**——实测 1600-token 运行换手 15,204 次。
>
> **离线实测（含自适应层模拟，校准误差 1.3%）**，N=3629：
>
> | 方案 | 命中率 |
> | :--- | ---: |
> | v1 静态 | 51.10% |
> | **v1 + 自适应（真实运行时）** | **75.59%** |
> | oracle 静态（完美排名） | 75.43% |
> | **oracle + 自适应（换 profile 的上限）** | **76.30%** |
> | 随机排名 + 自适应（对照） | 73.54% |
>
> 即：**自适应层已经吃掉了到 oracle 的全部差距**；在自适应之上换最优 profile 只多 **+0.71pt**。
> 按生产典型请求长度（385 位置）算，收益 **+2.95pt**；长会话 **+1.09pt**。
>
> 顺带：这也**解释了本节前提 2**（12GB 卡 2,537 槽 72% vs 16GB 卡 3,793 槽 73%，槽位 +50% 命中率仅 +1 点）
> —— 两边的自适应层各自收敛到同一负载平台，所以槽位数几乎不影响结果。前提 2 的观察是对的，
> 但它推出的结论（「命中率被排名卡住」）是错的：**真正卡住它的是自适应层的收敛速率，不是排名**。
>
> 详见 **`docs/T1_VERDICT_2026-10-04.md`**。原始数据与脚本在 `.workbuddy-ai/t1_probe/`。
> 未触碰任何基线文件。
>
> **替代方向**：自适应层参数扫描（`--adapt-every` / `--adapt-swaps`，两个**未文档化开关**，
> 默认 4 轮 / 96 次）。实测 `adapt_every` 由 13→4 位置有 **+2.4pt**，比换 profile 的 +0.7pt 更大。

**先修正两个前提**（查 `bench/results/2026-09-28-coder/README.md` 第 26–30 行后）：

1. ~~**当前 profile 不是编码专用的**~~ —— **此条已被推翻**。实测 coder profile 与出厂 profile 的
   序相关 Kendall tau = **+0.0032**（「重新索引」应保持顺序、tau 应为 ±1），coder 排名也不是 base
   的保序子序列（0/48 层单调），两者 top-3629 重合仅 **15.0%**。所以 README 那句
   「the shipped 48 × 512 ranking, re-indexed」**与文件实际内容不符**，建议修正 README。
   （但这对 T1 的判定已无影响——见上方判决框。）
2. **命中率更像被 profile 排名卡住，而非槽位数**：同机同 profile 下，**12 GB 卡 2,537 槽 → 72%**，
   **16 GB 卡 3,793 槽 → 73%**。槽位 +50%，命中率仅 +1 点。→ 结论应改为：
   **两条曲线都被自适应层收敛到同一平台**，与「排名」或「槽位」都关系不大。

| 步骤 | 动作 | 预期收益 | 风险 | 权重 |
| :--- | :--- | :--- | :--- | :--- |
| ~~**T1-1**~~ | ~~用真实编码 trace 重建 profile~~ | **实测仅 +0.7pt（长会话）~ +3.0pt（385 位置）** | — | **取消** |
| **T1-1′** | **自适应层参数扫描**：`--adapt-every`(1/2/4/8) × `--adapt-swaps`(48/96/192) | 命中率 +2~3pt（`adapt_every` 13→4 位置 +2.4pt）；需权衡 0.167 ms/轮的拷贝成本 | 低 | **新头号** |
| **T1-2** | 联合扫描 `--vram-reserve-mib`(600/700/800) × `--kv-resident`(20480/24576/32768) | 可能**收益有限**（见前提 2）；顺带定 reserve 的安全值 | 低 | 降级 |
| **T1-3** | 关闭 prefill 借槽（`--no-prefill-borrow`）或调 `--prefill-until` | 解释「上下文越长命中率越低」（73%→61%），与槽位总量无关 | 低 | 保持 |
| **T1-4** | `--expert-cache-per-layer` on/off | 有 profile 时可能无变化 | 极低 | 保持 |

> ⚠️ 关于 T1-3 的 `--prefill-until`：本次实验发现它是**陷阱**。native IQ pack 下把批量 prefill
> 截断后，投机循环（`generate.cpp:5410` 立即 break 到 spec 路径）**不会消费剩余 prompt**，
> 模型会从「单 token 上下文」开始生成。该开关不能用来「把 prompt 送进被插桩的路径」。


> **为什么先做这条**：命中率是速度主导项，证据最硬，且 **T1-1 是纯软件改动、不占一字节显存**。前提 2 表明「加槽位」这条路已经接近饱和，真正的杠杆在**排名质量**。

#### T1-1 的两个执行前提（查证后新增）

**(a) profile 文件结构**（实测解析）：
```
data/expert-profile-coder.bin   98,328 B = 24B 头 + 12,288×4B 排名表 + 48×256×4B 反查表
  头: magic=STRP ver=1 layers=48 experts=256 slots=12288 entries=12288
  排名表前几项: (47,123) (33,66) (44,31) (31,236) (3,60) (27,57)
```
即：**一个「(层, 专家) 对的优先级列表」**。引擎按此列表从上往下填 VRAM 槽位。

**(b) `make_profile.py` 无法对「完整 base」重排名** —— 这是必须先修的坑：

```python
if not a.no_base:
    take(read_profile(a.base, ne))      # ① base 的全部排名先进
take(sorted(freq.items(), by=-count))   # ② trace 里「还没出现过的」对才追加
```
因为 `expert-profile-coder.bin` **已经排满了全部 12,288 对**，② 里的对全部已在 ① 中 `seen` → `n_trace = 0` → **输出的就是原封不动的旧排名**。

所以 T1-1 只有两条可行路径：
- **路径 A**：`--no-base` + **一份足够大、足够有代表性的编码 trace**（让绝大多数对都在 trace 里出现过），纯按编码路由频率重排。风险：trace 若偏窄，排名会劣于通用排名。
- **路径 B**：小改 `make_profile.py`，把「追加」改成「加权合并」（如 base 频率与 trace 频率按比例融合）。更稳，但要动代码。

**建议先走路径 A 做一次探针**（成本最低），若有效再考虑路径 B 精调。

**(d) T1-1 应分两阶段：离线先判、在线后验**（新增，显著降低成本）

引擎 `--dump-routing` 的源码注释自己写着它的用途：

> *"One record per layer per position: `int32 layer, int32 k, k int32 ids, k float weights`. **It is what a hit-rate curve for a candidate VRAM expert cache is computed from**."*（`generate.cpp:237-240`）

也就是说，**命中率可以用一份 trace + 一份 profile 离线算出来**：命中率 = trace 中落在该 profile **top-N 排名内**的查找占比。这是纯计算——**不跑引擎、不占显存、不需要隔离脚手架**。

因此：

| 阶段 | 做什么 | 成本 | 门槛 |
| :--- | :--- | :--- | :--- |
| **1-A** | 跑一次 `--dump-routing`（普通 `generate` 模式，**非 serve**，不涉及 bin/json/bat）采集编码 trace | 一次引擎启动 | — |
| **1-B** | 离线算 **v1 profile** 的 top-3793 命中率，与实测 73% 对照 | 纯计算 | **自证代理可信**：若离线值≈73%，代理可用；差太远说明离线模型漏了自适应交换/prefill 借槽 |
| **1-C** | 离线生成并评估 **v2 排名**的命中率 | 纯计算 | **若 v2 离线不赢 → 直接终止，脚手架根本不用搭** |
| **2** | 仅当 1-C 明显更优，才搭 bin/json/bat 做真机 A/B，验证优势能否兑现为 tok/s | 串行两次引擎运行 | — |

> **保留意见**：离线命中率是**上限代理**——真机还有自适应槽位交换与 prefill 借槽（§2.0 第 2 条），实测必然低于离线值。所以离线只用来**做第一道筛子**，不能替代真机验证。

**(e) 隔离脚手架（阶段 2 才需要）** —— 新 bin / 新 json / 新 bat 三件套，复制自 ultra，但**必须同时改三处**，否则会静默不公平：

| 文件 | 改动 |
| :--- | :--- |
| `strata-coder-iq1_m-exp-profilev2.json` | ① `args` 的 `--expert-profile` → v2 路径；② **`log` → 新日志路径**（`server.py:2016/2021` 直接取 `cfg["log"]`，不改则两配置写同一日志） |
| `strata-coder-iq1_m-exp-profilev2.shared-settings.json` | 从 ultra 的**原样复制**（`server.py:2055-2064`：缺文件则 `shared={}`，`reasoning_effort` 不再注入 → 静默偏差） |
| `run-coder-exp-profilev2.bat` | 只改 `--config`；`STRATA_SPEC_COUPLED=1`、电源方案、双模菜单保持与 ultra 一致 |

> 生成 profile 时**必须带 `--n-expert 256`**：引擎按模型实际的 48×256 校验（`generate.cpp:2116`），默认的 512 会被拒绝启动。

**(c) 安全边界**：`data/expert-profile-coder.bin` 是 **git 已跟踪**文件（可回滚），但它被 **256k / tuned / ultra 三份配置共用**（三份 JSON 都指向同一路径）。因此：
- **绝不原地覆盖**；新文件命名 `expert-profile-coder-v2.bin`，只让实验配置指向它。
- 注意：profile 决定「哪些专家在 GPU、哪些在 CPU」，**两侧舍入不同 → 输出会有细微差异**（引擎日志有此警告，另有 `bench/results/2026-09-27-cache-parity` 声称同质量）。所以它是「速度旋钮」但**不是纯速度旋钮**，必须 A/B 后再决定是否采纳。

### 第二优先：PLE I/O（约占 15% token 时间，从未调过）

引擎源码自述 PLE gather「2.10–2.61 ms/token，因为 16 次行读是 16 次独立缺页」。按 66 tok/s（≈15 ms/token）折算约占 **15%**。而 PLE 表有 **320,001,536 行**，当前只缓存 1,048,576 行（**0.33%**），且 `--ple-io` 是 `direct`（无缓冲 SSD 读）。

| 步骤 | 动作 |
| :--- | :--- |
| **T2-1** | `--ple-row-cache` 1M → 4M → 16M（90 B/行，16M ≈ 1.4 GB；RAM 余量 21 GB 绰绰有余） |
| **T2-2** | `--ple-inflight` 64 → 128 → 256 |
| **T2-3** | `--ple-io direct` vs `mmap` |

### 第三优先：MTP 重扫（实际接受率仅 ~55%）

| 步骤 | 动作 |
| :--- | :--- |
| **T3-1** | 加 `--mtp-max-t` 限窗（从未设过），配合 `--spec` 3/4/5 重扫，记录**实际接受率**而非只看 tok/s |
| **T3-2** | `--suffix-draft` 3 → 4/6（该机制接受率约 80%，可能值得加大） |

### 第四优先：智商线（先验证，再谈调）

| 步骤 | 动作 |
| :--- | :--- |
| **T4-1** | 验证 `reasoning_effort` 是否被 Hermes 的 `medium` 覆盖（若覆盖，Mode 2 提示词全程为空，见 §1.3.1） |
| **T4-2** | **补上缺失的实验臂**：18 题矩阵只测过 32K 与 16K 两个截断点，从未测过不截断。而审计报告的 6 个探针证明模型自然收敛在 **37K~60K**。应加测 **budget=0（不截断）/ 32768 / 49152** 三个臂，重点看那 5 道失败题。这是当前**质量线信息量最高**的实验。 |
| **T4-3** | 攻 5/18 的语法失败（括号缺失、变量重名），n≥3 + 自动打分 |
| **T4-4** | 修 harness 缺口：题面 02 等多文件任务需要回收全部产物，否则该题永远无法度量（见 §1.5.4） |

> 注意：T4-2 与日常使用的关系是「低触发、高上限」——生产日志显示预算在日常从未触发（§1.5 之外，见 2.0 第 1 条），所以它不会拖慢日常；但它决定了**难题能不能做对**，而那 5 道失败题正是难题。

### 建议的第一步

**先跑 T1-1（重建 profile）+ T1-3（关 prefill 借槽）**。两者都是零/低成本，且直接瞄准命中率这个主导项。拿到数据后，再决定要不要动 `reserve` / `kv-resident` 这类有显存代价的旋钮。

### 评测基建

- 复用现有 `test_mtp_spec_sweep.py` / `test_workers_sweep.py` / `test_pcie_and_kv.py`（已封装 `StrataEngine` 直连，比走 HTTP 稳）。
- 新建固定 **18 题评测集** + `node --check` 语法校验 + 自动打分脚本，保证同题同判。
- 每次实验**只改一个变量**，跑 3 次取中位。

### 风险与回滚

- 所有实验配置派生新文件（如 `strata-coder-iq1_m-exp-*.json`），**绝不覆盖** `strata-coder-iq1_m-ultra.json`。
- 任一实验劣化即删除临时文件，ultra 生产版全程可用。
- 每个阶段结束后按项目规范同步更新 `STRATA_ISSUE_HANDOVER_REPORT.md` 并做中英双语提交。

### 预期收益（保守估计）

1. **速度**：T1（命中率）若能回收 5~8 个点 + T2（PLE）回收 3~5 tok/s，日常中位从 ~66 提到 **72~78**。
2. **稳定性**：T1-2 顺带把 `reserve` 调到既不 OOM 也不浪费的点，消除 22 次 LOW 告警。
3. **智商**：T4-1 若确证失效，修好即**白捡**整个 V4 提示词收益；T4-3 攻语法失败才是真正的质量提升点。

---

## 附：一句话结论

> 现状可用，这是**调优**。速度的主导项是**专家缓存命中率（实测中位 73%，文档以为 85~90%）**，而命中率低的一个直接原因是 **prefill 阶段借走了 2470/3793 个缓存槽**。因此第一步不是动显存旋钮，而是**重建 profile + 关掉 prefill 借槽**——两者零显存代价，直接瞄准主导项。至于智商线：16384 预算在生产中**从未触发**，它不是日常瓶颈，真正该攻的是 18 题里那 5 道仍然产出语法错误代码的任务。

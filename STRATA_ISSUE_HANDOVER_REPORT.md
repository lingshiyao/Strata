# Strata 引擎 x Qwen3.8-Coder-IQ1_M (256K) 全生命周期交接与系统工程档案
# Strata Engine x Qwen3.8-Coder-IQ1_M (256K) Lifecycle Handover & Engineering Knowledge Base

> **【唯一交接文档说明 / Single Source of Truth Notice】**  
> 本文档为 `D:\Strata` 项目**根目录下唯一的交接文档（Single Source of Truth）**，专为接管本工程的后续 AI Agent / 自动化流水线设计。  
> **核心规范（Rule of Project Evolution）**：  
> 1. 任何 AI Agent 对本项目进行任何增删改（包括代码、脚本、配置及本文档自身）时，**必须同步更新本文档**。  
> 2. 每次变更后**必须执行 Git 提交**，且 Git Commit Message **必须使用中英双语混合描述（Bilingual Chinese & English）**。  
> 3. 已固化的基准文件（`run-coder-iq1_m-256k.bat`、`hermes-coder-256k.bat`、`strata-coder-iq1_m-256k.json`）为**基准不可变资产（Immutable Baselines）**，所有后续调优必须派生为新的命名文件。

---

## 1. 系统架构与硬件基准 (System Architecture & Hardware Baseline)

本项目运行于极端混合异构计算架构（Hybrid Heterogeneous Architecture），将超大参数量 MoE 模型与 256K 超长上下文在单张消费级显卡上高效运行：

### 1.1 硬件配置 (Hardware Specifications)
* **GPU**: NVIDIA GeForce RTX 5070 Ti 16GB GDDR7（Dedicated VRAM: 16,384 MiB）
* **CPU**: Intel Core Ultra 7 270K Plus（16 P/E 核心并行线程池）
* **RAM**: 48GB DDR5 高频内存（支持大容量 Pinned Host Memory）
* **Storage**: 高速 NVMe SSD（模型权重与 MTP 存放于 `E:\Strata-data\`）
* **OS / Shell**: Windows 11 / PowerShell 7.5 & CMD

### 1.2 模型与引擎拓扑 (Model & Engine Topology)
* **模型**: `Qwen3.8-Flash-Next Coder IQ1_M`（ISTA-DASLab 剪枝代码专精 MoE，125B 参数，激活 256 专家）
* **权重布局**:
  * Shard 1 (Native Weights): `E:\Strata-data\models\coder-IQ1_M\Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00001-of-00002.gguf`
  * Shard 2 (PLE/N-gram): `E:\Strata-data\models\coder-IQ1_M\Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00002-of-00002.gguf`
  * MTP 投机头: `E:\Strata-data\mtp\rt` (Multi-Token Prediction)
  * Vision 视觉模态: `E:\Strata-data\models\mmproj-Qwen3.8-Flash-Next-BF16.gguf`
* **内存分配（256K 状态）**:
  * 模型基础权重与专家缓存：显存驻留 ~11.9 GB（含 3,629 个 GPU 专家槽位），剩余显存 ~4.1 GB 安全余量。
  * Int8 KV 缓存：256K 全上下文仅需 3.09 GiB Pinned RAM，其中前 32,768 tokens（`--kv-resident 32768`）常驻显存。
  * 主机内存占用：约 26.5 GB / 48 GB，系统可用内存余量超 21.5 GB，杜绝 OOM 崩溃。

---

## 2. 固化基准资产规范 (Solidified Baseline Assets)

项目已彻底移除历史遗留的 64K 与 128K 配置文件，全域固化为 **256K 生产级基准**：

| 文件绝对路径 | 类型 | 职责与关键特性 | 维护要求 |
| :--- | :--- | :--- | :--- |
| `D:\Strata\run-coder-iq1_m-256k.bat` | 服务启动 BAT | 启动本地 Strata OpenAI 兼容服务端点（端口 8080），加载 256K 配置 | **只读基准**，不可篡改 |
| `D:\Strata\hermes-coder-256k.bat` | 智能体连接 BAT | 自动配置 Hermes CLI/Desktop 环境（256K 上下文、压缩阈值 147456、Prune 48000、中等思考、Native Vision），并拉起/热重用 Strata 服务 | **只读基准**，不可篡改 |
| `D:\ninfer\hermes\hermes-strata-coder-256k.bat` | 镜像连接 BAT | 镜像部署于 Hermes 专用目录，与根目录版本保持二进制一致 | **镜像同步** |
| `D:\Strata\strata-coder-iq1_m-256k.json` | 引擎配置 JSON | 固化 256K 上下文、Int8 KV、采样防循环参数与 8192 Thinking Budget | **只读基准**，不可篡改 |
| `D:\Strata\benchmark_256k_full_spectrum.py` | 评测套件 Python | 覆盖 1K 到 216K 全上下文阶梯的流式性能与命中率基准测试脚本 | 标准测试工具 |

> **关键经验（CMD `call` 陷阱）**：在 Windows CMD 批处理文件中调用 `hermes config` 命令时，必须严格使用 `call hermes config ...`。因 `hermes` 在 Windows 下为 `hermes.cmd`，若不加 `call`，批处理执行权将被转移并提前终止后续脚本。

### 2.1 分支治理与原作者更新同步策略 (Branch Governance & Upstream Sync Protocol)

为确保“既能第一时间无缝吸收原作者新功能，又绝不冲垮本地已固化 256K 生产配置”，本项目严格采用“基准-定制解耦”双分支治理拓扑：

* **`main` 分支（原作者纯净收件箱 / Upstream Mirror）**：
  * 保持 100% 官方原汁原味代码，严格对齐 `origin/main`（`https://github.com/Niko1221/Strata.git`）。
  * 任何本地 AI Agent 严禁直接在 `main` 上开发提交。
  * 作用：原作者发布引擎新版本时，随时一键拉取（`git pull`），永远零冲突、零闪退。
* **`my-256k` 分支（本地 256K 生产与调优专属工作间 / Production & Tuning Workspace）**：
  * **当前默认活动分支**。所有的 256K 配置文件、启动批处理、死循环防御参数、调优实验与本文档均在此分支上维护。
* **后续 AI 同步原作者更新的标准协议 (Sync Upstream Protocol)**：
  1. `git fetch origin`（获取原作者最新提交）
  2. `git checkout main && git merge origin/main`（更新本地收件箱至官方最新）
  3. `git checkout my-256k`（切回生产工作间）
  4. `git merge main`（将官方引擎更新合并入 256K 生产环境）
  5. 验证服务启动并更新本文档与 Git 记录。

---

## 3. 死循环根因诊断与双阶段防御体系 (Anti-Looping Architecture & Root Cause)

### 3.1 历史故障现象还原
1. **代码阶段无限复读（Answering Loop）**：在生成前端 HTML/JS 游戏代码时，模型陷入自回归死循环，连续复读汉字“盲”（Unicode `\u76f2`，源自小丑牌游戏术语），单次 Tool Call 输出暴涨至 85,553 tokens，且以 98 tok/s 持续朝 236,400 tokens 消耗。
2. **磁盘无文件**：Hermes 协议要求 Tool Call 必须等到 JSON 闭合引号与花括号后方可解析写盘，因此无限循环导致无任何文件落盘。
3. **思考阶段复读中断（Thinking Dilemma）**：在遇到工作区残存破损文件（如 16 行空 stub 导致 Hermes 报错 `Refusing to overwrite...`）时，模型在 `<think>` 中反复权衡纠结，短语级复读超过 16,000 字符后被 Hermes 客户端 `RunawayStreamWatch` 强行熔断。

### 3.2 根因与机理分析
* **IQ1_M 超低比特量化长尾噪声**：极低比特量化（1.5~1.75 bits/weight）导致特定专有名词的 Logits 分布出现异常尖峰。
* **无界 `max_tokens` 陷阱**：单次请求未限制生成上限，默认吃满剩余全部上下文（236K tokens）。
* **回退窗口覆盖不足**：默认 `penalty_last_n: 64` 只能检测 64 token 内的单字重复，对跨句子、跨段落的百 Token 级语义复读完全失效。

### 3.3 双阶段防御矩阵（已固化生效于 `strata-coder-iq1_m-256k.json`）
```json
  "sampling": {
   "temperature": 0.5,
   "top_p": 0.95,
   "top_k": 40,
   "min_p": 0.08,
   "repetition_penalty": 1.08,
   "penalty_last_n": 512,
   "frequency_penalty": 0.15,
   "presence_penalty": 0.1
  },
  "reasoning_budget_tokens": 8192
```

* **`min_p: 0.08`（第一道噪声防火墙）**：动态剪裁低于当前 Top-1 概率 8% 的长尾候选词，精准过滤 IQ1_M 的底噪突刺。
* **`repetition_penalty: 1.08`（单字/短语物理衰减）**：对近期已生成词汇施加 1.08 倍对数衰减。代码模型严禁超过 1.12，1.08 处于黄金区间，既能阻止死循环，又不破坏编程中合法的重复符号（如 `for(;;)`、`}}`）。
* **`penalty_last_n: 512`（512 Token 全局扫描天网）**：将循环惩罚检测视窗从 64 扩大到 512 tokens，有效覆盖多段落长短语级循环。
* **`reasoning_budget_tokens: 8192`（满血思考预算）**：保留完整的 High-effort 深度思考上限，杜绝浅层思考导致的逻辑崩溃。
* **客户端断开即时熔断（Socket Disconnect Guard）**：在 `serve/server.py` 中引入 `select.select` 与 `MSG_PEEK` 套接字监听，用户在 Hermes 点击 Stop 时，Strata 引擎立即终止生成并释放显卡。

---

## 4. 256K 全上下文阶梯实测性能实证 (256K Full-Spectrum Benchmark Empirical Data)

使用 `benchmark_256k_full_spectrum.py` 在空载干净环境下完成从 1K 到 216K tokens（占总上下文 85%）的实测数据：

| 测试点 (Context Scale) | Prompt 长度 (Tokens) | Prefill 延迟 (TTFT) | 解码生成速度 (Decode Speed) | 总耗时 (Total Time) | GPU 专家缓存命中率 (Cache Hit) | 跨越状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Short (1K)** | 1,099 tokens | **1.37 s** | **44.1 tok/s** | 2.82 s | 68.9% (冷启动爬坡) | 显存完全驻留 |
| **Mid (18K)** | 18,318 tokens | **6.19 s** | **59.5 tok/s** | 7.27 s | 83.6% | 显存完全驻留 |
| **32K Boundary (36K)** | 36,636 tokens | **7.03 s** | **64.0 tok/s** | 8.03 s | 85.1% | 平滑跨入 DDR5 内存 |
| **Heavy (72K)** | 73,272 tokens | **13.41 s** | **64.4 tok/s** | 14.40 s | 84.7% | 混合异构稳定运行 |
| **Ultra (144K)** | 146,544 tokens | **28.16 s** | **71.3 tok/s** (峰值) | 29.06 s | 85.3% | MTP 投机加速最佳匹配 |
| **Near-Full (216K)** | 219,816 tokens | **33.94 s** | **51.1 tok/s** | 35.19 s | 85.7% | **无断崖式跌落** |

### 核心结论 (Empirical Insights)
1. **真实可用性确证**：在高达 21.9 万 token（满载 85%）的极端负载下，解码速度依旧保持在 **51.1 tok/s**，未出现任何因超长上下文导致的显存溢出、OOM、崩溃或速度断崖式下跌。
2. **跨越 32K 边界零损耗**：从 18K（显存内）跨越至 36K（溢出至 DDR5 Pinned RAM）时，解码速度反而从 59.5 升至 64.0 tok/s，证明 Strata 的异步 PCIe 流水线极度高效。
3. **MTP 投机在深层上下文依旧有效**：在 144K 超长上下文下达到 71.3 tok/s 的解码峰值，专家缓存命中率稳定在 85% 以上。

---

## 5. 五大调优方向技术蓝图 (The 5-Direction Tuning Roadmap)

在保持基准脚本 `run-coder-iq1_m-256k.bat` 不变的前提下，后续实验将探索更高解码速度与更优延迟：

### 方向一：显存专家缓存极致压榨 (VRAM Expert Cache Expansion)
* **核心机理**：当前 `--vram-reserve-mib 700` 分配了 3,629 个 GPU 专家槽位。显存尚有 4.1 GB 闲置，可尝试降低预留至 `300 MiB`，使 GPU 专家槽位扩充至 4,500~5,000 个。
* **预期目标**：将专家缓存命中率从 85% 提升至 92%+，减少 PCIe 和 DDR5 的搬运瓶颈。

### 方向二：MTP 多 Token 投机窗口拓宽 (MTP Speculative Window Expansion)
* **核心机理**：当前 `--spec 4`、`--spec-min-p 0.50`。在代码高重复度场景下，探索 `--spec 5` 或 `--spec 6`，并微调 `--spec-min-p 0.45`。
* **预期目标**：提高每个 step 接受的投机 token 数量，冲刺 80+ tok/s 解码速度。

### 方向三：显存驻留 KV 视窗扩大 (KV-Resident Window Expansion)
* **核心机理**：当前 `--kv-resident 32768`（仅前 32K tokens KV 驻留显存）。可测试 `--kv-resident 49152` 或 `65536`。
* **预期目标**：使 64K 以内的日常编码任务实现 100% 显存 KV 读取，降低 DDR5 内存延迟。

### 方向四：CPU 线程池与核心亲和性配平 (CPU Worker Pool Optimization)
* **核心机理**：当前 `--pool-workers 15`。Intel Core Ultra 7 270K Plus 具有高性能 P 核心与能效 E 核心，针对 14、16、18 线程池规模进行性能梯度扫描。
* **预期目标**：找到 CPU 处理 host expert offload 的最低调度开销点。

### 方向五：PCIe 流水线并发计算 (PCIe Streaming Compute)
* **核心机理**：当前 `--pcie-frac 0.00`。尝试开启微流并发（如 `--pcie-frac 0.10`），使 GPU 计算与 PCIe 数据传输重叠进行。
* **预期目标**：隐藏专家未命中时的 PCIe 传输时延。

---

## 6. 变更审计与版本日志 (Change Audit & Version Log)

| 日期 / 提交 | 模块 | 变更类型 | 描述 (Bilingual Summary) |
| :--- | :--- | :--- | :--- |
| 2026-10-02 | Root / Architecture | Consolidation & Baseline | 彻底下线删除 64K/128K 遗留文件，固化 256K 生产级基线（`run-coder-iq1_m-256k.bat`, `hermes-coder-256k.bat`, `strata-coder-iq1_m-256k.json`）。<br>*Deprecate 64K/128K configurations, consolidate and solidify 256K production baseline.* |
| 2026-10-02 | Sampling Defense | Bugfix & Hardening | 在 `strata-coder-iq1_m-256k.json` 中注入双阶段防死循环矩阵（`min_p: 0.08`, `repetition_penalty: 1.08`, `penalty_last_n: 512`, `budget: 8192`）。<br>*Inject two-phase anti-looping sampling defenses into 256K config to eliminate repetition attractors.* |
| 2026-10-02 | Engine / Server | Feature & Resilience | `serve/server.py` 增加客户端断开连接检测（`select` + `MSG_PEEK`），避免客户端点击 Stop 后服务端持续空转。<br>*Add socket disconnect detection in server.py for immediate inference cancellation.* |
| 2026-10-02 | Benchmark | Empirical Verification | 编写并执行 `benchmark_256k_full_spectrum.py`，完成 1K 至 216K 全阶梯性能测试，确证 256K 稳定性与无断崖衰减。<br>*Create and execute 256K full-spectrum benchmark, verifying 51.1~71.3 tok/s performance across context range.* |
| 2026-10-02 | Git / Handover | Governance | 更新 `.gitignore` 确保固化脚本纳入版本控制，重构建立唯一的 AI 全景交接文档。<br>*Update .gitignore to track coder configs and establish the unified root handover report.* |
| 2026-10-02 | Branch Topology | Governance | 建立 `my-256k` 专属工作分支与纯净官方 `main` 镜像，制定无缝吸收原作者更新的标准协议。<br>*Establish `my-256k` production branch and clean upstream `main` mirror with seamless sync protocol.* |


# tools/t1_probe — 专家缓存命中率线（T1）取证与判决工具

本目录是 **T1 判决**的可复现证据。判决结论与完整数据表见
`docs/T1_VERDICT_2026-10-04.md`；交接档案见 `STRATA_ISSUE_HANDOVER_REPORT.md` §11。

**判决：T1（重排专家缓存 profile）取消。** 原因是引擎的专家缓存带一个**自适应层**
（`src/program/generate.cpp`，搜 `Plan v0.3 P6: the VRAM tier follows the conversation`），
它已经拿到了这份收益——换最优排名在真实请求长度上只多约 3pt 命中率。

## 结论速览（N = 3629 槽位，引擎严格口径）

| 方案 | 命中率 |
| :--- | ---: |
| v1 静态（原方案看到的数字） | 51.10% |
| **v1 + 自适应（真实运行时）** | **75.59%** |
| oracle 静态（完美排名） | 75.43% |
| **oracle + 自适应（换 profile 的上限）** | **76.30%** |
| 随机排名 + 自适应 | 73.54% |
| 不给 profile + 自适应 | 75.94% |

会话长度扫描：385 位置（生产典型）时 oracle 仅比 v1 高 **+2.95pt**；2046 位置 **+1.09pt**。
模拟器的自适应交换次数 **15,014 vs 引擎实测 15,204（误差 1.3%）**。

## 脚本

| 脚本 | 作用 |
| :--- | :--- |
| `analyze_trace.py` | 阶段 1-B：静态命中率、hit(N) 曲线、前后半段泛化、K 折分块、集中度 |
| `sim_adaptive.py` | 阶段 1-C（**核心**）：离线复刻自适应层，多臂对照 + 会话长度扫描 + 频率敏感性 |

> **2026-10-05 精简**：本目录原有 8 个文件，其中 5 个脚本各自只回答一个一次性问题、
> 结论已完整固化在 `docs/T1_VERDICT_2026-10-04.md`，故予删除，不再随仓库维护。
> 保留下来的两个脚本 + 本 README 是**可复用方法**（离线自适应层模拟器 + trace 分析器 + 踩坑记录）。
>
> | 已删脚本 | 它回答的问题 | 结论落在 |
> | :--- | :--- | :--- |
> | `profile_provenance.py` | coder profile 与出厂 profile 的结构差异 | `T1_VERDICT` §5.2 |
> | `profile_reindex_test.py` | 「coder = 出厂排名重新索引」的 4 组假设检验 | `T1_VERDICT` §5.2 |
> | `profile_subseq_test.py` | 决定性判据：保序子序列 / Kendall tau / top-N 重合度 | `T1_VERDICT` §5.2 |
> | `build_prompt.py` | 把 benchmark prompt 拼成分词串（trace 的输入） | 产物留在本地，见下节 |
> | `sections.py` | 各任务段的 token 边界（leave-one-task-out 用） | 产物留在本地，见下节 |

运行方式（需 `regex`，用项目 venv）：

```bash
.venv/Scripts/python.exe tools/t1_probe/analyze_trace.py
.venv/Scripts/python.exe tools/t1_probe/sim_adaptive.py
```

## 数据文件不在此目录

两个路由 trace 二进制（`trace_decode.bin` 8.6 MB、`trace_prompt.bin` 0.67 MB）体积过大，
**未纳入版本控制**，留在本地工作区 `.workbuddy-ai/t1_probe/`（该目录已在 `.gitignore` 中）。
脚本按绝对路径读取那里，因此直接运行即可。

## 重新生成 trace

`trace_prompt.bin` 是**废弃产物**（`--prefill-until` 的陷阱，上下文退化为单 token），
只有 `trace_decode.bin` 是有效数据。重新生成：

```bash
# 1) 分词 —— 直接复用本地已生成的 token 文件，无需重新分词
#    原分词脚本 build_prompt.py 已删除（见上节）。分词是确定性的，
#    该文件内容不会变：2683 个 token id，逗号分隔。
ls -l .workbuddy-ai/t1_probe/prompt_tokens.txt

# 2) 采集（native IQ pack 的必需参数：--native/--spec/--prefill；--dump-routing 不可与 --no-pool 同用）
export PATH="/d/Strata/.venv/Lib/site-packages/nvidia/cu13/bin/x86_64:$PATH"
./engine/strata.exe \
  --pack E:/Strata-data/packs/coder-iq1_m \
  --native  E:/Strata-data/models/coder-IQ1_M/Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00001-of-00002.gguf \
  --ple-gguf E:/Strata-data/models/coder-IQ1_M/Qwen3.8-Flash-Next-GSQ-RCO-IQ1_M-00002-of-00002.gguf \
  --expert-profile D:/Strata/data/expert-profile-coder.bin \
  --expert-cache auto --prefill auto --spec 4 --mtp E:/Strata-data/mtp/rt --spec-min-p 0.50 \
  --max-context 262144 --kv int8 --kv-resident 32768 --vram-reserve-mib 700 --pool-workers 15 \
  --tokens-file D:/Strata/.workbuddy-ai/t1_probe/prompt_tokens.txt \
  --max-new 1600 --greedy \
  --dump-routing D:/Strata/.workbuddy-ai/t1_probe/trace_decode.bin
```

## 三个必须记住的坑

1. **缓存不是静态的。** 只算静态命中率会严重低估运行时表现（实测 51% vs 75%）。
   自适应层的参数：每 4 轮触发、候选衰减使用率 ≥ 2.0、增益阈值 1.5、每次上限 96 个、
   每轮 `usage *= 0.7`。`--adapt-every` / `--adapt-swaps` 两个开关**未写入 `usage()`**，属未文档化。
2. **命中率统计口径。** 引擎报表的分子**只有** `cache_hits`，`cache_admitted`（首次使用即入住）
   **只进分母不进分子**（`generate.cpp:5221-5222`）。模拟冷启动/无 profile 臂时必须按此口径实现。
3. **`--prefill-until` 是陷阱。** native IQ pack 下截断批量 prefill 后，投机循环
   （`generate.cpp` 中 `if (native_pack) { spec_pos = pos; break; }`）**不消费剩余 prompt**，
   模型会从「单 token 上下文」开始生成。该开关不可用于「把 prompt 送进被插桩的路径」。

另：`--dump-routing` 只覆盖**生成位置**——prompt 走批量 prefill（`src/prefill/` 不写 routing），
所以 trace 的规模由 `--max-new` 决定，与 prompt 长度无关。

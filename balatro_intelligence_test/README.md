# 《Balatro (小丑牌) 智能体高压编码能力评测工程库》
# Balatro Intelligence & Coding Benchmark Suite

> **工程定位**：专门为测试评估大模型（Qwen3.8-Coder x Hermès）高阶编码智力、复杂数学连锁逻辑、模块化工程架构与 UI 还原能力打造的**端到端全真复刻评测套件**。  
> **设计角色**：产品总监 (Product Director) & 设计总监 (Design Director)  
> **受试智能体**：Hermès Desktop (运行本地 Strata Qwen3.8 Coder 256K Ultra)

---

## 1. 评测工程资产全景 (Benchmark Assets)

```
D:\Strata\balatro_intelligence_test\
├── README.md                              # 本工程总览与导航
├── 01_BALATRO_GDD_PRD.md                  # 生产级游戏设计与产品需求规范书 (规则/公式/Joker库)
├── 02_ARCHITECTURE_AND_MODULAR_PLAN.md    # 模块化前端架构设计 (杜绝单文件面条代码)
├── 03_HERMES_TASK_PACKET.md               # 分发给 Hermès 的一键执行主提示词与验收标准
└── ui_mockups/                            # 4 张 16:9 高保真复古像素 UI 图纸
    ├── 01_combat_play_screen.jpg          # 1. 核心战斗出牌界面 (Joker槽/手牌/记分板/按钮)
    ├── 02_shop_screen.jpg                 # 2. 商店阶段交易界面 (货架/卡包/兑换券/重置)
    ├── 03_blind_selection_screen.jpg      # 3. 盲注选择界面 (Small/Big/Boss Blind/Debuff)
    └── 04_game_over_run_summary.jpg       # 4. 游戏结算通关界面 (战绩/胜场/最终阵容)
```

---

## 2. UI 视觉图纸索引 (Visual Design Gallery)

| 图纸编号 | 界面名称 | 核心设计要素 | 本地文件链接 |
| :---: | :--- | :--- | :--- |
| **01** | **核心出牌对局 (Combat)** | 5 个顶部 Joker 槽、右侧 2 个消耗槽、左侧霓虹记分板、8 张升降手牌、出牌与弃牌按钮 | [01_combat_play_screen.jpg](file:///D:/Strata/balatro_intelligence_test/ui_mockups/01_combat_play_screen.jpg) |
| **02** | **商店交易界面 (Shop)** | Ante 顶部横幅、2 槽待售 Joker、星球卡、标准补充包、兑换券、Reroll 递增按钮 | [02_shop_screen.jpg](file:///D:/Strata/balatro_intelligence_test/ui_mockups/02_shop_screen.jpg) |
| **03** | **盲注选择界面 (Blind)** | Small / Big / Boss Blind 三卡鼎立、跳过 Tag 奖励、Boss 特殊恶性 Debuff 标签 | [03_blind_selection_screen.jpg](file:///D:/Strata/balatro_intelligence_test/ui_mockups/03_blind_selection_screen.jpg) |
| **04** | **胜利战绩结算 (Summary)**| 通关 Ante 8 胜利牌匾、数据复盘、最终 5 张制胜 Joker 阵容光环展示、再来一局按钮 | [04_game_over_run_summary.jpg](file:///D:/Strata/balatro_intelligence_test/ui_mockups/04_game_over_run_summary.jpg) |

---

## 3. 测试如何启动与分发？(Quick Start)

1. 打开 **Hermès Desktop**。
2. 打开 [`03_HERMES_TASK_PACKET.md`](file:///D:/Strata/balatro_intelligence_test/03_HERMES_TASK_PACKET.md)，直接复制其中的 **【一键分发给 Hermès 的主提示词 (Master Prompt)】**。
3. 粘贴发送给 Hermès。
4. Hermès 将会自动：
   - 阅读 GDD 规则文档；
   - 依据模块化架构在 `balatro_game/` 逐步创建模块文件；
   - 依据 UI 图纸还原复古像素视觉效果；
   - 编写并运行自动化逻辑单测。

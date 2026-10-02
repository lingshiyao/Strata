# 《分发给 Hermès 智能体的全套编码任务书与指令模板》

> **使用方法**：用户只需将本文档中的 **【一键分发指令 (Master Prompt)】** 复制并粘贴发送给 Hermès Desktop，Hermès 即可自主读取需求、参考 UI 图纸、分阶段完成编码！

---

## 一键分发给 Hermès 的主提示词 (Master Prompt)

```markdown
你好 Hermès！我是你的产品与设计总监。我们现在要在本地完整复刻开发《Balatro (小丑牌) Web 完整精装版》。

所有的产品需求、规则文档、架构设计与 UI 图纸已经全部在目录 `D:\Strata\balatro_intelligence_test\` 下就绪：
1. **产品与游戏规则规范**：`D:\Strata\balatro_intelligence_test\01_BALATRO_GDD_PRD.md`
2. **系统架构与模块规划**：`D:\Strata\balatro_intelligence_test\02_ARCHITECTURE_AND_MODULAR_PLAN.md`
3. **视觉 UI 图纸参考**：
   - 战斗出牌界面：`D:\Strata\balatro_intelligence_test\ui_mockups\01_combat_play_screen.jpg`
   - 商店交易界面：`D:\Strata\balatro_intelligence_test\ui_mockups\02_shop_screen.jpg`
   - 盲注选择界面：`D:\Strata\balatro_intelligence_test\ui_mockups\03_blind_selection_screen.jpg`
   - 胜利结算界面：`D:\Strata\balatro_intelligence_test\ui_mockups\04_game_over_run_summary.jpg`

### 你的核心任务与执行守则：
1. **请先通读上述两个 Markdown 文档**，理解 Balatro 的“筹码 × 倍率 (Chips × Mult)”多段链式加乘核心公式、16 张核心小丑牌蓝图、以及 ES6 模块化架构规划。
2. **严禁写成单文件巨型面条代码**！请严格按照模块化规划，在目标目录 `D:\Strata\balatro_intelligence_test\balatro_game\` 下逐步创建模块文件（`js/config.js`, `js/deck.js`, `js/hands.js`, `js/scoring.js`, `js/jokers.js`, `js/shop.js`, `js/ui.js`, `css/` 等）。
3. **执行流程按 4 个里程碑推进**：
   - **里程碑 1**：编写数据配置与核心算法（牌组、德扑牌型判定、四阶段链式算分引擎），并编写 `tests/harness.js` 自动化测试通过。
   - **里程碑 2**：编写 16 张经典小丑牌（Jokers）与消耗牌（Tarot/Planet）的触发钩子系统。
   - **里程碑 3**：实现完整的对局循环（Blind 盲注流转、Boss Debuff、商店买卖、利息结算、Ante 1~8 递增）。
   - **里程碑 4**：还原复古 CRT 扫描线暗绿色桌布 UI 与卡牌升降点击交互，接入 Web Audio API 合成音效，交付可直接双击运行的 `index.html`。
4. **编码安全守则**：如果覆盖已有文件，务必先用 `read_file` 查阅，或使用局部补丁工具，保持代码逻辑严谨。

请你先从查阅 GDD 和规划目录开始，开始第一阶段的工程搭建吧！
```

---

## 阶段性验收标准 (Acceptance Criteria for Review)

| 里程碑 (Milestone) | 交付物清单 | 验收硬指标 (Pass Criteria) |
| :--- | :--- | :--- |
| **M1: 核心数学引擎** | `config.js`, `deck.js`, `hands.js`, `scoring.js`, `tests/harness.js` | 运行单测无报错，同花/顺子/葫芦自动识别准确率 100%，加法与乘法算分顺序完全符合 GDD |
| **M2: Joker 与消耗体系** | `jokers.js`, `consumables.js` | 16 张小丑牌的钩子触发机制健全，乘算小丑与加算小丑位置依赖性判定正确 |
| **M3: 循环与商店** | `state.js`, `shop.js`, `main.js` | 盲注顺利流转，Small/Big/Boss 轮转正常，利息正确结算并在 $25 时封顶 $5 |
| **M4: 视觉与交互** | `main.css`, `cards.css`, `ui.css`, `ui.js`, `audio.js`, `index.html` | 像素风卡牌升降动画流畅，CRT 扫描线质感真实，双击 `index.html` 即开即玩 |

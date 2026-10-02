# Balatro Coding & Autonomous Intelligence Benchmark Suite

> **Project Mission**: A production-grade, end-to-end game reproduction benchmark designed specifically to evaluate high-order coding intelligence, complex combinatorial mathematical logic, modular software architecture, and UI fidelity in local large models (`Qwen3.8-Flash-Next Coder` running via Strata Engine).  
> **Role Persona**: Product Director & Lead Systems Architect  
> **Target Agent**: Hermes Desktop / OpenCode (powered by Strata 256K Ultra)

---

## 1. Benchmark Asset Directory Topology

```
D:\Strata\balatro_intelligence_test\
├── README.md                              # Benchmark suite overview and execution guide
├── 01_BALATRO_GDD_PRD.md                  # Comprehensive Game Design Document & PRD (rules, formulas, Jokers)
├── 02_ARCHITECTURE_AND_MODULAR_PLAN.md    # Production modular architecture plan (anti-spaghetti specification)
├── 03_HERMES_TASK_PACKET.md               # Ready-to-send Master Prompt & acceptance criteria matrix
└── ui_mockups/                            # 4x High-fidelity 16:9 retro CRT visual mockups
    ├── 01_combat_play_screen.jpg          # 1. Core combat & play screen (Joker slots, hand, neon scoreboard)
    ├── 02_shop_screen.jpg                 # 2. Shop phase (items, boosters, vouchers, reroll button)
    ├── 03_blind_selection_screen.jpg      # 3. Blind selection screen (Small, Big, Boss blinds & debuffs)
    └── 04_game_over_run_summary.jpg       # 4. Victory & run summary screen (Ante 8 win, stats, Joker lineup)
```

---

## 2. Visual Design Reference Gallery

| ID | Screen Name | Key UI Elements | File Link |
| :---: | :--- | :--- | :--- |
| **01** | **Core Play & Combat** | 5 Joker slots, 2 consumable slots, left-side neon scoreboard, 8 elevated playing cards, play/discard actions | [01_combat_play_screen.jpg](file:///D:/Strata/balatro_intelligence_test/ui_mockups/01_combat_play_screen.jpg) |
| **02** | **Shop & Economy** | Ante header banner, 2 for-sale Joker slots, Planet/Tarot card, standard booster pack, voucher, reroll button | [02_shop_screen.jpg](file:///D:/Strata/balatro_intelligence_test/ui_mockups/02_shop_screen.jpg) |
| **03** | **Blind Selection** | Small, Big, and Boss Blind cards, skip tag rewards, Boss debuff badge and condition warnings | [03_blind_selection_screen.jpg](file:///D:/Strata/balatro_intelligence_test/ui_mockups/03_blind_selection_screen.jpg) |
| **04** | **Victory & Summary** | Ante 8 victory placard, detailed run statistics, glowing final 5-Joker lineup showcase, Play Again CTA | [04_game_over_run_summary.jpg](file:///D:/Strata/balatro_intelligence_test/ui_mockups/04_game_over_run_summary.jpg) |

---

## 3. How to Launch the Benchmark Test

1. Ensure the Strata engine is running on `http://127.0.0.1:8080/` with the latest `strata-coder-iq1_m-ultra.json` configuration (`reasoning_budget_tokens: 1024`).
2. Open **Hermes Desktop** (or OpenCode).
3. Open [`03_HERMES_TASK_PACKET.md`](file:///D:/Strata/balatro_intelligence_test/03_HERMES_TASK_PACKET.md) and copy the **[Turnkey Master Prompt]**.
4. Send the prompt to Hermes.
5. The agent will autonomously:
   - Ingest `01_BALATRO_GDD_PRD.md` and `02_ARCHITECTURE_AND_MODULAR_PLAN.md` in pure English.
   - Incrementally create the modular codebase in `balatro_game/`.
   - Implement the 4-phase scoring chain and verify logic via `tests/harness.js`.
   - Build the retro CRT visual presentation and audio synthesis.

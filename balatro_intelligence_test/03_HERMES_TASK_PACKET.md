# Hermes Agent Task Packet & Execution Directives

> **Usage Guide**: Copy and paste the **[Turnkey Master Prompt]** below directly into Hermes Desktop (or OpenCode). Hermes will autonomously inspect the specifications, consult the UI mockups, and execute the 4-milestone modular implementation.

---

## Turnkey Master Prompt for Hermes

```markdown
Hello Hermes! You are the Lead Systems Architect and Senior Gameplay Engineer for our project: building a complete, production-grade web replica of Balatro ("Balatro Web Edition").

All game design specifications, mathematical models, modular architecture plans, and visual UI mockups are ready in `D:\Strata\balatro_intelligence_test\`:
1. **Game Design Document & PRD**: `D:\Strata\balatro_intelligence_test\01_BALATRO_GDD_PRD.md`
2. **System Architecture & Modular Plan**: `D:\Strata\balatro_intelligence_test\02_ARCHITECTURE_AND_MODULAR_PLAN.md`
3. **Visual UI Reference Mockups**:
   - Combat / Play Screen: `D:\Strata\balatro_intelligence_test\ui_mockups\01_combat_play_screen.jpg`
   - Shop Phase Screen: `D:\Strata\balatro_intelligence_test\ui_mockups\02_shop_screen.jpg`
   - Blind Selection Screen: `D:\Strata\balatro_intelligence_test\ui_mockups\03_blind_selection_screen.jpg`
   - Run Summary / Victory Screen: `D:\Strata\balatro_intelligence_test\ui_mockups\04_game_over_run_summary.jpg`

### Core Directives & Execution Protocol:
1. **Thoroughly Study the Specification Documents**: First inspect `01_BALATRO_GDD_PRD.md` and `02_ARCHITECTURE_AND_MODULAR_PLAN.md`. Master the 4-stage scoring pipeline (`Chips × Mult`), the exact poker hand hierarchy, the 16 core Joker blueprints, and the strict ES6 modular architecture.
2. **Strictly Prohibit Monolithic Code**: Do NOT generate a single massive spaghetti file. You must strictly follow the modular plan and build the codebase under `D:\Strata\balatro_intelligence_test\balatro_game\` with separate modules (`js/config.js`, `js/deck.js`, `js/hands.js`, `js/scoring.js`, `js/jokers.js`, `js/consumables.js`, `js/state.js`, `js/shop.js`, `js/ui.js`, `js/audio.js`, `js/main.js`, `css/main.css`, `css/cards.css`, `css/ui.css`, `index.html`, and `tests/harness.js`).
3. **Execute in 4 Clear Milestones**:
   - **Milestone 1 (Core Math & Evaluation Engine)**: Implement card data structures, standard 52-card deck with Fisher-Yates shuffle, poker hand evaluator (Flush Five down to High Card), and the 4-stage scoring pipeline. Build `tests/harness.js` and verify that all unit test assertions pass.
   - **Milestone 2 (Jokers & Consumables System)**: Implement the 16 core Jokers with event hook triggers (`onCardScored`, `onHandPlayed`, `onDiscard`, `calculateMult`, etc.) and consumable cards (Tarot/Planet). Validate additive vs. multiplicative Joker positioning dependencies.
   - **Milestone 3 (Game Loop & Economy)**: Implement round flow (Small / Big / Boss Blinds), Boss debuff logic, shop generation (reroll mechanics, vouchers, booster packs), and interest calculation (1$ per 5$ capped at 5$ max at 25$).
   - **Milestone 4 (Visual Presentation & Polish)**: Build the CRT scanline aesthetic, felt-green tabletop canvas, pixel-art card elevation/click interactions, and procedural sound synthesis using the Web Audio API. Deliver a standalone, zero-dependency `index.html`.
4. **Code Quality & Reliability**: Whenever modifying or referencing existing code, read the file first. Ensure clean, defensive JavaScript with comprehensive error handling.

Begin now by reviewing the GDD and architecture documents, then start Milestone 1 implementation in `D:\Strata\balatro_intelligence_test\balatro_game\`.
```

---

## Acceptance Criteria & Milestone Review Matrix

| Milestone | Deliverables | Hard Acceptance Criteria |
| :--- | :--- | :--- |
| **M1: Core Mathematical Engine** | `config.js`, `deck.js`, `hands.js`, `scoring.js`, `tests/harness.js` | 100% pass on automated test harness; correct poker hand identification; strict execution of the 4-stage `(Base + Cards) × (Base + AddJokers) × MultJokers` pipeline. |
| **M2: Joker & Consumable Triggers** | `jokers.js`, `consumables.js` | 16 core Jokers with active event hooks; left-to-right trigger order; correct calculation of `+Mult` before `×Mult`. |
| **M3: Game Loop & Economy** | `state.js`, `shop.js`, `main.js` | Smooth transition across Small, Big, and Boss Blinds; Ante 1–8 scaling; Boss debuffs functional; interest capped at $5 at $25. |
| **M4: Visual Polish & Sound** | `main.css`, `cards.css`, `ui.css`, `ui.js`, `audio.js`, `index.html` | High-fidelity retro CRT scanlines and felt green table; smooth card hover/selection physics; Web Audio procedural SFX; double-click `index.html` runs out-of-the-box. |

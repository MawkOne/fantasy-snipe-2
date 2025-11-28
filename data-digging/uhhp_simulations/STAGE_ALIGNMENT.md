# Stage Structure - Aligned to League Rules

## 📋 League Rules Draft Day Process

From `league_rules.draft_day`:

1. **Buyouts** - Teams buy out existing contracts (real cash cost)
2. **Entry Draft** - 1 round, rookies from NHL Entry Draft (3 year deals)
3. **Superstar Round** - 1 round, nominate any UFA/RFA (3 year deals)
4. **UFA Nominations** - 2 rounds, nominate UFAs (3 year deals)
5. **RFA Poaching** - Unlimited rounds, poach RFAs with matching rights (3 year deals)
6. **Commissioner Processing** - Cap compliance, IR moves, cleanup
7. **Free Agent Auction Online** - Daily waivers pre-season (1 year deals)

---

## ✅ New JSON Stage Structure

### Stage 1: Entry Draft (Rookies)
- **League Rule**: Entry Draft
- **Description**: 1 round draft of players from current year's NHL Entry Draft
- **Contract Term**: 3 years
- **Decision Maker**: GM
- **Data Available**: No entry draft data captured in current sources
- **Actions**: 0 (would be populated if we had rookie draft data)

### Stage 2: Free Agent Auction
- **League Rules**: Superstar Round (1) + UFA Nominations (2) + RFA Poaching (unlimited)
- **Description**: Offline auction combining all FA auction rounds
- **Contract Term**: 3 years
- **Decision Maker**: GM
- **Data Available**: Auction CSV files with all winning bids
- **Actions**: Auction picks (e.g., 8 players for New Oilers Nation in 2025-2026)

### Stage 3: Commissioner Processing
- **League Rule**: Post-draft cleanup
- **Description**: Commissioner processes drops for cap compliance, IR moves, and post-draft cleanup
- **Decision Maker**: Commissioner
- **Data Available**: Transaction logs with drops, activations, IR moves
- **Actions**: Forced drops, IR activations (e.g., 25 actions for New Oilers Nation)
- **Note**: Clearly marked with `decision_maker: "commissioner"` and `reason: "cap_compliance"`

### Stage 4: Free Agent Auction Online
- **League Rule**: Free Agent Auction Online (daily waivers)
- **Description**: Daily waivers for pre-season free agent signings
- **Contract Term**: 1 year only
- **Decision Maker**: GM
- **Data Available**: Transaction logs with pre-season signings
- **Actions**: Pre-season waiver pickups (e.g., 9 signings for New Oilers Nation)
- **Note**: Marked with `note: "Pre-season waiver signing (1 year deal)"`

### Stage 5: Regular Season
- **League Rule**: 22 weeks + playoffs, weekly FA auctions
- **Description**: Head-to-head matchups with ongoing waiver activity
- **Contract Term**: 1 year for FA pickups
- **Decision Maker**: Mixed (GMs make moves, commissioners enforce rules)
- **Data Available**: Weekly results, in-season transactions
- **Actions**: Weekly results, waiver pickups, qualified injury drops

---

## 🎯 Key Differences from Original Structure

### Before:
```
1. Draft Day (combined everything)
2. Commissioner Processing
3. Waiver Period
4. Regular Season
```

### After:
```
1. Entry Draft (Rookies) - 3 year deals
2. Free Agent Auction - 3 year deals (Superstar + UFA + RFA)
3. Commissioner Processing - Forced maintenance
4. Free Agent Auction Online - 1 year deals (Pre-season)
5. Regular Season - 1 year deals (In-season)
```

---

## 💡 Why This Matters for AI

1. **Contract Terms Are Clear**: 
   - Stages 1-2: 3 year contracts
   - Stages 4-5: 1 year contracts

2. **Decision Attribution**:
   - Stages 1-2: GM decisions (draft/auction)
   - Stage 3: Commissioner maintenance
   - Stages 4-5: Mixed (GM pickups + commissioner drops)

3. **Strategic Context**:
   - AI can distinguish long-term investments (3yr) from short-term fills (1yr)
   - AI can separate GM strategy from forced compliance
   - AI can track different phases of team building

---

## 📊 2025-2026 Example (New Oilers Nation)

| Stage | Actions | Key Stats |
|-------|---------|-----------|
| Entry Draft | 0 | No data available |
| Free Agent Auction | 8 | $44 spent on 3-year contracts |
| Commissioner Processing | 25 | 24 forced drops, 0 GM decisions |
| FA Auction Online | 9 | 9 pre-season pickups (1-year) |
| Regular Season | 31 | 1-3 record, 2 waiver pickups |

---

## ✅ Alignment Complete

The JSON structure now accurately reflects:
- ✅ All 5 stages of the league process
- ✅ Contract term distinctions (3yr vs 1yr)
- ✅ Decision maker attribution (GM vs Commissioner)
- ✅ Strategic context for each phase
- ✅ Timeline preserved within each stage


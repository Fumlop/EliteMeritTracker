# Elite Dangerous Journal Data - Comprehensive Analysis

This document analyzes available data in Elite Dangerous journal files that could be useful for the EliteMeritTracker plugin (a PowerPlay-focused plugin).

**Journal File Analyzed**: `Journal.2025-12-19T223328.01.log`

---

## Currently Used Events

### FSDJump / Location Events
**Status**: ✅ **IMPLEMENTED**

**Available Data**:
```json
{
  "event": "FSDJump",
  "StarSystem": "Antliae Sector EG-Y d95",
  "SystemAddress": 3274686073195,
  "SystemAllegiance": "Federation",
  "SystemEconomy_Localised": "Extraction",
  "SystemSecondEconomy_Localised": "Industrial",
  "SystemGovernment_Localised": "Democracy",
  "SystemSecurity_Localised": "Low Security",
  "Population": 4091441,

  // PowerPlay Data
  "ControllingPower": "Felicia Winters",
  "Powers": ["Felicia Winters", "Zemina Torval"],
  "PowerplayState": "Stronghold",
  "PowerplayStateControlProgress": 0.891294,
  "PowerplayStateReinforcement": 47544,
  "PowerplayStateUndermining": 156250,

  // PowerPlay Conflict (for Unoccupied systems)
  "PowerplayConflictProgress": [
    {"Power": "Felicia Winters", "ConflictProgress": 0.014750},
    {"Power": "Zemina Torval", "ConflictProgress": 0.000000}
  ],

  // Faction Data
  "Factions": [
    {
      "Name": "Revolutionary HIP 47947 Liberals",
      "FactionState": "Boom",
      "Government": "Democracy",
      "Influence": 0.720000,
      "Allegiance": "Federation",
      "Happiness_Localised": "Happy",
      "MyReputation": 100.000000,
      "ActiveStates": [{"State": "Boom"}],
      "RecoveringStates": [{"State": "PirateAttack"}]
    }
  ],
  "SystemFaction": {
    "Name": "Revolutionary HIP 47947 Liberals",
    "FactionState": "Boom"
  }
}
```

**What We Extract**:
- ✅ System name, PowerPlay state
- ✅ Controlling power, Powers present
- ✅ PowerPlay progress (Reinforcement/Undermining)
- ✅ Conflict progress (for Unoccupied systems)
- ✅ Economy types (Primary/Secondary)
- ✅ Security level
- ❌ Population, Allegiance, Government (available but not used)
- ❌ Faction data (available but not used)

---

## Potentially Useful Events for PowerPlay

### 1. Population Data
**Status**: 🟡 **AVAILABLE BUT NOT USED**

**Use Case**: Show system population in UI for context
- High population systems = More valuable for PowerPlay
- Could help prioritize which systems to fortify/undermine

**FSDJump Data**: `"Population": 4091441`

**Implementation Idea**:
```
Row 6: Refinery / Tourism - Security: Low - Pop: 4.1M
```

---

### 2. System Government & Allegiance
**Status**: 🟡 **AVAILABLE BUT NOT USED**

**Use Case**: Quick reference for system alignment
- Shows if system is Federation/Empire/Alliance/Independent
- Government type might affect PowerPlay bonuses

**FSDJump Data**:
```json
"SystemAllegiance": "Federation",
"SystemGovernment_Localised": "Democracy"
```

**Implementation Idea**:
```
Row 7: Federation (Democracy) - Pop: 4.1M
```

---

### 3. Dominant Faction State
**Status**: 🟡 **AVAILABLE BUT NOT USED**

**Use Case**: Track faction states that affect PowerPlay
- Boom state = Better trade opportunities
- War/Civil War = Undermining opportunities
- Could affect merit gain efficiency

**FSDJump Data**:
```json
"SystemFaction": {
  "Name": "Revolutionary HIP 47947 Liberals",
  "FactionState": "Boom"
}
```

**Implementation Idea**:
```
Row 8: Faction: Revolutionary HIP 47947 Liberals (Boom)
```

---

### 4. Faction Influence Breakdown
**Status**: 🟡 **AVAILABLE BUT NOT USED**

**Use Case**: Advanced PowerPlay tracking
- Shows which factions control the system
- Track influence changes over time
- Could help predict system state changes

**FSDJump Data** (full faction list available):
```json
"Factions": [
  {
    "Name": "Revolutionary HIP 47947 Liberals",
    "Influence": 0.720000,
    "FactionState": "Boom",
    "MyReputation": 100.000000
  }
]
```

**Implementation**: Too complex for main UI, could be in Overview window

---

## Market/Trade Data (NOT PowerPlay Related)

### MarketSell Events
**Status**: ❌ **NOT RELEVANT FOR POWERPLAY**

The journal shows mining activities (platinum, osmium sales):
```json
{
  "event": "MarketSell",
  "Type": "platinum",
  "Count": 277,
  "SellPrice": 181765,
  "TotalSale": 50348905
}
```

**Why Not Relevant**:
- EliteMeritTracker is focused on PowerPlay merits
- Commodity trading is separate from PowerPlay mechanics
- Would clutter the UI with non-PowerPlay data

---

## Mining Events (NOT PowerPlay Related)

**Status**: ❌ **NOT RELEVANT FOR POWERPLAY**

Journal contains extensive mining data:
- `MiningRefined` (557 events)
- `ProspectedAsteroid` (47 events)
- `LaunchDrone` (114 events)
- `MaterialCollected` (5 events)

**Why Not Relevant**: Mining is not part of PowerPlay merit system

---

## Recommendations for EliteMeritTracker

### High Priority (Easy to Add, High Value)
1. **Population** - Single number, useful context
   - Shows system importance
   - Format: `Pop: 4.1M` or `4,091,441`

2. **System Allegiance** - Single field, useful for PowerPlay context
   - Federation/Empire/Alliance/Independent
   - Format: `Federation` or `Fed` (abbreviated)

### Medium Priority (More Complex, Medium Value)
3. **Dominant Faction State** - Shows if system is in Boom/War/etc
   - Affects trade and mission opportunities
   - Format: `Faction: Name (Boom)`

4. **Government Type** - Additional context
   - Democracy/Corporate/Dictatorship/etc
   - Format: `Democracy`

### Low Priority (Complex, Lower Value)
5. **Full Faction Breakdown** - Only in Overview window
   - Too much data for main UI
   - Could show influence percentages

---

## Current UI Layout with Potential Additions

**Current Layout**:
```
Row 1: Pledged: Felicia Winters  Rank: 224
Row 2: Session: 0  Total: 1,769,313
Row 3: 'System Name'  +10,347 merits
Row 4: Exploited  (26.06%) by Felicia Winters
Row 5: Cycle NET +100.00% ▲
Row 6: Refinery / Tourism - Security: Low
Row 7: (empty - previously reserved for reserve level)
Row 8: [Buttons]
```

**Potential Enhanced Layout** (using Row 7):
```
Row 1: Pledged: Felicia Winters  Rank: 224
Row 2: Session: 0  Total: 1,769,313
Row 3: 'System Name'  +10,347 merits
Row 4: Exploited  (26.06%) by Felicia Winters
Row 5: Cycle NET +100.00% ▲
Row 6: Refinery / Tourism - Security: Low
Row 7: Federation (Democracy) - Pop: 4.1M       ← NEW
Row 8: [Buttons]
```

**Alternative - Compact Row 6**:
```
Row 6: Refinery/Tourism - Low Sec - Fed - Pop: 4.1M
```

---

## Event Frequency Analysis

From the sample journal (Journal.2025-12-19T223328.01.log):

| Event Type | Count | Relevance to PowerPlay |
|------------|-------|------------------------|
| MiningRefined | 557 | ❌ Not relevant |
| Cargo | 403 | ❌ Not relevant (except PowerPlay cargo) |
| FSSSignalDiscovered | 129 | ❌ Not relevant |
| LaunchDrone | 114 | ❌ Not relevant |
| FSDJump | 4 | ✅ **Core event** |
| Location | ? | ✅ **Core event** (not in sample) |
| Powerplay | ? | ✅ **Important** (not in sample) |
| PowerplayMerits | ? | ✅ **Critical** (not in sample) |
| MarketSell | 3 | ❌ Not relevant |

---

## Data NOT Available in Journal

Some PowerPlay-related data that is **NOT** in journal events:

1. **Reserve Level** (Pristine/Major/etc) - Only in body scan events for rings
2. **Exact merit multipliers** - Game calculates internally
3. **Historical PowerPlay cycles** - Only current cycle data
4. **Other players' PowerPlay activities** - Only your own

---

## Conclusion

**Best additions for EliteMeritTracker**:

1. ✅ **Population** - Easy to add, good context
2. ✅ **Allegiance** - One word, useful for PowerPlay
3. 🤔 **Government** - Optional, adds context
4. 🤔 **Faction State** - Optional, more for advanced users

**Not recommended**:
- ❌ Mining data
- ❌ Market prices
- ❌ Commodity data
- ❌ Full faction influence breakdowns (too complex for main UI)

**Keep the focus on PowerPlay**: The plugin should stay focused on tracking merits, systems, and PowerPlay progress - not become a general-purpose Elite Dangerous tracker.

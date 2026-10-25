# THE LAST SHIFT — The story

> This document is the "bible" of the game world: it keeps everything the player
> sees consistent. The player only ever reads a small part of it, through the
> intro, the documents and the scenery.

---

## 1. The place: the Helix Institute

A private biotechnology research centre owned by **Helix Biosystems**.
Its flagship programme, the **Lazarus Project**, studied **cell regeneration**:
repairing any human tissue, indefinitely.

**Sector B** housed the human trials.

## 2. What happened: the night of the incident, six years ago

- One night, a containment unit in Sector B fails.
- The security guard on duty, **Thomas Varenne**, is exposed to the Lazarus
  compound while trying to close a cell: **cell 3**.
- The compound does not kill him. It never stops **rebuilding** him. For six years
  his body has been regenerating without a plan: the bones grow longer, the skin
  thickens, the uniform has fused with his flesh.
- **He is the monster.** His badge still hangs on his chest.

## 3. Why the centre is "abandoned"… but guarded

- **Official version:** closed for budget reasons.
- **Reality:** Helix can neither destroy what lives in Sector B (proof of an
  illegal accident) nor let it go (it is the Lazarus Project's only "success").
- The site is therefore **sealed and kept dormant**. The containment doors are
  **electrically locked**: as long as there is power, the creature stays in Sector B.
- Daytime surveillance is done remotely, by camera. But at night someone has to be
  on site to **watch the generator and restart it** after a power cut.
  Hence the only position still open: **night watchman**.

## 4. The rule that springs the trap

When the power fails, the building switches to **security lockdown**:
- Sector B's **containment doors** open (they only hold with power);
- the **building's exits** seal, so that nothing can get out.

**The watchman is locked in with the creature.** To get out, he must restore the
power: this closes containment again and unlocks the exit.

> This is exactly the game loop: keycard → fuse → both halves of the code →
> generator → exit. The story justifies every mechanic.

## 5. Why the player took the job

The ad said:

> *Night security guard — closed industrial site. Pay well above market rate.
> No experience required. Immediate start.*

The player needs money, fast. We never say why: everyone projects their own
reason, and the character stays nameless so the player can identify with them.

**What they were not told:** the position changes hands every two or three months.

## 6. The predecessor: Daniel Morel

- Night watchman for eleven weeks, until last week.
- He understood what lived in Sector B, and how to survive a power cut.
- He left a **note** for his successor, and changed the last digit of the
  generator code, which he wrote down in his **journal**.
- He **never handed in his badge**. Nobody knows whether he left… or whether he
  is still somewhere in the building.

---

## 7. What the player actually sees in the game

The player never reads this document. They discover the story in small touches:

| Moment | Medium | What they learn |
| --- | --- | --- |
| **Intro** (≤ 30 s, skippable) | 4 text cards | The place, the job, the missing predecessor, the power cut |
| **Objective** | On-screen text | "Restore the power. Get out." |
| **Morel's note** (`N`) | Text to read | Where the fuse and keycard are, the first two digits of the code, and two survival tips that teach the mechanics |
| **Documents** (`D`) | 6 short texts | The accident, the Lazarus Project, what Varenne became, the last digit of the code |
| **The scenery** | Signs, claw marks, cell 3, the green tanks in the lab | What Sector B was used for |
| **The monster** | Its appearance | A uniform, a badge: he was a watchman too |
| **Ending** | Victory or defeat screen | The loop closes |

### The intro

> **Helix Institute — Sector B**
> Closed for six years. Officially, for budget reasons.

> The site is sealed off. Only one position remains: night watchman.
> You start tonight.

> Your predecessor never handed in his badge.

> **12:13 a.m.** The power just went out.

### Morel's note (the `N` object)

> *If you're reading this, the power is out and the B doors are open.*
> *There's a spare fuse in the storeroom, to the north-east.*
> *It's locked: I left my keycard in the maintenance room, to the south-west.*
> *Generator code: 4 7 _. The last digit is in my journal, south-east wing.*
> *Don't run unless you have to. It hears.*
> *Hand in your badge on time.*
> *— D. M.*

"It hears" teaches the player, with no tutorial, that **running makes noise**.

### The endings

- **Victory:** "5:58 a.m. You hand in your badge."
- **Defeat:** "The night watchman position is open again."

---

## 8. The documents to find

Six documents, left by those who were there before. Read in any order, they
piece the story together. Only Morel's journal is required (it holds the last
digit of the code): the others reward exploration.

They are **short** (4 to 6 lines): the player reads them with a monster at their back.

| Document | Room | Cell (row, column) | What it reveals |
| --- | --- | --- | --- |
| Sticky note | Reception hall | (1, 17) | Thomas Varenne was a guard; Sector B already worried the staff |
| Incident report | Guard post | (5, 7) | The accident, the monster's name, why the power is vital |
| Dr Saunier's journal | Break room | (15, 13) | What the compound does, and that Helix knew |
| Daniel Morel's journal | Infirmary | (15, 28) | The predecessor had understood; **last digit of the code: 3, like the cell** |
| Dr Saunier's letter, never sent | Dr Saunier's office | (1, 33) | Varenne's family was lied to |
| Plate of cell 3 | Cell 3 | (3, 43) | "He always comes back to his cell." |

Morel's journal sits next to the monster's starting room: the most important
reward is also the most dangerous one to fetch.

The texts live in `levels/level1_documents.en.txt` and `.fr.txt`, not in the code:
**adding content does not require new code.**

---

## 9. What the story implies for the code and the rendering

| Story element | Consequence |
| --- | --- |
| The monster is a former guard | Image prompt: remains of a grey uniform, a badge |
| The exit is sealed without power | `ExitDoor` stays locked while `power_on` is false |
| The code is split between the note and the journal | `PowerPanel` requires `CODE_START` and `CODE_END` |
| Morel locked the storeroom | `LockedDoor` and the keycard |
| "It hears" | The monster perceives running (`can_hear`) |
| "He always comes back to his cell" | Cell 3 has no locker: going there is a real risk |
| The nameless player | No character name in the interface |

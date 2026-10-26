# NIGHT ROUNDS — The story

> This document is the "bible" of the game world: it keeps everything the player
> sees consistent. The player only ever reads a small part of it, through the
> intro, the documents and the scenery.

---

## 1. The place: Hollowmere Psychiatric Hospital

A private psychiatric hospital, run by a **board of directors** more interested in
results than in its patients. In secret, the board tested an experimental
treatment on them: the **Calder protocol**, a compound meant to "calm" patients
by repairing the brain, and in fact able to rebuild any human tissue.

**Ward B** housed the trials.

## 2. What happened: the night of the incident, six years ago

- One night, a patient in Ward B fights back during an injection.
- The night orderly, **Elias Brandt**, holds him down in **isolation room 3**; in the
  struggle, the needle goes into Brandt's arm and he receives the full dose of C-7.
- The compound was dosed to repair a damaged brain. In a healthy body, it has
  nothing to repair, so it never stops.
- The compound does not kill him. It never stops **rebuilding** him. For six years
  his body has been regenerating without a plan: the bones grow longer, the skin
  thickens, the uniform has fused with his flesh.
- **He is the monster.** His staff badge still hangs on his chest.

The horror comes from the institution and its experiments, never from the
patients: they were the first victims.

## 3. Why the hospital is "closed"… but guarded

- **Official version:** closed for budget reasons.
- The patients were quietly transferred to other hospitals.
- **Reality:** the board can neither destroy what lives in Ward B (proof of illegal
  trials) nor let it go (it is the Calder protocol's only "success").
- The building is therefore **sealed and kept dormant**. The isolation rooms are
  **electrically locked**: as long as there is power, the creature stays in Ward B.
  Like most hospital doors, their locks release when the power fails, so that
  nobody is trapped in a fire.
- Daytime surveillance is done remotely, by camera. But at night someone has to be
  on site to **watch the generator and restart it** after a power cut.
  Hence the only position still open: **night watchman**.

## 4. The rule that springs the trap

When the power fails, the building switches to **security lockdown**:
- the **isolation rooms** of Ward B open (their locks only hold with power);
- the **building's exits** seal, so that nothing can get out.

**The watchman is locked in with the creature.** To get out, he must restore the
power: this locks the isolation rooms again and unlocks the exit.

> This is exactly the game loop: keycard → fuse → both halves of the code →
> generator → exit. The story justifies every mechanic.

## 5. Why the player took the job

The ad said:

> *Night watchman — closed hospital. Pay well above market rate.
> No experience required. Immediate start.*

The player needs money, fast. We never say why: everyone projects their own
reason, and the character stays nameless so the player can identify with them.

**What they were not told:** the position changes hands every two or three months.

## 6. The predecessor: Jonas Reyes

- Night watchman for nine weeks, until last week.
- He understood what lived in Ward B, and how to survive a power cut.
- He left a **note** for his successor, and changed the last digit of the
  generator code, which he wrote down in his **journal**.
- He **never handed in his badge**. Nobody knows whether he left… or whether he
  is still somewhere in the building.

---

## 7. What the player actually sees in the game

| Moment | Medium | What they learn |
| --- | --- | --- |
| **Intro** (≤ 30 s, skippable) | 4 text cards | The place, the job, the missing predecessor, the power cut |
| **Objective** | On-screen text | "Restore the power. Get out." |
| **Reyes's note** (`N`) | Text to read | Where the fuse and keycard are, the first two digits of the code, and two survival tips that teach the mechanics |
| **Documents** (`D`) | 6 short texts | The accident, the Calder protocol, what Brandt became, the last digit of the code |
| **The scenery** | Signs, claw marks, isolation room 3, the treatment baths | What Ward B was used for |
| **The monster** | Its appearance | A uniform, a staff badge: he worked here too |
| **Ending** | Victory or defeat screen | The loop closes |

### The intro

> **Hollowmere Psychiatric Hospital — Ward B**
> Closed for six years. Officially, for budget reasons.

> The building is sealed off. Only one position remains: night watchman.
> You start tonight.

> Your predecessor never handed in his badge.

> **12:13 a.m.** The power just went out.

### Reyes's note (the `N` object)

> *If you're reading this, the power is out and the isolation rooms are open.*
> *There's a spare fuse in the storeroom, to the north-east.*
> *It's locked: I left my keycard in the maintenance room, to the south-west.*
> *Generator code: 4 7 _. The last digit is in my journal, south-east wing.*
> *Don't run unless you have to. It hears.*
> *Hand in your badge on time.*
> *— J. R.*

"It hears" teaches the player, with no tutorial, that **running makes noise**.

### The endings

- **Victory:** "5:58 a.m. You hand in your badge."
- **Defeat:** "The night watchman position is open again."

---

## 8. The documents to find

Six documents, left by those who were there before. Only Reyes's journal is
required (it holds the last digit of the code): the others reward exploration.
They are **short** (4 to 6 lines): the player reads them with a monster at their back.

| Document | Room | Cell (row, column) | What it reveals |
| --- | --- | --- | --- |
| Sticky note | Admissions | (1, 17) | Elias Brandt was an orderly; Ward B already worried the staff |
| Incident report | Nurses' station | (5, 7) | The accident, the monster's name, why the power is vital |
| Dr Halloway's journal | Staff room | (15, 13) | What the compound does, and that the board knew |
| Jonas Reyes's journal | Infirmary | (15, 28) | The predecessor had understood; **last digit of the code: 3, like his room** |
| Dr Halloway's letter, never sent | Dr Halloway's office | (1, 33) | Brandt's family was lied to |
| Plate of isolation room 3 | Isolation room 3 | (3, 43) | "He always comes back to his room." |

Reyes's journal sits next to the monster's starting room: the most important
reward is also the most dangerous one to fetch.

The texts live in `levels/level1_documents.en.txt` and `.fr.txt`, not in the code:
**changing the story does not require new code.**

---

## 9. What the story implies for the code and the rendering

| Story element | Consequence |
| --- | --- |
| The monster is a former orderly | Image prompt: remains of a staff uniform, a badge |
| The exit is sealed without power | `ExitDoor` stays locked while `power_on` is false |
| The code is split between the note and the journal | `PowerPanel` requires `CODE_START` and `CODE_END` |
| Reyes locked the storeroom | `LockedDoor` and the keycard |
| "It hears" | The monster perceives running (`can_hear`) |
| "He always comes back to his room" | Isolation room 3 has no locker: going there is a real risk |
| The nameless player | No character name in the interface |

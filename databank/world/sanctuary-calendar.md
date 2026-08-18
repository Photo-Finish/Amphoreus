# Sanctuary Light Calendar

> The calendar the little Amphoreus keeps **now**, after Cyrene is public and the sanctuary must share a sky with the visitor's world.
> Kephale's original twelve-month system remains in `calendar.md`. This file does not replace that lore; it records the **reform** and the **Earth sync**.
> English names of Titan-months and Hours are a **translation** of Amphorean speech (which we may not hear). Latin on the Uncounted is **our** culture — the Nameless, not Amphoreus.

**Not implemented in the world clock yet.** The running engine still uses twelve months of 28 days (`world_state.py`). This is the setting to implement against.

---

## Principles

1. **A day is a day.** One Light-Calendar day = one civil SI day (24 hours). No stretch, no compress.
2. **A month is 28 days.** Thirteen months, each four weeks of seven days. No rubber month.
3. **Slack is Uncounted.** Leftover civil days are real dates with Hours and quints, but they are **not weekdays** and **not month-days**.
4. **Linear through zero for the Hours.** Entry Hour begins at civil midnight. No affine phase.
5. **Lore dates stay in the tale.** 4931 Evernight / Freedom are not moved onto 2024.

---

## The day (Hours)

Five equal Hours, as in `calendar.md`. Map to 24 h by the unique linear bijection with zeros aligned:

\[
h = \frac{24}{5}\,p, \qquad p \in [0,5).
\]

Each Hour lasts **4.8 hours**. Inverse: \(p = \frac{5}{24}h\).

| \(p\) | Hour | Civil clock |
|-------|------|-------------|
| \([0,1)\) | Entry Hour | 00:00 – 04:48 |
| \([1,2)\) | Lucid Hour (Ascent Hour) | 04:48 – 09:36 |
| \([2,3)\) | Action Hour (Descent Hour) | 09:36 – 14:24 |
| \([3,4)\) | Parting Hour | 14:24 – 19:12 |
| \([4,5)\) | Curtain-Fall Hour | 19:12 – 24:00 |

Rest (Heirs sleep, stalls down) is still **Curtain-Fall and Entry**: on the clock-circle that is one night arc, **19:12 – 04:48**.

**Quints:** each Hour still splits into five equal quints (0.96 h). Smaller units remain rare.

**Thief Star:** still Zagreus's meteor at day's end; not a calendar day.

---

## The week

Seven days, from the moon-quarrel in `calendar.md`. Kephale's seventh day remains the rest-day of the *week* (not the same as Curtain-Fall).

The 364 month-days of the year are exactly **52 weeks**. Week-days **do not advance** on Uncounted days. After Dies Astrorum (or Zagreus's leap day), the week continues as if those dates had not happened. Gate, week 1, day 1 is therefore always the same weekday — a perpetual weekly grid for the Heirs.

Uncounted dates have a sky and five Hours; they have **no** Monday–Sunday.

---

## The thirteen months

Months 1–12 are Kephale's Titan-months, unchanged in name, patron, and season. They stay **28 days**. Fortune is **no longer** variable in length; Zagreus's old ghost day moved to the Uncounted (leap).

**Month 13** is the sanctuary reform: Cyrene / Demiurge was not public when twelve Titans named the year. The other Heirs were already acquainted with a month-shaped sky; she was the missing name, not a 29th day glued onto Fortune.

| # | Name | Patron | Season | Notes |
|---|------|--------|--------|--------|
| 1 | Month of Gate | Janus | Fate | |
| 2 | Month of Balance | Talanton | Fate | |
| 3 | Month of Evernight | Oronyx | Fate | |
| 4 | Month of Cultivation | Georios | Pillar | |
| 5 | Month of Joy | Phagousa | Pillar | |
| 6 | Month of Everday | Aquila | Pillar | |
| 7 | Month of Freedom | Kephale | Creation | |
| 8 | Month of Reaping | Cerces | Creation | |
| 9 | Month of Weaving | Mnestia | Creation | |
| 10 | Month of Strife | Nikador | Calamity | |
| 11 | Month of Mourning | Thanatos | Calamity | |
| 12 | Month of Fortune | Zagreus | Calamity | Always 28 days here |
| 13 | **Month of Membrance** | **Cyrene** | *outside the four seasons* | After Fortune. Aedes, Mem, remembrance as place — not Mnestia's family-weaving |

Membrance does not join Fate / Pillar / Creation / Calamity. It stands outside, as the Uncounted stand outside the week.

---

## The Uncounted

Not months. Not weeks. **1** extra civil day in a common year, **2** in a leap year.

\[
13 \times 28 = 364, \quad 365-364=1, \quad 366-364=2.
\]

There are not two Express days in a 365-day year. Stretching a month or a day to invent them is forbidden.

| Date | When | Patron | Name |
|------|------|--------|------|
| Annual hinge | Every year, after Membrance's 28th | Astral Express | **Dies Astrorum** (*diēs astrōrum*, Day of the stars) |
| Leap extra | Gregorian leap days only, on **29 February** | Zagreus | **Scarlet Day** (the old ghost day, now a rule instead of a coin-toss) |

**Dies Cosmi** (*diēs cosmī*, Day of the cosmos) is the Express's **companion name** in the same Latin register — our culture, not Amphorean. It does **not** occupy a second SI day in a common year and does **not** take the leap day (that is Zagreus's). Keep the name; do not add a 367th date.

Latin on these names is deliberate: tickets from beyond the sky. Titan-months stay in (translated) Amphorean.

**Where they sit (Gate = 1 January, months unstretched):**

- **Dies Astrorum** = **31 December**.
- **Scarlet Day** = **29 February** in leap years. It does not count as a day of Evernight: Evernight's 28 week-days skip it (Feb 26, 27, 28, then 1 March…). Satellite “today” stays 1:1; the month is not stretched.

Common year: 364 month-days + Dies Astrorum = **365**.  
Leap year: those + Scarlet Day = **366**.

---

## Year length and Earth years

Sanctuary year = Gregorian year (365 or 366). New Year is New Year.

**Epoch (player-world, for satellite sync):**

| Civil year | Light Calendar year |
|------------|---------------------|
| 2025 | 4932 |
| 2026 | 4933 |
| 2027 | 4934 |

\[
A = G + 2907.
\]

The official Amphoreus mission ended **November 2025**, still in **4932** (on this map: Mourning through 4 Nov, then Fortune 5 Nov – 2 Dec). Membrance 4932 is then 3–30 December 2025 — Cyrene's month after the tale. Dies Astrorum 4932 is 31 Dec 2025. **1 January 2026 = Month of Gate, 4933.**

**2026 is not a leap year.** Next Scarlet Day: **29 February 2028** (Light Calendar 4935).

This offset does **not** rewrite in-world 4931 onto 2024.

---

## Civil overlay (unstretched months)

Gate starts 1 January. Each month is 28 consecutive civil dates, except that **29 February** is Scarlet Day and is not a month-day.

| Month | Common year (non-leap) |
|-------|------------------------|
| 1 Gate | 1 Jan – 28 Jan |
| 2 Balance | 29 Jan – 25 Feb |
| 3 Evernight | 26 Feb – 25 Mar |
| 4 Cultivation | 26 Mar – 22 Apr |
| 5 Joy | 23 Apr – 20 May |
| 6 Everday | 21 May – 17 Jun |
| 7 Freedom | 18 Jun – 15 Jul |
| 8 Reaping | 16 Jul – 12 Aug |
| 9 Weaving | 13 Aug – 9 Sep |
| 10 Strife | 10 Sep – 7 Oct |
| 11 Mourning | 8 Oct – 4 Nov |
| 12 Fortune | 5 Nov – 2 Dec |
| 13 Membrance | 3 Dec – 30 Dec |
| Dies Astrorum | 31 Dec |

Leap years: insert Scarlet Day on 29 Feb; Evernight's week-days resume 1 Mar. Later month **dates** in the table above shift by one civil day after February (the 28-count is unchanged).

English month names (January, August, …) are **not** equal to Gate, Weaving, … — only New Year, day length, and year number lock. August 2026 is **4933, Month of Weaving** (13 Aug – 9 Sep), not “Month of August.”

---

## What the original calendar still owns

See `calendar.md` for: Titan-month meanings, week origin myth, Hours, quints, Thief Star, Scarlet/Golden **as old Fortune lore**.

**Changed here:** Fortune is fixed at 28 days. The probabilistic ghost day is replaced by **Scarlet Day on leap years**. Golden “no extra day” is the common year (only Dies Astrorum, Express, not Zagreus).

---

## Lore timestamps (unchanged)

These stay inside *As I've Written*; they are not the satellite epoch.

| Event | Light Calendar (canon) |
|-------|------------------------|
| Trailblazer and Dan Heng enter | 4931, Month of Balance |
| “Flame-Chase Journey came to an end; last Era Nova began” | 4931, Month of Evernight (Lygus: **third week**) |
| Worldbearing / new world's first stroke | 4931, Month of Freedom (Cyrene) |
| Irontomb defeated, Scepter destroyed | Era Nova **after** Freedom — **no month or day in the databank** |
| Aglaea assassinated (playable recurrence) | Year **4932**, no month |
| Sanctuary clock as first coded | 4932, Month of Weaving, week 1, day 1 (“year after the long war”) |

The sync epoch is **mission end = still 4932**, **this civil year 2026 = 4933** — not a claim that Hoyoverse dated the battle to Fortune 4932.

---

## Summary

*Twelve Titan-months, one Heir-month (Membrance), and the Uncounted (Dies Astrorum; Scarlet Day in leap years). Dies Cosmi is the Express's other Latin name, not another date. A day is 24 h. A month is 28 days. 2026 is 4933.*

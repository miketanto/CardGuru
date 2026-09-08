# Adjudication: `tax-opponent-spells`

Decide, for each card below, whether it satisfies the QUESTION.
Judge the card on its own text. There is no query here and you do not know which search returned it — that is deliberate.

## Question

> stax pieces that tax my opponents' spells without taxing mine

**What makes it tricky:** The asymmetry is the whole question - Thalia and Sphere of Resistance use nearly identical wording but tax everyone including you, so word-level matching cannot separate symmetric from one-sided taxes.

**Author's notes:** Good probe of whether the system models the affected-player argument of a static effect.

**Cards already accepted as satisfying it** (for a consistent reading, not as a pattern to match): Grand Arbiter Augustin IV

**Cards already rejected**: Thalia, Guardian of Thraben, Sphere of Resistance

## Cards

| # | card | type | text |
|---|---|---|---|
| 1 | Callaphe, Beloved of the Sea | Legendary Enchantment Creature Demigod | Callaphe's power is equal to your devotion to blue. (Each {U} in the mana costs of permanents you control counts toward your devotion to blue.)\nCreatures and enchantments you control have "Spells your opponents cast that target this permanent cost {1} more to cast." |
| 2 | Elspeth Conquers Death | Enchantment Saga | (As this Saga enters and after your draw step, add a lore counter. Sacrifice after III.)\nI — Exile target permanent an opponent controls with mana value 3 or greater.\nII — Noncreature spells your opponents cast cost {2} more to cast until your next turn.\nIII — Return target creature or planeswalk |
| 3 | Jubilant Skybonder | Creature Human Wizard | Flying\nCreatures you control with flying have "Spells your opponents cast that target this creature cost {2} more to cast." |
| 4 | Monastery Siege | Enchantment | As Monastery Siege enters, choose Khans or Dragons.\n• Khans — At the beginning of your draw step, draw an additional card, then discard a card.\n• Dragons — Spells your opponents cast that target you or a permanent you control cost {2} more to cast. |
| 5 | Soul Partition | Instant | Exile target nonland permanent. For as long as that card remains exiled, its owner may play it. A spell cast by an opponent this way costs {2} more to cast. |
| 6 | Tax Collector | Creature Human Advisor | When Tax Collector enters, choose one —\n• Tax — Until your next turn, spells your opponents cast cost {1} more to cast.\n• Arrest — Detain target creature an opponent controls. (Until your next turn, that creature can't attack or block and its activated abilities can't be activated.) |

## Answer format

Write JSON to `verdicts/tax-opponent-spells.json`: an object mapping each card name to `"present"`, `"absent"` or `"unclear"`.

- `present` — it clearly satisfies the question.
- `absent`  — it clearly does not.
- `unclear` — the question wording genuinely does not decide it. Use this freely; a forced call is worse than no call.

Every one of the cards listed must appear exactly once.

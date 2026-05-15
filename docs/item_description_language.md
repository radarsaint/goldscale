# Item Description Language Research

Goldscale must parse explicit pricing inputs from D&D 5e-style magic item text without becoming an item database. These notes summarize SRD/OGL-style wording patterns and the safe parser implications.

Sources reviewed:

- Wand of Magic Missiles, SRD-style text: charges, recharge dice, and last-charge d20 destruction language. Source: https://dnd-srd-sphinx.readthedocs.io/en/latest/magic-item/wand-of-magic-missiles.html
- Wand of Wonder, SRD-style text: charges, range, target/point language, random table, save DC, and randomized effects. Source: https://5thsrd.com/Gamemaster_Rules/magic_items/wand_of_wonder/
- Basic Rules magic item charges overview: charges and regained-charge language. Source: https://www.dndbeyond.com/sources/dnd/basic-rules-2014/magic-items
- SRD magic items A-Z mirror: examples of save DCs, spellcasting text, bonus language, damage dice, healing spell lists, AoE shapes, and non-impact counts. Source: https://5e.d20srd.org/srd/magicItems/magicItemsAToZ.htm
- Necklace of Fireballs SRD page: bead-count dice. Source: https://dnd-wiki.org/wiki/SRD5%3ANecklace_of_Fireballs

This note intentionally does not copy full item descriptions or create runtime item data.

| Language pattern | Example phrase shape | Should Goldscale extract? | Should Goldscale ignore? | Reason | Parser/test implication |
| --- | --- | --- | --- | --- | --- |
| Fixed charge count | `has 7 charges`, `has 10 charges`, `The wand has 3 charges` | Yes, as `charges` | No | Explicit count of item uses is part of the formula when an impact is supplied. | Keep charge-count extraction. Test that `has 7 charges` is extracted. |
| Recharge dice | `regains 1d6 + 1 expended charges daily at dawn`, `regains 1d3 expended charges` | No | Yes | Recharge dice describe replenishment, not damage/healing impact. | Keep recharge dice rejection. Test recharge dice do not become damage. |
| Last-charge destruction roll | `roll a d20`, `On a 1, ... destroyed` | No | Yes | A d20 roll here is a breakage/random outcome check, not impact. | Keep `roll d20` rejection. Test `roll a d20` is not damage. |
| Random table | `Roll d100 and consult the table`, `roll on the effects table` | Extract only randomized marker | Ignore as impact | Random outcomes need DM-supplied impact; table entries vary too much to price safely. | Keep randomized flag. User-facing tests should offer explicit utility-tier retries only. |
| Spellcasting text without dice | `cast fireball`, `cast magic missile`, `cast cure wounds` | No | Yes | Spell names imply mechanics, but Goldscale must not infer hidden spell damage/healing from names. | Help text should ask user to add dice manually. Tests should verify missing impact rather than inferred dice. |
| Explicit damage dice | `takes 1d6 fire damage`, `deals 2d10 force damage` | Yes, as damage | No | Dice are directly tied to damage language. | Keep damage keyword extraction. |
| Explicit healing dice | `2d4+2 healing`, `regain 2d4 + 2 hit points` | Yes, as healing | No | Dice are directly tied to healing/hit point recovery. | Keep healing keyword extraction. |
| Bonus language | `you gain a +1 bonus`, `grants a +2 bonus` | Yes, as bonus | Sometimes block final pricing | Bonus is explicit impact, but charged complex items may have more priced effects. | Keep bonus extraction. Keep charged-complex partial-bonus guard. |
| Save DC | `save DC 15`, `DC 17` | No | Yes | DC is a difficulty number, not damage/healing/charges/utility tier. | Add tests that DCs are not impact. |
| Range-only distance | `within 120 feet`, `within 60 feet of you` | No | Yes for AoE | Range selects a target; it is not area coverage by itself. | Remove range-only `within N feet` AoE detection. Test it does not set AoE. |
| Point of origin alone | `point in space`, `point of origin` | No | Yes for AoE | A target point is not enough to prove an area effect. | Test point-origin language does not set AoE unless shape/radius/creature-in-area wording appears. |
| Area shape/radius | `20-foot radius`, `60-foot cone`, `each creature in the cone`, `sphere`, `cube` | Yes, as AoE | No | These are direct area-shape clues. | Keep shape/radius/cone/cube/sphere/cylinder and `each creature in/within` AoE detection. |
| Quantity dice | `1d6 + 3 beads`, `1d6 removed stars reappear`, `1d4 + 2 magic beads` | No | Yes | Dice count objects/uses, not damage or healing. | Add quantity-noun dice rejection for beads/stars and similar count nouns. |
| Charge expenditure numbers | `1 charge`, `5 charges`, `one of its 3 charges` | Extract fixed total only when phrased as item has count | Ignore as impact | Per-effect costs are not total charges and not damage. | Existing charge parser should avoid `1 charge` expenditure unless phrased as total charge count. |

## Safe Parser Principles

- Extract only explicit pricing inputs: rarity, category/type, fixed charge count, bonus, dice tied to damage/healing, AoE shape language, utility tier, official price override, sell percentage.
- Ignore dice attached to recharge, random outcome, destruction, save DC, range, or object-count language.
- Treat randomized/table-driven items as needing explicit user impact.
- Treat spell names as text only. If the pasted description lacks dice, ask for dice manually.
- Do not map item names to mechanics, prices, damage, healing, utility tiers, or official item behavior.

# Goldscale Agent Instructions

Goldscale is a Discord.py bot for deterministic D&D 5e magic item pricing.

Project rules:

- Do not add JSON item databases.
- Do not infer D&D item mechanics from item names.
- Do not invent official prices.
- Utility impact may only be minor, reusable, or broad.
- Randomized/table-driven items must ask for explicit impact.
- Recharge dice are not damage.
- Bare numbers are not sell percentages.
- Never commit `.env` or any Discord token.

Implementation guidance:

- Keep parser and pricing behavior deterministic.
- Add focused parser and pricing tests for behavior changes.
- Do not print, inspect, or expose Discord tokens.
- Use explicit item-description inputs only. Do not use supplied price overrides.

# Goldscale Agent Instructions

Goldscale is a Discord.py bot for deterministic D&D 5e magic item pricing.

Project rules:

- Design for players first, not programmers.
- Goldscale must not require users to learn command syntax or formula vocabulary as the default workflow. Commands may exist as shortcuts, but normal guidance should ask plain-language questions and accept plain-language replies.
- Do not present retry commands as the primary solution to missing information.
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

## Cursor Cloud specific instructions

- The environment install creates a repo-local `.venv` and installs `requirements.txt`. Run tests from the repository root with `.venv/bin/python -m pytest`.
- The `?gs` handlers in `goldscale/bot.py` price items through `start_appraisal` and `continue_appraisal`. That path is the product interaction and does not open a Discord connection.
- Leave `DISCORD_TOKEN` unset unless this session should log the bot into Discord. Starting `goldscale_bot.py` while another process is already logged in makes Goldscale reply twice.

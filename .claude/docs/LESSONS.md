# Lessons

- **S1 (2026-11-21):** the plan's file paths (`minotaurus/levels.py`) disagreed with CLAUDE.md
  (`minotaurus/engine/`). CLAUDE.md wins; fix the plan when next edited.
- **S1:** tests that pin the exact observation layout protect `obs_version` 1; a layout change must
  bump the version.
- **S1:** the race rule "does the loser keep going?" was not in the design; chosen: the race ends at
  the first finish.

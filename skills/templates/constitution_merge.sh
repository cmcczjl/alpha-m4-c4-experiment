# Constitution Steamding Template

This template can be used to create a new constitution section or merge existing ones.

```bash
# Merge new rules into existing constitution
# Usage: bash merge_constitution.sh [new_rules.md] [existing_constitution.md]

EXISTING=$2
NEW=$1

# Simple merge: append new non-duplicate lines
grep -v -F -f <(grep '^##\\|^-\\|^$' "$EXISTING" | sort) "$NEW" >> "$EXISTING"

# Or use Python for smarter merge:
python3 - <<'PY'
import sys
existing = open(sys.argv[2]).read().splitlines()
new_lines = open(sys.argv[1]).read().splitlines()
seen = set(existing)
for line in new_lines:
    if line not in seen:
        existing.append(line)
        seen.add(line)
open(sys.argv[2], 'w').writelines(l + '\n' for l in existing)
PY
```
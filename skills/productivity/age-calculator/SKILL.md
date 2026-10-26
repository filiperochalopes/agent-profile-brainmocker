---
name: age-calculator
description: Calculate exact age from birth date to reference date.
version: 1.0.0
author: BMoca
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [age, calculation, date, deterministic]
    related_skills: [evolution-api]
---

# Age Calculator Skill

Deterministic age calculation from birth date to reference date. No LLM approximation.

## Function: calculate_age(birth_date, reference_date=None)

- **birth_date**: string "YYYY-MM-DD" or "DD/MM/YYYY" or date object
- **reference_date**: string "YYYY-MM-DD" or date object (default: today)
- **Returns**: dict with years, months, days, total_months, formatted string

## Rules

- Age < 2 years: return in months ("14 meses")
- Age >= 2 years: return in years ("3 anos")
- Handles leap years correctly
- Pure Python, no external dependencies

## Integration: Cadastro analysis (with evolution-api)

Used for calculating children's ages from birth dates parsed from `*CADASTRO DE PARTICIPANTES*` messages in WhatsApp groups (Escola Sem Nome).

**Pattern**:
```python
from age_calculator import calculate_age
# birth_date from cadastro (DD/MM/YYYY or inferred year)
# reference_date = analysis date (e.g., "2026-10-24")
age = calculate_age(birth_date, reference_date)
print(age['formatted'])  # e.g., "2 anos" or "14 meses"
```

**Critical**: User requires deterministic calculation — never approximate manually. Manual approximations in this session produced errors (7 meses vs 2 anos, 5 anos vs 4 anos, etc.).

**Birth date resolution**: See `evolution-api/references/cadastro-birth-date-patterns.md` for patterns (age-only, day/month-only, typo years) and resolution rules. Always resolve to YYYY-MM-DD before calling `calculate_age`.
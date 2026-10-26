# Cadastro Birth Date Patterns — Escola Sem Nome

Reference for parsing incomplete birth dates from `*CADASTRO DE PARTICIPANTES*` messages.

## Patterns encountered

| Pattern | Example | Parsing strategy |
|---------|---------|------------------|
| **Complete** | `23/10/2024` | Use directly |
| **Complete + approx age** | `06/09/2022 - 5 anos` | Use date; age is parent's approximation (often rounded up) |
| **Day/month only** | `19/02` | Infer year: if parent states age ("2 anos"), calculate birth year = ref_year - age; adjust if birthday hasn't occurred yet |
| **Age only** | `2 anos` | Infer birth year = ref_year - age; month/day unknown — ask user for complete date |
| **Day/month + approx age** | `01/12 (3 anos)` | Use day/month; infer year from stated age (3 anos → born ~2023) |
| **Typo year (future)** | `23/10/2026` for 3-year-old | Correct year: if age stated, use age to infer correct year (2026 - 3 = 2023) |
| **Typo year (format)** | `01/08/2021-5 anos` (no space) | Parse date before dash; age is approximation |

## Resolution rules

1. **Always prefer explicit complete date** (DD/MM/YYYY) over inferred
2. **Parent-stated ages are approximations** — usually rounded up to next birthday
3. **When inferring year from age**: `birth_year = reference_year - stated_age`; if day/month known, check if birthday already passed in reference year — if not, subtract 1 more year
4. **Flag all inferred dates** for user confirmation
5. **Use `age-calculator` with the resolved date** for final age — never manually approximate

## Examples from 2026-10-24 analysis

| Child | Raw input | Resolved date | Age (calc) | Parent said |
|-------|-----------|---------------|------------|-------------|
| Enoque | `2 anos` | 13/08/2024 (user confirmed) | 2a 2m | 2 anos |
| Elisa | `01/12 (3 anos)` | 01/12/2023 | 2a 10m | 3 anos |
| Aurora | `19/02` | 19/02/2024 (inferred from 2 anos) | 2a 8m | 2 anos |
| José Antonio | `06/09/2022 - 5 anos` | 06/09/2022 | 4a 1m | 5 anos |
| Maria Olívia | `24/11/2024 - 2 anos` | 24/11/2024 | 23 meses | 2 anos |
| Benício | `23/10/2026 - 3 anos` | 23/10/2023 (typo fix) | 3 anos | 3 anos |
| Melissa | `23/10/2024` | 23/10/2024 | 2 anos | — |

## Integration with age-calculator

```python
from age_calculator import calculate_age

# After resolving birth_date to YYYY-MM-DD:
age = calculate_age(birth_date, reference_date)
# age['formatted'] gives "2 anos" or "14 meses"
```
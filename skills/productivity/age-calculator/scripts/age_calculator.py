"""Age calculation module for age-calculator skill."""
from datetime import date
import re
import calendar

def parse_date(d):
    """Parse YYYY-MM-DD, DD/MM/YYYY, or date object."""
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        d = d.strip()
        if re.match(r'^\d{4}-\d{2}-\d{2}$', d):
            y, m, d = map(int, d.split('-'))
            return date(y, m, d)
        if re.match(r'^\d{2}/\d{2}/\d{4}$', d):
            d, m, y = map(int, d.split('/'))
            return date(y, m, d)
    raise ValueError(f"Invalid date format: {d}")

def calculate_age(birth_date, reference_date=None):
    """
    Calculate exact age from birth_date to reference_date.
    Returns dict: years, months, days, total_months, formatted.
    
    Usage in cadastro analysis:
        from age_calculator import calculate_age
        age = calculate_age("2024-10-23", "2026-10-24")
        # {'years': 2, 'months': 0, 'days': 1, 'total_months': 24, 'formatted': '2 anos'}
        print(age['formatted'])  # '2 anos'
    """
    born = parse_date(birth_date)
    ref = parse_date(reference_date) if reference_date else date.today()
    
    # Calculate years
    years = ref.year - born.year
    if (ref.month, ref.day) < (born.month, born.day):
        years -= 1
    
    # Calculate months
    month_diff = ref.month - born.month
    if ref.day < born.day:
        month_diff -= 1
    if month_diff < 0:
        month_diff += 12
    
    # Calculate days
    last_month = ref.month - 1 if ref.month > 1 else 12
    last_year = ref.year if ref.month > 1 else ref.year - 1
    days_in_last_month = calendar.monthrange(last_year, last_month)[1]
    day_start = born.day
    if day_start > days_in_last_month:
        day_start = days_in_last_month
    
    if ref.day >= day_start:
        days = ref.day - day_start
    else:
        days = ref.day + days_in_last_month - day_start
        month_diff -= 1
        if month_diff < 0:
            month_diff = 11
            years -= 1
    
    total_months = years * 12 + month_diff
    
    if years < 2:
        formatted = f"{total_months} meses"
    else:
        formatted = f"{years} anos"
    
    return {
        "years": years,
        "months": month_diff,
        "days": days,
        "total_months": total_months,
        "formatted": formatted
    }

if __name__ == "__main__":
    # Quick test
    print(calculate_age("2024-10-23", "2026-10-24"))
    print(calculate_age("2025-08-01", "2026-10-24"))
    print(calculate_age("2024-11-24", "2026-10-24"))

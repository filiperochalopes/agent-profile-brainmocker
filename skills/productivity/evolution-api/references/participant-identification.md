# Participant identification in WhatsApp groups (wpp.orango.io)

## Problem
Group participant list (`GET /group/participants/{instance}?groupJid={JID}`) returns LIDs and phone numbers but often has `name: null` for many members. Need to correlate with message `pushName` and/or user-provided phone directory.

## Data sources
1. **Roster endpoint** → `id` (LID), `phoneNumber` (e.g. `557592637710@s.whatsapp.net`), `admin`, `name` (often null)
2. **Messages** → `key.participant` (LID), `pushName` (display name at send time)
3. **User-provided directory** → formatted phone numbers with known names

## Correlation procedure
```python
# 1. Build LID -> pushName map from messages
lid_name = {}
for m in messages:
    p = m.get('key', {}).get('participant', '')
    pn = m.get('pushName') or m.get('key', {}).get('pushName')
    if p.endswith('@lid') and pn:
        lid_name[p] = pn

# 2. Build clean phone -> formatted map from user directory
phone_to_formatted = {
    '557592637710': '+55 75 9263-7710',
    # ...
}

# 3. Enrich roster
for r in roster:
    lid = r['id']
    phone_raw = r.get('phoneNumber', '').replace('@s.whatsapp.net', '')
    r['push_name'] = lid_name.get(lid)
    r['phone_formatted'] = phone_to_formatted.get(phone_raw)
```

## Matching cadastro to roster
- Cadastro messages contain full names of parents. Parse and match to roster by `push_name` or LID.
- When a couple shares a cadastro, both may be in the roster with different LIDs/phones.
- Use the `phone_formatted` from user directory to confirm identities for participants without pushName.

## Escola Sem Nome specific (Oct 2026)
- Group JID: `120363429552702512@g.us`
- Instance: `Filipe Lopes - Pessoal` (`Filipe%20Lopes%20-%20Pessoal`)
- Known admins: `140668919906317@lid` (Robson Cardoso), `216797198418110@lid` (Lorena Lopes), `109032123699374@lid` (Layane Neri)
- Cadastro format: `*CADASTRO DE PARTICIPANTES*` followed by parent names and child data
- **Age calculation**: Use the `age-calculator` skill (`calculate_age(birth_date, reference_date)`) for deterministic ages. Never approximate manually. Reference date = analysis date (e.g., `2026-10-24`).
- **Output formats**: User requests pure lists for copying. Three variants:
  1. `<Nome completo> (+55 DDD NUMERO)` — with hyphens
  2. `<Nome completo> (+55 DDD NUMERO)` — without hyphens
  3. `<Nome completo>` — names only

## Cadastro-to-roster correlation (Oct 2026 session)
- 19 roster participants
- 13 had pushName from messages
- 6 had no pushName → matched via 8 user-provided phones
- Result: 14 identified, 5 known via pushName only (Laila, Layane, Ester, Igor, Robson)
- 1 truly unknown initially: +55 75 8318-5656 (later identified as Marco Antonio Suzin Lanzzarini)
- Couples often appear as separate roster entries (e.g., Igor & Laís, Michel & Layane, Davi & Ester)
- Cadastro author may be one parent; the other parent is in roster with different LID

## Pitfalls
- LIDs are stable; pushNames can change when a user updates their profile name. Always re-correlate on fresh message pulls.
- `phoneNumber` in roster includes `@s.whatsapp.net` suffix; strip before matching.
- Some participants never send messages → no pushName available. Rely on user-provided phone directory.
- Multi-device: same user may appear with different LIDs; dedupe by phone number.
- Admin status in roster (`admin: "admin"` or `null`) useful for knowing who can manage group settings.
- **Incomplete cadastro data**: parents often provide only age ("2 anos"), only day/month ("19/02"), or day/month+approx age ("01/12 (3 anos)"). Use `evolution-api/references/cadastro-birth-date-patterns.md` for resolution, then `age-calculator` for final age.
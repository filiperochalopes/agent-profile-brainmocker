# Shared Google Calendars

Use this procedure when the user wants a separate calendar/agenda shared with named people. This is different from creating an event on an existing calendar.

## When to Use

Use for requests to create a named calendar and grant people access. Do not use it for adding guests to one event.

## Procedure

1. Run `setup.py --check` for the active Hermes profile. Use the profile's authenticated token; do not copy credential files from another profile when the active profile already authenticates successfully.
2. Before any write, show the exact calendar title, recipient email addresses, and intended roles. Obtain approval.
3. Use the Google Calendar API directly: call `calendars.insert` with the requested `summary`, then call `acl.insert` for each recipient with an explicit role such as `writer`. Set notification behavior explicitly (`sendNotifications=True` or `False`) according to what was approved.
4. Read the calendar back with `calendars.get` and enumerate its rules with `acl.list`. Report the calendar ID, title, timezone, and every requested person's resulting role.

## Minimal Python pattern

Run in an environment with `google-auth` and `google-api-python-client`, reading the active profile's `google_token.json`:

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

service = build("calendar", "v3", credentials=creds, cache_discovery=False)
calendar = service.calendars().insert(body={"summary": title}).execute()
for email in recipients:
    service.acl().insert(
        calendarId=calendar["id"],
        sendNotifications=True,
        body={"scope": {"type": "user", "value": email}, "role": "writer"},
    ).execute()
verified_calendar = service.calendars().get(calendarId=calendar["id"]).execute()
verified_acl = service.acl().list(calendarId=calendar["id"]).execute()["items"]
```

## Pitfalls

- Skip `acl.insert` for a recipient who is already the calendar owner, and verify their owner role with `acl.list`; Google rejects attempts to change the authenticated owner's access level with a 403.
- Treat an email alias that resolves to the authenticated owner the same way as the owner; report its actual role from the final ACL instead of assuming the requested role.
- Preserve recipient addresses exactly as supplied, including corrections; an address that looks similar is not a valid substitute.
- Do not report the calendar as shared until `acl.list` confirms every requested recipient's resulting access role.

# Versioning a Hermes profile safely

Use this when a user wants Git history for a profile's rules, configuration, skills, or selected memory.

## Distinguish authoring from installing

A profile distribution is an authored Git repository. `hermes profile install <repo> --alias` consumes that repository to create a profile elsewhere; it does not initialize, publish, or attach a remote to the current profile.

## Inventory before staging

1. Resolve the active profile with `$HERMES_HOME`.
2. Inspect hidden credential files explicitly; do not infer their absence from a shallow directory listing:

   ```bash
   for f in .env .env.lock .env.example auth.json auth.lock; do
     test -e "$HERMES_HOME/$f" && printf '%s exists\n' "$f"
   done
   ```

3. List SQLite databases and runtime directories before writing a minimal `.gitignore`:

   ```bash
   find "$HERMES_HOME" -type f \( -name '*.db' -o -name '*.sqlite' -o -name '*.sqlite3' \) -print
   ```

4. Ask whether memory is intentionally versioned. Do not ignore `memories/` when the user wants it in history; still ignore lock files and conversation/session state unless the user has expressly chosen to retain them.

## Minimal ignore policy

Build `.gitignore` from files and directories that actually exist. Always exclude credentials, OAuth tokens, messaging sessions, and SQLite database binaries. Preserve a deliberate `.env.example` if present, but never version an actual `.env` or its lock file. Ignore generated locks, job outputs, caches, and audit logs separately from their versioned definitions such as `cron/jobs.json`.

A `.gitignore` does not remove files already in the index. After changing it, inspect `git status --short`; unstage mistakenly added paths with `git rm --cached <path>` for a tracked directory or `git restore --staged <path>` for ordinary files.

## Detect nested repositories before `git add .`

Run this before staging a profile root:

```bash
find "$HERMES_HOME" -type d -name .git -prune -print
```

Each nested repository needs an explicit choice:

- **Keep independent (default):** remove its gitlink from the profile index and ignore its directory in the outer repository. Commit and push its source in its own repository.
- **Use a submodule:** only when the nested repository has an accessible, stable remote and consumers need the exact source checkout. `git add .` creates only a gitlink; it does not create a usable submodule declaration or provide a remote for a child repository that lacks one.
- **Make a monorepo:** deliberately migrate history with `git subtree` or another reviewed migration; never delete a child `.git` directory as an incidental cleanup.

Verify accidental gitlinks with:

```bash
git -C "$HERMES_HOME" ls-files --stage | awk '$1 == "160000" {print}'
```

Do not commit while generated job outputs, locks, caches, runtime state, or an unintended mode-`160000` gitlink remains staged. If an initial local commit already captured newly ignored files, remove every tracked ignored path with `git ls-files -ci --exclude-standard`, amend before the first push, then re-scan the committed tree for credential-shaped values.

### Submodule publication workflow

1. Commit and push each child repository first. A child without an accessible remote is not a usable submodule.
2. For a third-party child with required local changes, fork it, keep the original as `upstream`, commit the change to the fork, and point the profile submodule at the fork. Never point the parent at an unpushed child commit; a clone cannot reproduce it.
3. Use SSH URLs for every `origin` and in `.gitmodules` when the user requires SSH. After editing `.gitmodules`, run `git submodule sync --recursive`, commit `.gitmodules` and the mode-`160000` entries, then verify each remote ref with `git ls-remote <ssh-url> refs/heads/main`.
4. Verify both `git submodule status` and the parent remote SHA after the push. Do not assume a profile installer recursively initializes submodules; test that install path or document `git submodule update --init --recursive` for manual clones.

## Commit convention

Use English Conventional Commits for profile repositories. A baseline profile commit can be:

```text
chore(profile): initialize versioned profile configuration
```

Use focused later commits, for example `fix(policy): restrict API access by instance` or `chore(cron): update scheduled job definitions`.

# Operations, backup and updates

## Installed Linux service

Run as the same desktop user who installed the app:

```bash
systemctl --user status mystical-mark-astrology.service
systemctl --user restart mystical-mark-astrology.service
journalctl --user -u mystical-mark-astrology.service -n 80 --no-pager
```

The optional gateway has its own `mystical-mark-astrology-gateway.service`. To inspect both, run:

```bash
"$HOME/.local/lib/mystical-mark-astrology/current/.venv/bin/python" \
  "$HOME/.local/lib/mystical-mark-astrology/current/manage.py" status
```

Use `password` in place of `status` to show the local password, or `reset-password` to generate a new one and restart the app. The username remains `mark`. Do not share logs before checking them for private information.

## Portable launcher

Keep `run.py` running; Ctrl+C stops it. Use the same Python executable, OS account and `MM_ASTRO_DATA` override (if any) for every launch and password check. Windows and macOS data locations are listed in the README.

To reset a portable password, stop the app, delete only `access-password` from its data directory, then run `run.py --show-password` and restart. Existing browser login prompts may require closing/reopening the browser. Do not delete the database.

## Backups

The app's JSON backup contains saved chart inputs, notes and settings. Store it privately; restore is **additive**, so repeated imports duplicate saved charts. It does not include your login password, ephemeris files or Caddy CA.

For a complete filesystem backup, stop the app and copy its data directory. Also back up your private gateway configuration and Caddy storage separately if you need to retain the same CA. CA private keys must never be committed or shared. Resume the app after copying. Keep at least one backup on separate storage and test a JSON import using disposable data before relying on it.

## Update

Download a new source release into a separate folder. Back up first. For installed Linux, run `bash install.sh` there as your original user. The installer preserves the data directory and existing gateway environment; it creates a database snapshot before switching `current`, and records the old release as `previous`. Read any migration notes before proceeding.

For portable installations, stop the app, back up data, extract the new source, recreate its `.venv`, install its requirements, then launch with the same OS account and data-path override. Do not overwrite or move runtime data into the repository.

Release 1.2.0 changes neither the database schema nor calculation methods.

## Linux code rollback

Inspect the links first:

```bash
ls -l "$HOME/.local/lib/mystical-mark-astrology/current" \
      "$HOME/.local/lib/mystical-mark-astrology/previous"
```

If `previous` exists and is the intended release:

```bash
systemctl --user stop mystical-mark-astrology.service
app_root="$HOME/.local/lib/mystical-mark-astrology"
previous_release=$(readlink "$app_root/previous")
test -d "$previous_release" && ln -sfn "$previous_release" "$app_root/current"
systemctl --user start mystical-mark-astrology.service
```

This switches code only. Do not roll back across a future database migration without following that release's instructions. Restoring a database snapshot can discard later chart edits; keep a copy of the current data before restoration.

## Disable startup

```bash
systemctl --user disable --now mystical-mark-astrology.service
systemctl --user disable --now mystical-mark-astrology-gateway.service
```

The second command applies only if the gateway was configured. Data and source releases remain available. Do not disable user lingering if other services rely on it. To remove a trusted CA, follow the client-specific instructions in [HTTPS.md](HTTPS.md).

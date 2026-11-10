# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Impact Data: a Django 5.2 app (Python 3.12, French UI/comments) for managing adherents (members), organizations, interactions, badges (QR codes / PDF via reportlab, imgkit, html2image), and per-agent objectives. Single Django app `core` inside project `impactData`. `README.md` has full install/deploy steps (and many other `*.md` files in the root are historical fix notes, not authoritative docs).

## Commands

```bash
venv\Scripts\activate                 # Windows venv is checked into the working dir
pip install -r requirements.txt       # file is UTF-16 encoded; mysqlclient is only needed for MySQL
python manage.py migrate
python manage.py initialize_reference_values   # required seed data (ReferenceValue)
python manage.py initialize_permissions        # required seed data (RolePermission per role)
python manage.py runserver
python manage.py test_email | test_badge_generation   # custom management commands (not unit tests)
```

Config is read via python-decouple from `.env` (`SECRET_KEY`, `EMAIL_*`, optional `DB_*`). Dev DB is SQLite (`db.sqlite3`); the MySQL block in `impactData/settings.py` is commented out and must be swapped in manually for production.

### Tests
`core/tests.py` is empty. The `test_*.py` files in the repo root are ad-hoc scripts that call `django.setup()` and run against the real dev database — run them as `python test_permissions_system.py`, not via `manage.py test`. Many data-repair commands live in `core/management/commands/` (`fix_*`, `clean_*`, `update_*`).

## Architecture

- **Custom user**: `AUTH_USER_MODEL = 'core.User'` with a `role` field (`admin`, `superviseur`, `agent`; superusers bypass everything). Superviseurs manage agents; data visibility is scoped by role (see `can_access_data` in `core/views.py`).
- **Dynamic permissions**: authorization is DB-driven, not Django's built-in perms. `RolePermission(role, permission, is_active)` rows define codes like `adherent_create`, `user_view`, `badge_revoke` (full list in `RolePermission.PERMISSION_CHOICES`). Enforce via `has_permission(user, code)`, the `@require_permission(code)` decorator, or `PermissionRequiredMixin.permission_required` on CBVs — all defined at the top of `core/views.py`. Adding a new permission requires adding the choice and re-running `initialize_permissions`.
- **Reference values**: dropdown options (statuses, profession types, languages, etc.) are `ReferenceValue` rows managed in the Settings UI rather than hardcoded choices; forms in `core/forms.py` and `core/widgets.py` (searchable select) load them from the DB. `GeneralParameter` holds app-wide settings; `SystemLog`/`UserActionLog` audit actions.
- **Objectives**: `UserObjective` progress is recomputed by `post_save`/`post_delete` signals on Organization, Adherent and Interaction in `core/models.py` (~line 1330). Bulk-creating via `bulk_create` or `.update()` bypasses these.
- **Badges**: `Badge` model + `BadgeTemplate`-style customization (see `BADGE_MANAGEMENT.md`, `BADGE_FIELDS_INTEGRATION.md`); generation logic in `core/services.py` and badge views.
- **Public registration** (in-progress on branch `feature/adherent-public-registration`): unauthenticated `inscription/<organization_id>/` (`public_adherent_register`) creates an `AdherentRegistrationRequest` (status pending/approved/rejected); supervisors/admins review them in `core/templates/core/adherents/registration_request_*.html`. The `core.context_processors.pending_registration_count` context processor feeds the nav badge in `base.html`. The optional profile photo on this unauthenticated form is guarded by `core/uploads.py`: size/format/pixel checks plus Pillow re-encoding to JPEG, per-IP rate limit (5 POSTs/hour, Django cache, `REMOTE_ADDR` only), and storage in `PRIVATE_MEDIA_ROOT` (outside `/media/`), served only through the permission-protected `adherent_registration_photo` view. The photo is copied to `Adherent.profile_picture` on approval and deleted on rejection. Keep any new public upload behind the same helpers.
- **Layout**: almost all logic is in the large `core/views.py` (~4000 lines, function- and class-based views mixed) and `core/models.py`; routes in `core/urls.py` (`app_name = 'core'`), templates under `core/templates/core/<feature>/`.

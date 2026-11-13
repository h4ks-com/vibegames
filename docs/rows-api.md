# Rows API — user data for vibed games

Every project is served from its own subdomain (`<project>.games.h4ks.com`). That gives the
platform two things for free: a trustworthy **app identity** (the subdomain) and a
**same-origin API path** with no CORS.

`/__api/rows` stores small JSON blobs, one namespace per `(app, user)`. There is no query
language, no schema registration and no server-side logic per game.

## Using it from a game

```html
<script>
  const api = "/__api"; // same origin as the game itself

  const me = await (await fetch(api + "/me")).json();
  if (!me.sub) {
    location.href = "https://games.h4ks.com/__auth/login?next=" + location.pathname;
  }

  // read everything this user stored in this app (they have at most 64 keys)
  const { rows } = await (await fetch(api + "/rows")).json();
  const save = rows.find(r => r.key === "save")?.value ?? { level: 1 };

  // write one row
  await fetch(api + "/rows/save", {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ value: { level: save.level + 1 } }),
  });
</script>
```

## Endpoints

| Method | Path | Auth | Body / result |
|---|---|---|---|
| `GET` | `/__api/me` | cookie | `{sub, username, name, picture}` |
| `GET` | `/__api/rows` | cookie | `{rows:[{key,value,public,bytes,updated_at}], usage:{keys,bytes,max_keys,max_bytes}}` |
| `GET` | `/__api/rows/{key}` | cookie | one row |
| `PUT` | `/__api/rows/{key}` | cookie | `{value:<any JSON>, public?:bool}` |
| `DELETE` | `/__api/rows/{key}` | cookie | `204` |
| `DELETE` | `/__api/rows` | cookie | `{deleted:n}` — hard-deletes everything for this user in this app |
| `GET` | `/__api/public?limit=50` | none | rows of this app that their authors marked `public`, newest first |

Errors are always `{"error": {"code": ..., "message": ...}}` with a stable code:
`login_required`, `bad_key`, `too_large`, `quota_exceeded`, `rate_limited`, `not_found`,
`cross_site`.

`updated_at` is a unix timestamp in seconds.

## Who the caller is

Both identities are resolved on the server, before the handler:

* **app** — the subdomain of the request's `Host`. No endpoint accepts an app id.
* **user** — the `vg_session` cookie, looked up in the `sessions` table. No endpoint accepts
  a user id.

There is therefore no request a client can send that says "act as another app" or "act as
another user". The cookie is `HttpOnly` (XSS cannot read it), `Secure`, `SameSite=Lax`
(cross-site writes do not carry it) and scoped to `BASE_DOMAIN`, so one login covers every
project subdomain.

## Limits

| Limit | Value | Setting |
|---|---|---|
| Value size | 8 KiB | `OBBY_MAX_VALUE_BYTES` |
| Keys per user per app | 64 | `OBBY_MAX_KEYS` |
| Bytes per user per app | 128 KiB | `OBBY_MAX_BYTES` |
| Public rows per app | 5000 | `OBBY_MAX_PUBLIC_ROWS` |
| Writes per user per minute | 60 | `OBBY_WRITES_PER_MINUTE` |
| Key format | `^[a-zA-Z0-9_.:-]{1,64}$` | — |

## What "private" means here

Being precise, because it is easy to over-promise:

* **private rows are only ever returned to their owner.** No endpoint lists another user's
  private rows; `GET /__api/rows` is scoped by the session, and `GET /__api/public` filters
  on `public = true`. Other games cannot read them either — the query always includes the
  app from the subdomain.
* **`public: true` is opt-in at write time** and is visible to anyone who can reach the app's
  subdomain, logged in or not. It exists for feeds and leaderboards. Do not put secrets in a
  public row.
* **at rest the data is plaintext** in the SQLite file. Someone with database access (the
  operator) can read it. We do not claim otherwise.
* **deletion is a hard delete**: `DELETE /__api/rows` removes the user's rows in that app
  immediately. There is no backup retention policy yet.

If we ever need "not even the operator can read it", that requires client-side encryption in
 the game, which this API does not attempt.

## Configuration

```
LOGTO_ISSUER=https://auth.h4ks.com/oidc
LOGTO_CLIENT_ID=...
LOGTO_CLIENT_SECRET=...
LOGTO_REDIRECT_URI=https://games.h4ks.com/__auth/callback
SESSION_COOKIE_DOMAIN=games.h4ks.com
SESSION_TTL_DAYS=30
OBBY_ENABLED=true
```

Leave `LOGTO_CLIENT_ID` empty to disable login entirely (`/__auth/login` answers `503`) —
the rest of the platform keeps working.

## Tests

```sh
cd api
poetry run pytest
```

The suite drives the real login redirects against a fake identity provider (no network) and
covers isolation between users and between apps, quotas, the public feed and CSRF handling.

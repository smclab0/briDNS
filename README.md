# briDNS

A web console for managing a BIND 9 DNS server, packaged with Docker.

**Status: mockup.** Sign-in is real. The console pages use sample data and don't talk to BIND yet. The BIND container is real and serves the zones in `bind/zones/`.

## Run

```bash
# one-time: set the admin password
cp .env.example .env   # then edit BRIDNS_ADMIN_PASSWORD and BRIDNS_SECRET

# one-time: generate the rndc control key
docker compose build bind
docker compose run --rm --no-deps -T bind tsig-keygen rndc-key > bind/config/rndc.key

docker compose up -d --build
```

- Web console: http://localhost:8088 (sign in as `admin`)
- DNS: `dig @127.0.0.1 -p 5353 nas.home.lan`

DNS is published on host port 5353 so it doesn't clash with a local resolver. Change it to `53:53` in `docker-compose.yml` when the machine should act as the network's DNS server.

The `:Z` on the volumes relabels them for SELinux. Remove it on hosts without SELinux.

## Sign-in

The `api` container checks the username and password from `.env` and sets a signed session cookie (HttpOnly, SameSite=Strict, 8 hours by default). nginx asks the API about every console request and sends anyone without a valid session to `/login`.

- Five wrong passwords from one IP lock sign-in for 60 seconds.
- Set `BRIDNS_SECRET`, or everyone is signed out whenever the api container restarts.
- Set `BRIDNS_COOKIE_SECURE=true` once briDNS is behind HTTPS.
- Sign out removes the cookie from the browser. A copied cookie stays valid until it expires; server-side session revocation is still to do.

## Layout

| Path | What it is |
|---|---|
| `docker-compose.yml` | `bind` (Alpine + BIND 9.18), `web` (nginx Alpine) and `api` (Python Alpine) services |
| `.env.example` | admin user, password and session settings; copy to `.env` |
| `api/app.py` | sign-in API (Python standard library only) |
| `bind/Dockerfile` | Alpine 3.20 image with `bind` and `bind-tools` |
| `bind/config/` | `named.conf`, `named.conf.options`, `rndc.key` → `/etc/bind` |
| `bind/zones/` | zone files → `/var/lib/bind` |
| `web/mockup.html` | the console UI (single file, vanilla JS) |
| `web/login.html` | the sign-in page |
| `web/nginx.conf` | serves the pages, protects the console, proxies `/api/` |

## Next steps

1. **Extend the API** (`bridns-api`): read/write zone files, validate with `named-checkzone`, bump the SOA serial, run `rndc reload`.
2. Wire the UI to the API in place of the sample data.
3. Audit log of who changed which record, more users, password change from the UI.

# briDNS

A web console for managing a BIND 9 DNS server, packaged with Docker.

**Status: mockup.** The web UI uses sample data and doesn't talk to BIND yet. The BIND container is real and serves the zones in `bind/zones/`.

## Run

```bash
# one-time: generate the rndc control key
docker run --rm --entrypoint tsig-keygen ubuntu/bind9:9.18-22.04_beta rndc-key > bind/config/rndc.key

docker compose up -d --build
```

- Web console: http://localhost:8088
- DNS: `dig @127.0.0.1 -p 5353 nas.home.lan`

DNS is published on host port 5353 so it doesn't clash with a local resolver. Change it to `53:53` in `docker-compose.yml` when the machine should act as the network's DNS server.

The `:Z` on the volumes relabels them for SELinux. Remove it on hosts without SELinux.

## Layout

| Path | What it is |
|---|---|
| `docker-compose.yml` | `bind` (ubuntu/bind9) + `web` (nginx) services |
| `bind/config/` | `named.conf`, `named.conf.options`, `rndc.key` → `/etc/bind` |
| `bind/zones/` | zone files → `/var/lib/bind` |
| `web/mockup.html` | the console UI (single file, vanilla JS) |

## Next steps

1. **API service** (`bridns-api`): reads/writes zone files, validates with `named-checkzone`, bumps the SOA serial, runs `rndc reload`.
2. Wire the UI to the API in place of the sample data.
3. Login, plus an audit log of who changed which record.

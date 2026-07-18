# Deployment: GitHub Pages + keeping consult-rah.com

## What I found

Looking up consult-rah.com's nameservers shows they're `ns0[1-4].squarespacedns.com` — the domain's DNS
is managed through Squarespace. That's true whether the domain is *registered* at Squarespace or just
using their nameservers. Either way, the path of least resistance is:

- Keep the domain where it is (no registrar transfer, no waiting periods, no transfer lock).
- Edit the DNS records in the Squarespace domains panel so they point at GitHub Pages instead of
  Squarespace's website builder.
- Cancel/downgrade only the Squarespace *website* subscription once the new site is confirmed working —
  domain registration and website hosting are billed and managed separately even though they're both
  "Squarespace."

A domain transfer is only worth it if you want DNS management off Squarespace entirely (e.g. onto
Cloudflare). Not necessary for this — skip it unless you want it later.

## 1. Create the GitHub repo

```bash
cd /path/to/consult-rah-site
git init
git add .
git commit -m "Initial site scaffold"
git branch -M main
```

Then on github.com: **New repository** → name it `consult-rah-site` (any name works — the custom domain
is what determines the public URL, not the repo name) → **Public** → do *not* initialize with a README
(you already have one) → Create repository.

```bash
git remote add origin https://github.com/rahmcrae/consult-rah-site.git
git push -u origin main
```

(Use SSH instead of HTTPS if that's your normal auth method.)

## 2. Enable GitHub Pages

In the repo: **Settings → Pages**
- Source: `Deploy from a branch`
- Branch: `main`, folder: `/ (root)`
- Save

Under **Custom domain**, enter `consult-rah.com` and save. GitHub will detect the `CNAME` file already
in the repo. Leave **Enforce HTTPS** unchecked for now — it won't be available until DNS is verified.

## 3. Point DNS at GitHub Pages (in Squarespace)

Squarespace → **Settings → Domains → consult-rah.com → DNS Settings** (wording may be "Use a domain you
already own" or "Advanced DNS" depending on which Squarespace panel you're in).

Add these records — **don't delete existing MX/email records** if you use email on this domain:

| Type | Host | Value | Notes |
|---|---|---|---|
| A | @ | 185.199.108.153 | GitHub Pages |
| A | @ | 185.199.109.153 | GitHub Pages |
| A | @ | 185.199.110.153 | GitHub Pages |
| A | @ | 185.199.111.153 | GitHub Pages |
| CNAME | www | rahmcrae.github.io | |

Remove or disable any existing A record / "Connect Squarespace domain to this website" toggle that
points the apex domain at Squarespace's own hosting — otherwise it'll conflict with the new A records.

## 4. Verify and wait

DNS changes typically propagate within minutes to a few hours (occasionally up to 48h). Check status:

```bash
dig +short A consult-rah.com
dig +short CNAME www.consult-rah.com
```

You should see the four GitHub IPs and `rahmcrae.github.io.` respectively. You can also check
https://dnschecker.org for global propagation.

Once GitHub sees the correct DNS, go back to **Settings → Pages** and check **Enforce HTTPS** — GitHub
issues a free TLS certificate automatically once it can validate the domain.

## 5. Clean up

Once consult-rah.com is confirmed loading the new site over HTTPS:
- Downgrade or cancel the Squarespace **website** plan (Settings → Billing) — you're only paying for
  domain registration/DNS now, which is usually far cheaper.
- Double check any Squarespace email service tied to this domain (e.g. Google Workspace via
  Squarespace) still has its MX records intact — those are untouched by the steps above, but worth a
  quick check before canceling anything.

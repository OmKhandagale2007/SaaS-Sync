# SyncLine

An interactive, 3D-styled prototype that simulates a no-code data sync pipeline between **Excel/Google Sheets → CRM → Invoicing** software. Built for SMEs who want to see how automated field mapping, contact deduplication, and invoice generation would work before wiring up real API credentials (e.g. in Make.com, Zapier, or n8n).

**[Live demo →](#deploying-with-github-pages)** (enable GitHub Pages — see below)

## What it does

- Load a sample sheet or upload your own CSV (`Customer Name, Email, Phone, Product, Amount, Due Date`)
- Click **Run sync** and watch data animate through three stages: Spreadsheet → CRM → Invoicing
- **Deduplicates contacts by email** — repeat customers update an existing CRM record instead of creating a duplicate
- **Filters invoices** — only generates an invoice when `Amount > 0`
- Tracks a simulated **Make.com-style operations counter** against the 1,000/month free tier
- Live sync log of every action taken
- Export the resulting invoice batch as a CSV

This is a self-contained front-end simulation — no backend, no real API calls, no data leaves the browser. It's meant as a working spec / demo you can point non-technical stakeholders to, or a starting point for wiring up real Make.com / Zapier / n8n scenarios and CRM & invoicing APIs.

## Tech

Single-file static site: plain HTML, CSS, and JavaScript.

- [PapaParse](https://www.papaparse.com/) (via CDN) for CSV parsing
- Google Fonts: Space Grotesk, Fraunces, JetBrains Mono
- No build step, no dependencies to install

## Running locally

Just open `index.html` in a browser. Or serve it locally:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Deploying with GitHub Pages

1. Push this repo to GitHub.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, set **Source** to `Deploy from a branch`, branch `main`, folder `/ (root)`.
4. Save — your site will be live at `https://<your-username>.github.io/<repo-name>/` within a minute or two.

## Customizing

Everything lives in `index.html`:

- Colors are defined as CSS variables at the top of the `<style>` block (`:root { ... }`) — change these to re-theme the whole site.
- Sample data is in the `SAMPLE` constant near the top of the `<script>` block.
- Sync logic (dedup, filtering, invoice numbering) lives in the `runSync()` function.

## License

MIT — see [LICENSE](LICENSE).

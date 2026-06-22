# Automated Ingestion via GitHub Actions

## Schedule

| Trigger | When | What runs |
|---|---|---|
| Weekdays (Mon–Fri) | 6:00 AM UTC | `fundamentals` + `analyst_targets` |
| Monthly | 2nd of month, 3 AM UTC | All 4 scripts (full refresh) |
| Manual | On-demand from GitHub UI | Your choice of step |

---

## Setup Steps

### 1. Push your code to GitHub
```bash
git add .
git commit -m "Add GitHub Actions ingestion workflow"
git push
```

### 2. Add Secrets to GitHub

Go to your repo → **Settings → Secrets and Variables → Actions → New repository secret**

Add these secrets:

| Secret Name | Value | Where to find |
|---|---|---|
| `TIDB_HOST` | `gateway01.ap-southeast-1.prod.aws.tidbcloud.com` | `.env.tidb` |
| `TIDB_PORT` | `4000` | `.env.tidb` |
| `TIDB_USER` | your TiDB username | `.env.tidb` |
| `TIDB_PASSWORD` | your TiDB password | `.env.tidb` |
| `TIDB_DB` | `stock_db` | `.env.tidb` |
| `TIDB_CA` | `.certs/isrgrootx1.pem` | `.env.tidb` |
| `TIDB_CA_CERT` | *(paste full contents of `.certs/isrgrootx1.pem`)* | your `.certs/` folder |

> ⚠️ `TIDB_CA_CERT` is the **file contents**, not the path.

### 3. Make sure `.env.tidb` and `.certs/` are in `.gitignore`
```
# in .gitignore
.env
.env.tidb
.certs/
```
This keeps credentials off GitHub — the workflow recreates them from Secrets at runtime.

### 4. Test it manually
Go to your repo → **Actions → Stock Data Ingestion → Run workflow**

Select step:
- `all` — runs everything
- `stocks` — only stock symbols
- `fundamentals` — only prices/PE/ROE etc.
- `quarterly` — only quarterly financials
- `analyst` — only analyst targets

---

## How it works

```
GitHub Actions runner (Ubuntu)
        │
        ├── checkout code
        ├── install requirements.txt
        ├── recreate .env.tidb from Secrets
        ├── recreate .certs/isrgrootx1.pem from Secret
        │
        ├── [weekdays]  ingest_fundamentals.py  ← prices change daily
        ├── [weekdays]  ingest_analyst_targets.py
        │
        ├── [2nd/month] ingest_stocks.py         ← new stocks rarely added
        ├── [2nd/month] ingest_fundamentals.py
        ├── [2nd/month] ingest_quarterly_financials.py
        ├── [2nd/month] ingest_analyst_targets.py
        │
        └── check_tidb.py  ← verify row counts after each run
```

---

## Cron Reference

```
┌─ minute (0-59)
│  ┌─ hour (0-23) UTC
│  │  ┌─ day of month (1-31)
│  │  │  ┌─ month (1-12)
│  │  │  │  ┌─ day of week (0=Sun, 5=Fri)
│  │  │  │  │
0  6  *  *  1-5    → 6 AM UTC, Mon–Fri
0  3  2  *  *      → 3 AM UTC, 2nd of every month
```

> UTC+5:30 (IST) = UTC + 5h 30m  
> So 6 AM UTC = **11:30 AM IST**  
> And 3 AM UTC = **8:30 AM IST**

---

## Costs

- GitHub Actions is **free** for public repos (unlimited minutes)
- For private repos: **2,000 free minutes/month** on the free plan
- Each ingestion run takes ~5–10 minutes → well within limits

---

## Troubleshooting

**Workflow not triggering on schedule?**
- GitHub may delay scheduled workflows by up to 15 minutes
- Schedules only run if the workflow file exists on the **default branch** (main/master)

**Authentication error?**
- Double-check secret names match exactly (case-sensitive)
- Re-paste the CA cert contents — make sure no trailing spaces

**Script fails for one stock but continues?**
- Each script handles per-stock errors gracefully and moves on
- Check the Actions log for `⚠️` warnings

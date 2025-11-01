# Lead Magnet Analyzer - Deployment Guide

This guide covers deploying Lead Magnet Analyzer for production use with viral growth features.

## Quick Start Options

### Option 1: Railway.app (Recommended - Easiest)

**Why Railway?**
- One-click deployment from GitHub
- Automatic HTTPS
- Auto-scaling
- $5/month to start
- No credit card needed for trial

**Steps:**

1. Push your code to GitHub

2. Go to [Railway.app](https://railway.app)

3. Click "Start a New Project" → "Deploy from GitHub repo"

4. Select your repository

5. Add environment variables:
   ```
   DATABASE_URL=sqlite:///./lead_magnet_analyzer.db
   API_KEY=your-secret-api-key-here
   ```

6. Railway will auto-detect the Dockerfile and deploy

7. Get your public URL (e.g., `your-app.railway.app`)

**That's it!** Your app is live in ~5 minutes.

---

### Option 2: Fly.io (Free tier available)

**Why Fly.io?**
- Free tier: 3 shared VMs
- Global CDN
- Good performance
- Easy CLI deployment

**Steps:**

1. Install Fly CLI:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. Login:
   ```bash
   fly auth login
   ```

3. Create app:
   ```bash
   fly launch
   ```
   - Choose app name
   - Select region (closest to your users)
   - Don't deploy yet

4. Set secrets:
   ```bash
   fly secrets set API_KEY=your-secret-key
   ```

5. Deploy:
   ```bash
   fly deploy
   ```

6. Open app:
   ```bash
   fly open
   ```

---

### Option 3: Docker + VPS (Most control)

**For:** DigitalOcean, AWS EC2, Linode, etc.

**Steps:**

1. SSH into your server

2. Install Docker:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

3. Clone repository:
   ```bash
   git clone https://github.com/yourusername/lead-magnet-analyzer.git
   cd lead-magnet-analyzer
   ```

4. Create `.env` file:
   ```bash
   echo "DATABASE_URL=sqlite:///./lead_magnet_analyzer.db" > .env
   echo "API_KEY=your-secret-key" >> .env
   ```

5. Build and run:
   ```bash
   docker-compose up -d
   ```

6. Set up Nginx reverse proxy (optional):
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

7. Get SSL with Let's Encrypt:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite:///./lead_magnet_analyzer.db` | Database connection string |
| `API_KEY` | No | `secret` | API key for authenticated endpoints |
| `PORT` | No | `8000` | Port to run the server on |

---

## Database Setup

### SQLite (Default - Good for <10K users)

No setup needed! SQLite database is created automatically on first run.

**Pros:**
- Zero configuration
- Works out of the box
- Good for MVP and testing

**Cons:**
- Single file (no horizontal scaling)
- Slower with high concurrency

### PostgreSQL (For scale)

When you hit 10K users or 100K analyses, migrate to PostgreSQL.

**Steps:**

1. Create PostgreSQL database (Railway/Heroku/AWS RDS)

2. Update `DATABASE_URL`:
   ```
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   ```

3. Restart app - tables will be created automatically

---

## Monitoring & Maintenance

### Health Check

The app exposes a health check endpoint:

```bash
curl https://your-domain.com/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-11-01T12:00:00"
}
```

### Logs

**Railway:**
```bash
# View logs in dashboard or CLI
railway logs
```

**Fly.io:**
```bash
fly logs
```

**Docker:**
```bash
docker-compose logs -f
```

### Backups

**SQLite:**
```bash
# Backup database
cp lead_magnet_analyzer.db lead_magnet_analyzer.backup.db

# Restore
cp lead_magnet_analyzer.backup.db lead_magnet_analyzer.db
```

**PostgreSQL:**
```bash
# Backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql
```

---

## Scaling Considerations

### Current Architecture (Phase 1)
```
┌──────────────┐
│   Railway    │
│   (1 VM)     │
│              │
│  FastAPI +   │
│  SQLite      │
└──────────────┘
```

**Handles:** 100-1,000 users

---

### Scaled Architecture (Phase 2 - At 10K users)
```
┌───────────────────┐
│  Load Balancer    │
└─────────┬─────────┘
          │
     ┌────┼────┐
     ▼    ▼    ▼
┌────────┐┌────────┐┌────────┐
│FastAPI ││FastAPI ││FastAPI │
└────┬───┘└────┬───┘└────┬───┘
     │         │         │
     └────────┬┼─────────┘
              ││
     ┌────────▼▼────────┐
     │   PostgreSQL     │
     └──────────────────┘
              │
     ┌────────▼─────────┐
     │   Redis Cache    │
     └──────────────────┘
```

**Handles:** 10K-100K users

---

## Cost Estimates

### Month 1 (0-1K users)

| Service | Cost |
|---------|------|
| Railway.app | $5 |
| Domain | $1 |
| **Total** | **$6/month** |

### Month 3 (1K-5K users)

| Service | Cost |
|---------|------|
| Railway Pro | $20 |
| PostgreSQL | $0 (Railway included) |
| Domain | $1 |
| **Total** | **$21/month** |

### Month 6 (10K+ users)

| Service | Cost |
|---------|------|
| AWS EC2 (3x t3.medium) | $100 |
| RDS PostgreSQL | $50 |
| ElastiCache Redis | $30 |
| S3 + CloudFront | $20 |
| **Total** | **$200/month** |

---

## Troubleshooting

### Issue: Playwright fails to launch browser

**Solution:**
```bash
# Ensure Playwright browsers are installed
playwright install chromium
playwright install-deps chromium
```

### Issue: Database locked errors

**Cause:** SQLite can't handle concurrent writes

**Solution:** Upgrade to PostgreSQL:
```bash
export DATABASE_URL=postgresql://user:pass@host/db
```

### Issue: Slow analysis (>60 seconds)

**Causes:**
- Target site is slow
- Network issues
- High server load

**Solutions:**
1. Increase timeout in `main.py`:
   ```python
   page.goto(current_url, timeout=30000)  # 30 seconds
   ```

2. Add retry logic for failed pages

3. Scale to multiple workers

### Issue: Running out of disk space

**Cause:** Result PNG files accumulating

**Solution:** Clean old files:
```bash
# Delete files older than 30 days
find results/ -name "*.png" -mtime +30 -delete
```

Or set up auto-cleanup in api.py:
```python
import os
from datetime import datetime, timedelta

def cleanup_old_files():
    threshold = datetime.now() - timedelta(days=30)
    for file in os.listdir("results"):
        filepath = os.path.join("results", file)
        if os.path.getmtime(filepath) < threshold.timestamp():
            os.remove(filepath)
```

---

## Security Checklist

Before going to production:

- [ ] Change default `API_KEY` from "secret" to strong random key
- [ ] Enable HTTPS (automatic with Railway/Fly.io)
- [ ] Set up rate limiting (add middleware in api.py)
- [ ] Configure CORS if needed
- [ ] Set up database backups
- [ ] Enable monitoring/alerts
- [ ] Review and set sensible timeout values
- [ ] Add input validation for all user inputs
- [ ] Set up error tracking (Sentry)

---

## Next Steps

After deployment:

1. **Test the full flow:**
   - Visit your landing page
   - Submit a URL for analysis
   - Wait for results
   - Share the report
   - Check database for records

2. **Set up analytics:**
   - Add Plausible/PostHog
   - Track key metrics:
     - Analyses per day
     - Share rate
     - Conversion rate (free → paid)

3. **Launch marketing:**
   - Submit to Product Hunt
   - Post on Reddit /r/marketing
   - Tweet about it
   - Reach out to influencers

4. **Monitor performance:**
   - Watch error rates
   - Check response times
   - Monitor database size
   - Track user growth

---

## Support

Need help deploying?

- Check our [GitHub Issues](https://github.com/yourusername/lead-magnet-analyzer/issues)
- Email: support@leadmagnetanalyzer.com
- Discord: [Join our community](#)

---

**Ready to launch?** Start with Railway.app - you'll be live in 5 minutes! 🚀

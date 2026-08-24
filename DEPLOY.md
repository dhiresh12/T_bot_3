# Xio PayPlus - Deployment Guide

## Prerequisites
- GitHub account
- Render account (https://render.com)
- Telegram bot token from @BotFather
- MongoDB database (MongoDB Atlas recommended)

## Step 1: Prepare Your Repository

1. Push all code to GitHub:
```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

## Step 2: Deploy on Render

### Option A: Using render.yaml (Recommended)

1. Go to https://render.com and sign up/login
2. Click "New" → "Blueprint"
3. Connect your GitHub repository: `dhiresh12/T_bot_3`
4. Render will automatically detect `render.yaml`
5. Click "Apply" to deploy

### Option B: Manual Deployment

1. Go to https://render.com and sign up/login
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Fill in the details:
   - **Name**: `xio-payplus`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn "app.mini_app:create_app()" --bind 0.0.0.0:$PORT --timeout 120`
   - **Plan**: Free

## Step 3: Set Environment Variables

In Render dashboard, go to your service → "Environment" tab and add:

| Variable | Value | Required |
|----------|-------|----------|
| `APP_ENV` | `production` | Yes |
| `SECRET_KEY` | Generate a secure random string (32+ chars) | Yes |
| `TELEGRAM_BOT_TOKEN` | Your bot token from @BotFather | Yes |
| `TELEGRAM_BOT_USERNAME` | Your bot username (e.g., `xiolis_bot`) | Yes |
| `ADMIN_KEY` | A secure admin key (keep this secret!) | Yes |
| `ADMIN_ID` | Your Telegram user ID (number) | Yes |
| `MONGO_URI` | Your MongoDB connection string | Yes |
| `MINI_APP_URL` | Your Render app URL (e.g., `https://xio-payplus.onrender.com`) | Yes |

### How to get these values:

**TELEGRAM_BOT_TOKEN:**
1. Open Telegram and search for @BotFather
2. Send `/newbot`
3. Follow instructions to create your bot
4. Copy the token (looks like: `123456789:ABCdef...`)

**ADMIN_ID:**
1. Search for @userinfobot in Telegram
2. Send `/start`
3. Copy your numeric user ID

**MONGO_URI:**
1. Go to https://www.mongodb.com/atlas/database
2. Create a free cluster
3. Get your connection string
4. Replace `<password>` with your database password

**SECRET_KEY:**
Generate a secure random string. You can use:
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

## Step 4: Deploy

1. Click "Create Web Service" or "Apply" if using Blueprint
2. Wait for deployment to complete (2-3 minutes)
3. Your app will be live at: `https://xio-payplus.onrender.com`

## Step 5: Configure Telegram Webhook

After deployment, set the webhook:

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://xio-payplus.onrender.com/webhook"
```

Or use the bot's `/setwebhook` command if available.

## Step 6: Test Your Bot

1. Open Telegram and search for your bot
2. Send `/start`
3. You should receive a welcome message with mini app button
4. Click the mini app button to test

## Troubleshooting

### Bot not responding?
- Check Render logs: Dashboard → Logs
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Verify webhook is set correctly
- Check `/health` endpoint: `https://xio-payplus.onrender.com/health`

### Mini app not loading?
- Verify `MINI_APP_URL` is set correctly
- Check that the URL is accessible publicly
- Verify `RENDER_EXTERNAL_URL` is set

### Database errors?
- Verify `MONGO_URI` is correct
- Check MongoDB Atlas network access (allow all IPs for testing)
- Verify database user has read/write permissions

### Admin panel not accessible?
- Verify `ADMIN_KEY` is set
- Access at: `https://xio-payplus.onrender.com/admin?admin_key=YOUR_KEY`

## Production Checklist

- [ ] Set all environment variables
- [ ] Deploy on Render
- [ ] Set Telegram webhook
- [ ] Test bot commands
- [ ] Test mini app
- [ ] Test admin panel
- [ ] Configure MongoDB backup
- [ ] Set up monitoring/alerts
- [ ] Test withdrawal flow
- [ ] Verify ad integration (if using real ads)

## Security Notes

1. **Never commit environment variables** to GitHub
2. **Use strong SECRET_KEY** and ADMIN_KEY
3. **Rotate keys regularly**
4. **Monitor logs** for suspicious activity
5. **Enable MongoDB authentication**
6. **Use HTTPS only** (Render provides this automatically)

## Scaling

Free tier limitations:
- 512 MB RAM
- Shared CPU
- 750 hours/month
- Spins down after 15 minutes of inactivity

For production, upgrade to:
- Starter plan ($7/month) - Always on
- Standard plan ($25/month) - More resources

## Support

If you encounter issues:
1. Check Render logs first
2. Verify all environment variables
3. Test locally before deploying
4. Check MongoDB connection
5. Verify Telegram bot token

---
**Note**: This is a production-ready configuration. Always test in a staging environment first.

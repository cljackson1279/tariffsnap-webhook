# TariffSnap Webhook - Quick Setup Guide (5 Minutes)

## What You're Setting Up

A Python server that automatically sends tariff reports when customers pay $149 via Stripe.

**Result:** Customer pays → Gets report in 30-60 seconds (completely automated)

---

## Prerequisites

You need 3 things:

1. ✅ Stripe account (you have this)
2. ✅ Gmail account (you have this: cljackson1279@gmail.com)
3. ✅ GitHub account (free - create at github.com if you don't have one)

---

## Step 1: Create Gmail App Password (2 minutes)

**Why:** So the server can send emails on your behalf

1. Go to: **https://myaccount.google.com/apppasswords**
2. You might need to sign in again
3. Click **"Select app"** → Choose **"Mail"**
4. Click **"Select device"** → Choose **"Other (Custom name)"**
5. Type: `TariffSnap`
6. Click **"Generate"**
7. **Copy the 16-character password** (looks like: `abcd efgh ijkl mnop`)
8. **Remove the spaces** → Final password: `abcdefghijklmnop`
9. **Save this password** - you'll need it in Step 4

---

## Step 2: Create Google Service Account (3 minutes)

**Why:** So the server can read your Google Sheet

1. Go to: **https://console.cloud.google.com/**
2. Click **"Select a project"** → **"New Project"**
3. Name it: `TariffSnap`
4. Click **"Create"**
5. Wait 10 seconds for project to be created
6. Click **"Enable APIs and Services"**
7. Search for: `Google Sheets API`
8. Click on it → Click **"Enable"**
9. Go to **"IAM & Admin"** (left sidebar) → **"Service Accounts"**
10. Click **"Create Service Account"**
11. Name: `tariffsnap-webhook`
12. Click **"Create and Continue"**
13. Skip role assignment → Click **"Continue"** → Click **"Done"**
14. Click on the service account you just created
15. Go to **"Keys"** tab
16. Click **"Add Key"** → **"Create new key"**
17. Select **"JSON"**
18. Click **"Create"**
19. **A JSON file will download** - save it!
20. **Copy the service account email** (looks like: `tariffsnap-webhook@tariffsnap-123456.iam.gserviceaccount.com`)

---

## Step 3: Share Google Sheet with Service Account (30 seconds)

1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/17t8iwdkzCdXBev13lRmERSH5v1OFaWUfFF8-5Ac8GTU/edit
2. Click **"Share"** (top right)
3. Paste the service account email (from Step 2, #20)
4. Change permission to **"Editor"**
5. **Uncheck** "Notify people"
6. Click **"Share"**

---

## Step 4: Deploy to Render.com (5 minutes)

1. Go to: **https://render.com/**
2. Click **"Get Started for Free"**
3. Sign up with GitHub (or email)
4. Once logged in, click **"New +"** → **"Web Service"**
5. Click **"Public Git repository"**
6. Paste this URL: `https://github.com/YOUR_USERNAME/tariffsnap-webhook`
   - **Wait!** You need to create this repository first (see Step 5 below)

---

## Step 5: Create GitHub Repository (2 minutes)

1. Go to: **https://github.com/new**
2. Repository name: `tariffsnap-webhook`
3. Description: `TariffSnap automated report delivery`
4. Select: **Public**
5. Click **"Create repository"**
6. You'll see instructions to push code
7. **I'll provide you with a ZIP file** - upload all files to this repository
8. Or use command line:

```bash
cd /path/to/tariffsnap-webhook
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/tariffsnap-webhook.git
git push -u origin main
```

---

## Step 6: Configure Render (3 minutes)

Back in Render:

1. Paste your GitHub repository URL
2. Click **"Connect"**
3. Configure:
   - **Name:** `tariffsnap-webhook`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`

4. **Add Environment Variables** (click "Advanced" → "Add Environment Variable"):

| Key | Value |
|-----|-------|
| `STRIPE_API_KEY` | Your Stripe secret key (starts with `sk_live_`) |
| `STRIPE_WEBHOOK_SECRET` | Leave blank for now (we'll add this in Step 7) |
| `GOOGLE_SHEET_ID` | `17t8iwdkzCdXBev13lRmERSH5v1OFaWUfFF8-5Ac8GTU` |
| `GMAIL_USER` | `cljackson1279@gmail.com` |
| `GMAIL_APP_PASSWORD` | The 16-char password from Step 1 (no spaces!) |
| `GOOGLE_CREDENTIALS_JSON` | Open the JSON file from Step 2, copy ENTIRE contents, paste here |

5. Click **"Create Web Service"**
6. Wait 2-3 minutes for deployment
7. **Copy your Render URL** (looks like: `https://tariffsnap-webhook.onrender.com`)

---

## Step 7: Configure Stripe Webhook (2 minutes)

1. Go to: **https://dashboard.stripe.com/webhooks**
2. Click **"Add endpoint"**
3. **Endpoint URL:** `https://your-render-url.onrender.com/webhook/stripe`
   - Replace `your-render-url` with your actual Render URL from Step 6
4. Click **"Select events"**
5. Search for and select: **`payment_intent.succeeded`**
6. Click **"Add events"**
7. Click **"Add endpoint"**
8. **Copy the "Signing secret"** (starts with `whsec_`)
9. Go back to Render dashboard
10. Click on your service → **"Environment"** tab
11. Find `STRIPE_WEBHOOK_SECRET` → Click **"Edit"**
12. Paste the signing secret
13. Click **"Save Changes"**
14. Your service will automatically restart

---

## ✅ Done! Test It

### Test 1: Health Check

1. Open: `https://your-render-url.onrender.com/`
2. You should see:
```json
{
  "status": "ok",
  "service": "TariffSnap Webhook Server",
  "version": "1.0.0"
}
```

### Test 2: Real Payment

1. Submit your Google Form
2. Make a test Stripe payment of $149
3. Check your email within 60 seconds
4. You should receive the tariff report!

---

## 🎉 You're Live!

Your automation is now running 24/7 for FREE. Every time someone pays $149 via Stripe, they'll automatically get their tariff report within 30-60 seconds.

**No more manual work!**

---

## Monitoring

**Check logs in Render:**
1. Go to Render dashboard
2. Click on your service
3. Click "Logs" tab
4. See real-time webhook events

**Check Stripe webhook events:**
1. Go to: https://dashboard.stripe.com/webhooks
2. Click on your endpoint
3. See all events and their delivery status

---

## Troubleshooting

**Email not sending?**
- Check `GMAIL_APP_PASSWORD` has no spaces
- Verify Gmail account allows app passwords
- Check Render logs for errors

**Webhook not working?**
- Verify Stripe webhook URL is correct
- Check `STRIPE_WEBHOOK_SECRET` matches Stripe
- Ensure Render service is running

**Google Sheets error?**
- Verify service account has Editor access
- Check `GOOGLE_CREDENTIALS_JSON` is valid
- Ensure sheet ID is correct

---

## Need Help?

Check the full README.md for detailed troubleshooting steps.

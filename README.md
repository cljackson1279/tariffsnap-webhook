# TariffSnap Webhook Server

Automatically sends tariff impact reports when customers pay via Stripe.

## Features

- ✅ **Instant delivery** - Reports sent within 30-60 seconds of payment
- ✅ **Stripe webhook integration** - Triggered automatically when payment succeeds
- ✅ **Google Sheets integration** - Pulls data from your Results tab
- ✅ **Professional email reports** - HTML formatted with tables and styling
- ✅ **Free hosting** - Deploy to Render.com free tier
- ✅ **Zero manual work** - Completely automated

## How It Works

1. Customer pays $149 via Stripe
2. Stripe sends webhook to this server
3. Server verifies payment amount
4. Server fetches data from Google Sheet "Results" tab
5. Server sends formatted email report to customer
6. Customer receives report in 30-60 seconds

## Deployment Instructions

### Step 1: Create Google Service Account

1. Go to: https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable Google Sheets API
4. Create Service Account:
   - Go to "IAM & Admin" → "Service Accounts"
   - Click "Create Service Account"
   - Name it: `tariffsnap-webhook`
   - Click "Create and Continue"
   - Skip role assignment
   - Click "Done"
5. Create JSON key:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key"
   - Select "JSON"
   - Download the JSON file
6. Share your Google Sheet with the service account email:
   - Open your Google Sheet
   - Click "Share"
   - Paste the service account email (looks like: `tariffsnap-webhook@project-id.iam.gserviceaccount.com`)
   - Give it "Editor" access

### Step 2: Get Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Other (Custom name)"
3. Name it: `TariffSnap Webhook`
4. Click "Generate"
5. Copy the 16-character password (no spaces)

### Step 3: Deploy to Render.com

1. Go to: https://render.com/
2. Sign up or log in
3. Click "New +" → "Web Service"
4. Connect your GitHub account (or use "Public Git repository")
5. If using GitHub:
   - Create a new repository
   - Push this code to the repository
   - Select the repository in Render
6. If using Public Git:
   - You'll need to push this code to a public Git repository first
7. Configure:
   - **Name:** `tariffsnap-webhook`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`
8. Add Environment Variables:
   - `STRIPE_WEBHOOK_SECRET`: (get from Stripe dashboard)
   - `STRIPE_API_KEY`: (your Stripe secret key)
   - `GOOGLE_SHEET_ID`: `17t8iwdkzCdXBev13lRmERSH5v1OFaWUfFF8-5Ac8GTU`
   - `GMAIL_USER`: `cljackson1279@gmail.com`
   - `GMAIL_APP_PASSWORD`: (the 16-char password from Step 2)
   - `GOOGLE_CREDENTIALS_JSON`: (paste the entire contents of the JSON file from Step 1)
9. Click "Create Web Service"

### Step 4: Configure Stripe Webhook

1. Go to: https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. **Endpoint URL:** `https://your-render-url.onrender.com/webhook/stripe`
   - Replace `your-render-url` with your actual Render URL
4. **Events to send:** Select `payment_intent.succeeded`
5. Click "Add endpoint"
6. Copy the "Signing secret" (starts with `whsec_`)
7. Go back to Render dashboard
8. Update the `STRIPE_WEBHOOK_SECRET` environment variable with this secret
9. Restart your Render service

## Testing

### Test the webhook server:

```bash
curl https://your-render-url.onrender.com/
```

You should see:
```json
{
  "status": "ok",
  "service": "TariffSnap Webhook Server",
  "version": "1.0.0"
}
```

### Test with a real payment:

1. Submit your Google Form
2. Make a test Stripe payment of $149
3. Check your email within 60 seconds
4. You should receive the tariff report

## Monitoring

### Check logs in Render:

1. Go to your Render dashboard
2. Click on your service
3. Go to "Logs" tab
4. You'll see real-time logs of webhook events

### Check Stripe webhook events:

1. Go to: https://dashboard.stripe.com/webhooks
2. Click on your webhook endpoint
3. You'll see all events and their status

## Troubleshooting

### Email not sending:

- Check that `GMAIL_APP_PASSWORD` is correct (16 characters, no spaces)
- Verify `GMAIL_USER` matches your Gmail address
- Check Render logs for error messages

### Webhook not receiving events:

- Verify Stripe webhook URL is correct
- Check that `STRIPE_WEBHOOK_SECRET` matches Stripe dashboard
- Ensure Render service is running (not sleeping)

### Google Sheets not accessible:

- Verify service account email has Editor access to the sheet
- Check that `GOOGLE_CREDENTIALS_JSON` is valid JSON
- Ensure `GOOGLE_SHEET_ID` is correct

## Cost

**100% FREE** for your volume:

- Render.com free tier: 750 hours/month (always-on)
- Google Sheets API: Free for < 60 requests/minute
- Gmail SMTP: Free for < 500 emails/day
- Stripe webhooks: Free

## Support

If something isn't working:
1. Check Render logs for error messages
2. Verify all environment variables are set correctly
3. Test each component individually
4. Check Stripe webhook delivery status

## Security

- All sensitive data is stored in environment variables
- Stripe webhook signatures are verified
- Google service account has minimal permissions
- No data is stored on the server

## License

MIT

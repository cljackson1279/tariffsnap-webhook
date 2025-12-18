#!/usr/bin/env python3
"""
TariffSnap Webhook Server
Automatically sends tariff reports when customers pay via Stripe
"""

import os
import json
import logging
from flask import Flask, request, jsonify
import stripe
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration from environment variables
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '17t8iwdkzCdXBev13lRmERSH5v1OFaWUfFF8-5Ac8GTU')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')

stripe.api_key = STRIPE_API_KEY


def get_google_sheet_data(customer_email=None):
    """Fetch data from Google Sheets, filtered by customer email if provided"""
    try:
        # Set up Google Sheets credentials
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']
        
        # Use service account credentials from environment
        creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        if creds_json:
            creds_dict = json.loads(creds_json)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            # Fallback to file-based credentials
            creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        
        client = gspread.authorize(creds)
        
        # Open the Google Sheet
        sheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        # Strategy: The sheet should have a "Products" tab where each row is:
        # Email | Product | Old Cost | Tariff% | New Cost | Action
        # OR the Results tab should include an Email column
        
        # Try to get Products sheet first, fall back to Results
        try:
            products_worksheet = sheet.worksheet('Products')
            logger.info("Using 'Products' worksheet")
        except:
            # Fall back to Results tab
            products_worksheet = sheet.worksheet('Results')
            logger.info("Using 'Results' worksheet")
        
        # Get all records
        all_data = products_worksheet.get_all_records()
        
        if not customer_email:
            # No filter, return all
            logger.info(f"Fetched {len(all_data)} total rows (no email filter)")
            return all_data
        
        # Filter by customer email
        # Check if there's an Email column in the data
        if all_data and 'Email' in all_data[0]:
            # Filter rows where Email matches
            customer_data = [
                row for row in all_data 
                if row.get('Email', '').lower() == customer_email.lower()
            ]
            logger.info(f"Fetched {len(customer_data)} products for customer {customer_email}")
            return customer_data
        else:
            # No Email column - need different approach
            # Get Form Responses to find customer's timestamp
            logger.info("No Email column in products data, checking Form Responses")
            
            form_responses = sheet.worksheet('Form Responses 1')
            responses_data = form_responses.get_all_records()
            
            # Find customer's submission timestamp
            customer_timestamp = None
            for row in responses_data:
                if row.get('Email', '').lower() == customer_email.lower():
                    customer_timestamp = row.get('Timestamp')
                    logger.info(f"Found customer timestamp: {customer_timestamp}")
                    break
            
            if customer_timestamp:
                # Filter products by matching timestamp
                customer_data = [
                    row for row in all_data
                    if row.get('Timestamp') == customer_timestamp
                ]
                logger.info(f"Fetched {len(customer_data)} products for customer by timestamp")
                return customer_data
            else:
                # Customer not found, return empty
                logger.warning(f"Customer {customer_email} not found in Form Responses")
                return []
    
    except Exception as e:
        logger.error(f"Error fetching Google Sheet data: {str(e)}")
        return []


def send_email(to_email, store_name, results_data):
    """Send tariff report email to customer"""
    try:
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = 'Your TariffSnap Tariff Impact Report is Ready! 🎯'
        
        # Build email body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                h2 {{ color: #2563eb; border-bottom: 3px solid #2563eb; padding-bottom: 10px; }}
                h3 {{ color: #1e40af; margin-top: 30px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th {{ background-color: #2563eb; color: white; padding: 12px; text-align: left; }}
                td {{ padding: 10px; border: 1px solid #ddd; }}
                tr:nth-child(even) {{ background-color: #f3f4f6; }}
                .action-kill {{ color: #dc2626; font-weight: bold; }}
                .action-price {{ color: #f59e0b; font-weight: bold; }}
                .action-keep {{ color: #16a34a; font-weight: bold; }}
                .info-box {{ background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 30px 0; }}
                .highlight-box {{ background-color: #eff6ff; padding: 20px; border-left: 4px solid #2563eb; margin: 30px 0; }}
                .savings-box {{ background-color: #fef3c7; padding: 20px; border-radius: 8px; margin: 30px 0; }}
            </style>
        </head>
        <body>
            <h2>Your TariffSnap Tariff Impact Report 🎯</h2>
            
            <p>Hi there,</p>
            
            <p>Thanks for using TariffSnap! Here's your complete tariff impact analysis for <strong>{store_name or 'your store'}</strong>.</p>
            
            <h3>📊 Your Results:</h3>
            
            <table>
                <thead>
                    <tr>
                        <th>Product</th>
                        <th>Old Cost</th>
                        <th>Tariff %</th>
                        <th>New Cost</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add product rows
        for row in results_data:
            product = row.get('Product', 'N/A')
            old_cost = row.get('Old Cost', 'N/A')
            tariff = row.get('Tariff%', 'N/A')
            new_cost = row.get('New Cost', 'N/A')
            action = row.get('Action', 'N/A')
            
            # Style action based on value
            action_class = ''
            if 'KILL' in str(action).upper():
                action_class = 'action-kill'
            elif 'PRICE' in str(action).upper():
                action_class = 'action-price'
            elif 'KEEP' in str(action).upper():
                action_class = 'action-keep'
            
            html_body += f"""
                    <tr>
                        <td>{product}</td>
                        <td>${old_cost}</td>
                        <td>{tariff}%</td>
                        <td>${new_cost}</td>
                        <td class="{action_class}">{action}</td>
                    </tr>
            """
        
        html_body += """
                </tbody>
            </table>
            
            <div class="info-box">
                <h3>🎯 What These Actions Mean:</h3>
                
                <p><strong class="action-kill">🔴 KILL:</strong> Discontinue these products - margins too thin after tariffs</p>
                
                <p><strong class="action-price">🟡 PRICE UP:</strong> Increase prices to maintain profitability</p>
                
                <p><strong class="action-keep">🟢 KEEP:</strong> No action needed - margins still healthy</p>
            </div>
            
            <div class="highlight-box">
                <h3>💡 Next Steps:</h3>
                
                <ol>
                    <li>Review each product's recommended action</li>
                    <li>Calculate your potential savings by discontinuing "KILL" products</li>
                    <li>Adjust pricing for "PRICE UP" products to maintain margins</li>
                    <li>Focus marketing budget on "KEEP" products with healthy margins</li>
                </ol>
            </div>
            
            <div class="savings-box">
                <p style="margin: 0; font-size: 16px;">
                    <strong>💰 Estimated Annual Savings:</strong> Based on our analysis, stores like yours typically save <strong>$6,000+</strong> per year by implementing these recommendations.
                </p>
            </div>
            
            <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
            
            <p style="font-size: 14px; color: #666;">
                <strong>Questions?</strong> Reply to this email and we'll help you interpret your results.
            </p>
            
            <p style="font-size: 14px; color: #666;">
                Best regards,<br>
                <strong>The TariffSnap Team</strong>
            </p>
            
            <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #999; text-align: center;">
                <p>TariffSnap - Tariff Impact Analysis for E-commerce Sellers</p>
                <p>This report was generated on """ + datetime.now().strftime('%B %d, %Y at %I:%M %p') + """</p>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML body
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email via Gmail SMTP
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False


@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'TariffSnap Webhook Server',
        'version': '1.0.0'
    })


@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        
        logger.info(f"Received Stripe event: {event['type']}")
        
        # Handle payment_intent.succeeded event
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            
            # Check if payment is $59 (5900 cents) - End-of-Year Sale
            amount = payment_intent.get('amount', 0)
            if amount != 5900:
                logger.warning(f"Payment amount {amount} does not match expected 5900")
                return jsonify({'status': 'ignored', 'reason': 'amount_mismatch'}), 200
            
            # Get customer email from payment intent
            customer_email = payment_intent.get('receipt_email')
            
            # If no receipt email, try to get from customer object
            if not customer_email:
                customer_id = payment_intent.get('customer')
                if customer_id:
                    customer = stripe.Customer.retrieve(customer_id)
                    customer_email = customer.get('email')
            
            if not customer_email:
                logger.error("No customer email found in payment intent")
                return jsonify({'status': 'error', 'reason': 'no_email'}), 400
            
            logger.info(f"Processing payment for {customer_email}")
            
            # Fetch Google Sheet data filtered by customer email
            results_data = get_google_sheet_data(customer_email)
            
            if not results_data:
                logger.error("No data found in Google Sheet")
                return jsonify({'status': 'error', 'reason': 'no_sheet_data'}), 500
            
            # Send email report
            store_name = payment_intent.get('description', '')
            success = send_email(customer_email, store_name, results_data)
            
            if success:
                return jsonify({'status': 'success', 'email_sent': True}), 200
            else:
                return jsonify({'status': 'error', 'reason': 'email_failed'}), 500
        
        # Return success for other event types
        return jsonify({'status': 'success', 'processed': False}), 200
    
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        return jsonify({'status': 'error', 'reason': 'invalid_signature'}), 400
    
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return jsonify({'status': 'error', 'reason': str(e)}), 500


if __name__ == '__main__':
    # Run Flask app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
from datetime import datetime

def send_daily_report(report_data: Dict):
    """
    Send daily analysis report via email
    """
    # Email configuration
    sender_email = "crypto.assistant@example.com"
    receiver_email = "user@example.com"  # Should be configurable
    
    # Create message
    msg = MIMEMultipart()
    msg['Subject'] = f"Crypto Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # Create HTML content
    html = f"""
    <html>
        <body>
            <h2>Crypto Analysis Report</h2>
            <h3>{report_data['crypto']} Analysis</h3>
            
            <h4>Price Analysis</h4>
            <p>Current Trend: {report_data['price_analysis']['trend']}</p>
            <p>Technical Indicators:</p>
            <ul>
                <li>SMA 20: {report_data['price_analysis']['indicators']['sma_20']}</li>
                <li>SMA 50: {report_data['price_analysis']['indicators']['sma_50']}</li>
                <li>RSI: {report_data['price_analysis']['indicators']['rsi']}</li>
            </ul>

            <h4>Sentiment Analysis</h4>
            <p>Overall Sentiment: {report_data['sentiment']['overall']}</p>
            <p>Sentiment Score: {report_data['sentiment']['score']}</p>
            
            <h4>Social Media Insights</h4>
            <p>Reddit Activity: {len(report_data['social_data']['reddit'])} posts</p>
            <p>Twitter Activity: {len(report_data['social_data']['twitter'])} tweets</p>
        </body>
    </html>
    """

    msg.attach(MIMEText(html, 'html'))

    # For demonstration, print the email content
    print("Email report generated:")
    print(msg.as_string())

    # In production, you would use actual SMTP server
    """
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, 'password')
        server.send_message(msg)
    """

def send_summary_mail(receiver_email, analytics):
    import os
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from dotenv import load_dotenv

    # Load environment variables from .env file
    load_dotenv()

    # ✅ Get values from environment variables
    sender = os.getenv("EMAIL_USER")
    app_password = os.getenv("EMAIL_PASS")

    # Check if they loaded correctly
    if not sender or not app_password:
        print("❌ Email or password not found in .env file!")
        return

    # Create the email
    message = MIMEMultipart("alternative")
    message["Subject"] = "📊 File Organizer Summary Report"
    message["From"] = "anjanajoy82@gmail.com"
    message["To"] = "anjanajoy82@gmail.com"

    # ✅ Correct key names from analytics
    total_size_mb = analytics.get("total_size_bytes", 0) / (1024 * 1024)
    total_files = analytics.get("total_files", 0)
    time_taken = analytics.get("time_taken_sec", 0)
    categories = analytics.get("categories", {})

    body = f"""
    ✅ File Organization Summary

    Total Files Organized: {total_files}
    Total Size: {total_size_mb:.2f} MB
    Time Taken: {time_taken:.2f} sec
    Categories:
    {chr(10).join(f"- {k}: {v}" for k, v in categories.items())}
    """

    message.attach(MIMEText(body, "plain"))

    # ✅ Send the email safely
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_password)
            server.send_message(message)
        print("📧 Email sent successfully!")
    except Exception as e:
        print("❌ Email failed:", e)

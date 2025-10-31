def send_summary_mail(receiver_email, analytics):
    import os
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage

    from dotenv import load_dotenv

    load_dotenv()
    sender = os.getenv("EMAIL_USER")
    app_password = os.getenv("EMAIL_PASS")

    message = MIMEMultipart("alternative")
    message["Subject"] = "📊 File Organizer Summary Report"
    message["From"] = sender
    message["To"] = receiver_email

    # ✅ Fix the wrong key names
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
    # ✅ Attach the analytics chart image
try:
    with open("analytics.png", "rb") as f:
        img_data = f.read()
        message.attach(MIMEImage(img_data, name="analytics.png"))
except FileNotFoundError:
    print("⚠️ analytics.png not found — skipping image attachment.")


    # Send mail
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, app_password)
        server.send_message(message)

    print("📧 Email sent successfully!")



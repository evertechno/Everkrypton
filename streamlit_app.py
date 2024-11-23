import streamlit as st
from email_validator import validate_email, EmailNotValidError
import dns.resolver
import smtplib
import socket
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import time
import os
import re
import random
import datetime
from typing import List

# Function to check email validity
def validate_email_address(email, blacklist, custom_sender="test@example.com"):
    """Enhanced email validation with DNS, SMTP, and blacklist checks."""
    try:
        validate_email(email)
    except EmailNotValidError as e:
        return email, "Invalid", f"Invalid syntax: {str(e)}"
    
    domain = email.split("@")[-1]
    if domain in blacklist:
        return email, "Blacklisted", "Domain is blacklisted."

    try:
        mx_records = dns.resolver.resolve(domain, "MX")
    except dns.resolver.NXDOMAIN:
        return email, "Invalid", "Domain does not exist."
    except dns.resolver.Timeout:
        return email, "Invalid", "DNS query timed out."
    except Exception as e:
        return email, "Invalid", f"DNS error: {str(e)}"

    try:
        mx_host = str(mx_records[0].exchange).rstrip(".")
        smtp = smtplib.SMTP(mx_host, timeout=10)
        smtp.helo()
        smtp.mail(custom_sender)
        code, _ = smtp.rcpt(email)
        smtp.quit()
        if code == 250:
            return email, "Valid", "Email exists and is reachable."
        elif code == 550:
            return email, "Invalid", "Mailbox does not exist."
        elif code == 451:
            return email, "Greylisted", "Temporary error, try again later."
        else:
            return email, "Invalid", f"SMTP response code {code}."
    except smtplib.SMTPConnectError:
        return email, "Invalid", "SMTP connection failed."
    except Exception as e:
        return email, "Invalid", f"SMTP error: {str(e)}"

    return email, "Invalid", "Unknown error."

# Function to generate random email addresses
def generate_random_email() -> str:
    domains = ["gmail.com", "yahoo.com", "outlook.com", "example.com", "test.com"]
    username = ''.join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=10))
    domain = random.choice(domains)
    return f"{username}@{domain}"

# Function to check the email format
def is_valid_email_format(email: str) -> bool:
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None

# Streamlit App
st.title("Inboxify by EverTech")

# Resource utilization stats - live update
cpu_metric = st.empty()
ram_metric = st.empty()
bandwidth_metric = st.empty()

# Blacklist upload
blacklist_file = st.file_uploader("Upload a blacklist file (optional)", type=["txt"])
blacklist = set()
if blacklist_file:
    blacklist = set(line.strip() for line in blacklist_file.read().decode("utf-8").splitlines())
    st.write(f"Loaded {len(blacklist)} blacklisted domains.")

# File upload
uploaded_file = st.file_uploader("Upload a .txt file with emails", type=["txt"])
if uploaded_file:
    emails = uploaded_file.read().decode("utf-8").splitlines()
    st.write(f"Processing {len(emails)} emails...")

    # Process emails in chunks
    chunk_size = 1000
    results = []
    progress = st.progress(0)

    with ThreadPoolExecutor(max_workers=20) as executor:
        for i in range(0, len(emails), chunk_size):
            chunk = emails[i:i + chunk_size]
            futures = [executor.submit(validate_email_address, email.strip(), blacklist) for email in chunk if email.strip()]
            for idx, future in enumerate(as_completed(futures)):
                results.append(future.result())
                if idx % 100 == 0:
                    progress.progress(len(results) / len(emails))

    # Display results
    df = pd.DataFrame(results, columns=["Email", "Status", "Message"])
    st.dataframe(df)

    # Summary report
    st.write("### Summary Report")
    st.write(f"Total Emails: {len(emails)}")
    for status in ["Valid", "Invalid", "Greylisted", "Blacklisted"]:
        count = df[df["Status"] == status].shape[0]
        st.write(f"{status} Emails: {count}")

    # Export results
    csv = df.to_csv(index=False)
    st.download_button("Download Results", data=csv, file_name="email_validation_results.csv", mime="text/csv")

# Live resource update every second
while True:
    # Get resource utilization stats
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    net_io = psutil.net_io_counters()
    bandwidth_usage = (net_io.bytes_sent + net_io.bytes_recv) / (1024 ** 2)  # in MB

    # Update live metrics on Streamlit app
    cpu_metric.metric("CPU Usage (%)", cpu_usage)
    ram_metric.metric("RAM Usage (%)", ram_usage)
    bandwidth_metric.metric("Bandwidth Usage (MB)", bandwidth_usage)

    # Wait before updating again
    time.sleep(1)

# Additional features
def system_info():
    """Returns system information like OS, CPU, RAM, Disk Space."""
    os_info = os.uname()
    cpu_count = psutil.cpu_count()
    disk_space = psutil.disk_usage('/')
    return f"OS: {os_info.system} {os_info.release}, CPU: {cpu_count} cores, Disk: {disk_space.percent}% used"

def get_current_time():
    """Returns the current time and date."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def random_email_statistics(emails: List[str]):
    """Generate statistics about random emails."""
    valid_count = sum(1 for email in emails if is_valid_email_format(email))
    invalid_count = len(emails) - valid_count
    return valid_count, invalid_count

# Display system info and current time
st.sidebar.write("### System Info")
st.sidebar.write(system_info())
st.sidebar.write(f"Current Time: {get_current_time()}")

# Display random email statistics
random_emails = [generate_random_email() for _ in range(100)]
valid_count, invalid_count = random_email_statistics(random_emails)
st.sidebar.write("### Random Email Statistics")
st.sidebar.write(f"Valid Emails: {valid_count}")
st.sidebar.write(f"Invalid Emails: {invalid_count}")

# End of the Streamlit app

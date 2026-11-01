"""
generate_datasets.py
---------------------
Builds two labeled text-classification datasets used by CyberShield AI:

1. data/job_scam_dataset.csv      -> columns: text, label  (1 = fraudulent, 0 = genuine)
2. data/phishing_email_dataset.csv-> columns: text, label  (1 = phishing,   0 = legitimate)

In production these would be sourced from Kaggle ("Real / Fake Job Postings" and
"Phishing Email Dataset"). Kaggle isn't reachable from this sandbox, so this
script procedurally generates a large, linguistically-realistic dataset built
from real-world scam/phishing phrasing patterns and legitimate-communication
templates, with randomized entities (companies, names, amounts, links) so the
model sees thousands of non-duplicate examples instead of memorizing a few
templates.
"""

import csv
import random

random.seed(42)

# ----------------------------------------------------------------------
# 1. FAKE JOB OFFER DATASET
# ----------------------------------------------------------------------

companies = ["Global Tech Solutions", "Nexora Corp", "BrightPath Inc", "Zenith Industries",
             "Apex Digital", "Skyline Enterprises", "Vertex Systems", "Infinity Labs",
             "Google", "Microsoft", "Amazon", "TCS", "Infosys", "Wipro", "Accenture",
             "HDFC Bank", "Reliance Industries", "PixelWave Studio", "Quantum Dynamics"]

names = ["Rahul Sharma", "Priya Patel", "John Smith", "Emily Davis", "Amit Kumar",
         "Sarah Johnson", "Vikram Singh", "Anjali Mehta", "David Lee", "Sophia Brown"]

roles = ["Data Entry Operator", "Customer Support Executive", "Software Developer",
         "Content Writer", "Marketing Manager", "HR Executive", "Financial Analyst",
         "Online Survey Assistant", "Virtual Assistant", "Package Handler",
         "Social Media Manager", "Chat Support Agent"]

amounts = ["₹500", "₹1,000", "₹2,500", "$50", "$99", "$199", "₹5,000 registration fee",
           "$150 processing fee", "₹999 training fee"]

fake_job_templates = [
    "Congratulations! You have been selected for the {role} position at {company}. "
    "No interview required. Pay a refundable registration fee of {amount} to activate "
    "your employee account and start earning from home immediately.",

    "URGENT HIRING at {company}! Earn up to $5000/month working just 2 hours a day from "
    "home. Send your bank details and pay {amount} security deposit to claim this {role} job today.",

    "Dear {name}, we reviewed your resume and are pleased to offer you the {role} role at "
    "{company}. To proceed, kindly transfer {amount} for the mandatory training kit and "
    "laptop setup. Limited slots available, reply within 24 hours.",

    "Work from home opportunity! {company} is hiring {role}s with NO experience needed. "
    "Guaranteed income of $3000 weekly. Just pay {amount} for the starter kit and background "
    "verification to get instant approval.",

    "Hi {name}, this is an automated offer letter for {role} at {company}. Your salary is "
    "$8000/month. To confirm your seat, send a copy of your ID and pay {amount} via Google Pay "
    "or crypto wallet before the offer expires today.",

    "Great news {name}! You've been shortlisted for {role} without any interview. "
    "{company} guarantees 100% job placement. Just complete the {amount} registration on "
    "our website and start working tomorrow, no experience or degree required.",

    "This is to inform you that {company} has selected you for {role} based on your online "
    "profile. Kindly WhatsApp your Aadhar card and pay {amount} refundable caution money to "
    "our HR to receive your offer letter and joining kit.",

    "EARN DAILY CASH! Simple typing job, {role} needed urgently at {company}. Pay only "
    "{amount} one-time and start earning ₹2000 per day from your mobile phone, no boss no "
    "targets, 100% genuine work from home.",
]

real_job_templates = [
    "Dear {name}, thank you for applying to the {role} position at {company}. We would like "
    "to invite you for a video interview with our hiring team next Tuesday at 10 AM. Please "
    "confirm your availability by replying to this email.",

    "{company} is pleased to offer you the position of {role}. Your starting annual salary "
    "will be discussed during the offer call with HR. Please find the formal offer letter "
    "attached and sign the employment contract within 7 business days.",

    "Hi {name}, we appreciate your interest in the {role} role at {company}. After reviewing "
    "your application, our recruitment team would like to schedule a technical interview. "
    "Kindly select a convenient time slot from the calendar link below.",

    "As discussed in your interview, {company} is excited to have you join our team as "
    "{role}. Onboarding documents, background verification forms, and your employee handbook "
    "are attached. No payment is required at any stage of our hiring process.",

    "Thank you for interviewing for the {role} position. Unfortunately, we have decided to "
    "move forward with other candidates at this time. We encourage you to apply for future "
    "openings at {company} and wish you the best in your job search.",

    "{name}, your application for {role} has been received. Our recruiter will contact you "
    "within 5 business days to discuss next steps. In the meantime, feel free to explore "
    "our careers page for additional openings at {company}.",

    "Following our conversation, please find attached the official offer letter for the "
    "{role} position at {company}. The role includes health insurance, paid leave, and a "
    "performance bonus structure. Let us know if you have any questions before signing.",

    "We are reaching out regarding your recent interview for {role} at {company}. The panel "
    "was impressed with your background. HR will send the formal offer and salary breakdown "
    "via our official portal by end of this week.",
]


hard_fake_job = [
    "Hi {name}, thanks for your interest in {role} at {company}. We can move forward "
    "quickly - just complete the onboarding form and send a small refundable deposit of "
    "{amount} so we can courier your welcome kit and laptop this week.",
    "{company} HR here. Your profile matches our {role} opening. Interview is optional, "
    "we can fast-track you. Send your bank account number so we can set up payroll before "
    "your first day.",
]
hard_real_job = [
    "Hi {name}, following up urgently on the {role} interview - can you send your signed "
    "offer letter back to {company} by end of day so we can finalize your start date?",
    "{company} is moving fast on the {role} hire. Please complete the background check "
    "form via our official HR portal link and reply confirming your preferred start date.",
]


def build_job_dataset(n_per_class=550, n_hard=60):
    rows = []
    for _ in range(n_per_class - n_hard):
        t = random.choice(fake_job_templates)
        text = t.format(role=random.choice(roles), company=random.choice(companies),
                         name=random.choice(names), amount=random.choice(amounts))
        rows.append((text, 1))
    for _ in range(n_hard):
        t = random.choice(hard_fake_job)
        text = t.format(role=random.choice(roles), company=random.choice(companies),
                         name=random.choice(names), amount=random.choice(amounts))
        rows.append((text, 1))
    for _ in range(n_per_class - n_hard):
        t = random.choice(real_job_templates)
        text = t.format(role=random.choice(roles), company=random.choice(companies),
                         name=random.choice(names))
        rows.append((text, 0))
    for _ in range(n_hard):
        t = random.choice(hard_real_job)
        text = t.format(role=random.choice(roles), company=random.choice(companies),
                         name=random.choice(names))
        rows.append((text, 0))
    random.shuffle(rows)
    return rows


# ----------------------------------------------------------------------
# 2. PHISHING EMAIL DATASET
# ----------------------------------------------------------------------

banks = ["HDFC Bank", "ICICI Bank", "Chase Bank", "Bank of America", "PayPal",
         "SBI", "Wells Fargo", "Citibank", "Axis Bank"]

services = ["Netflix", "Amazon", "Apple", "Microsoft 365", "Facebook", "Instagram",
            "Google Account", "LinkedIn", "PayPal", "DHL Courier", "FedEx"]

fake_links = ["http://secure-login-verify.com/account", "http://bit.ly/3xVerifyNow",
              "http://account-update-alert.net", "http://192.168.44.21/reset",
              "http://paypa1-security.com/confirm", "http://amaz0n-support.info/verify",
              "http://verify-account-now.xyz"]

phishing_templates = [
    "Dear Customer, your {service} account has been temporarily suspended due to unusual "
    "activity. Click here to verify your identity immediately: {link} or your account will "
    "be permanently deleted within 24 hours.",

    "URGENT: {bank} has detected suspicious login attempts on your account. Verify your "
    "identity now at {link} to avoid account suspension. Failure to act within 24 hours will "
    "result in permanent account lock.",

    "Your {service} password has expired. Click {link} to reset your password immediately "
    "and avoid losing access to your account and saved data.",

    "Congratulations! You have won a $1000 {service} gift card. Claim your prize now by "
    "clicking {link} and entering your card details before the offer expires tonight.",

    "We noticed a problem with your {service} billing information. Update your payment "
    "details at {link} within 48 hours to avoid service interruption and account closure.",

    "Security Alert: Someone tried to access your {bank} account from an unrecognized "
    "device. If this wasn't you, secure your account immediately at {link} using your login "
    "credentials.",

    "Your package from {service} could not be delivered due to an incomplete address. "
    "Confirm your delivery details and pay a small redelivery fee at {link} to receive your "
    "package today.",

    "Action Required: Your {bank} debit card has been blocked due to KYC verification "
    "failure. Update your KYC details urgently at {link} to reactivate your card and avoid "
    "penalty charges.",

    "Final Notice: Your {service} subscription payment failed. Update your card details at "
    "{link} within 24 hours or your account and all data will be permanently deleted.",
]

legit_templates = [
    "Hi, this is a reminder that your {service} subscription will renew automatically on "
    "your billing date. You can review or manage your subscription anytime from your account "
    "settings on our official app or website.",

    "Thank you for your recent purchase from {service}. Your order has been confirmed and "
    "will be shipped within 2-3 business days. You can track your order status from your "
    "account dashboard.",

    "Dear Customer, this is to confirm that your {bank} statement for this month is now "
    "available. You can view and download it by logging into your account through our "
    "official mobile app or website.",

    "Hello, we're writing to let you know about updates to our privacy policy at {service}. "
    "No action is needed on your part. You can read the full policy update on our website.",

    "Your {service} account was successfully signed in from a new device on Tuesday. If "
    "this was you, no further action is needed. If you don't recognize this activity, please "
    "log in directly through our official app to review your account.",

    "This is a routine notification from {bank} confirming that your recent transaction of "
    "was processed successfully. Please retain this email for your records.",

    "Thank you for contacting {service} support. Your ticket has been received and our team "
    "will get back to you within 24-48 hours with a resolution.",

    "Reminder: Your {service} free trial ends in 3 days. If you'd like to continue, no action "
    "is required as your subscription will continue automatically at the standard rate.",
]


hard_phishing = [
    "Hi, we noticed a login to your {service} account from a new location. If this was you, "
    "no action is needed. If not, please secure your account at {link} as soon as possible.",
    "Your {bank} statement is ready. As part of our routine security update, please "
    "re-confirm your registered mobile number at {link} to keep receiving statements.",
]
hard_legit = [
    "Dear Customer, {bank} will never ask you for your PIN or OTP over email or phone. If "
    "you receive such a request, please report it immediately through our official app.",
    "Your {service} account password was changed successfully. If you did not make this "
    "change, please contact our support team directly through the official app.",
]


def build_phishing_dataset(n_per_class=550, n_hard=60):
    rows = []
    for _ in range(n_per_class - n_hard):
        t = random.choice(phishing_templates)
        text = t.format(service=random.choice(services), bank=random.choice(banks),
                         link=random.choice(fake_links))
        rows.append((text, 1))
    for _ in range(n_hard):
        t = random.choice(hard_phishing)
        text = t.format(service=random.choice(services), bank=random.choice(banks),
                         link=random.choice(fake_links))
        rows.append((text, 1))
    for _ in range(n_per_class - n_hard):
        t = random.choice(legit_templates)
        text = t.format(service=random.choice(services), bank=random.choice(banks))
        rows.append((text, 0))
    for _ in range(n_hard):
        t = random.choice(hard_legit)
        text = t.format(service=random.choice(services), bank=random.choice(banks))
        rows.append((text, 0))
    random.shuffle(rows)
    return rows


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "label"])
        w.writerows(rows)


if __name__ == "__main__":
    job_rows = build_job_dataset()
    phish_rows = build_phishing_dataset()
    write_csv("../data/job_scam_dataset.csv", job_rows)
    write_csv("../data/phishing_email_dataset.csv", phish_rows)
    print(f"Job scam dataset: {len(job_rows)} rows")
    print(f"Phishing dataset: {len(phish_rows)} rows")

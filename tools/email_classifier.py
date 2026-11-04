#!/usr/bin/env python3
import json
import os
from datetime import datetime

# 模拟邮件数据集
MOCK_EMAILS = [
    {"id": "msg_001", "sender": "support@bank.com", "subject": "Security Alert: Login detected", "body": "A new login was detected on your account from a new IP address."},
    {"id": "msg_002", "sender": "news@techdaily.com", "subject": "Top 10 AI trends in 2024", "body": "Discover the latest breakthroughs in generative AI and LLMs..."},
    {"id": "msg_003", "sender": "noreply@amazon.com", "subject": "Your order has shipped", "body": "Great news! Your package is on its way and will arrive soon."},
    {"id": "msg_004", "sender": "marketing@fashionhub.com", "subject": "50% OFF EVERYTHING!", "body": "Don't miss out on our seasonal sale. Shop now for huge discounts!"},
    {"id": "msg_005", "sender": "hr@company.com", "subject": "Meeting Invitation: Q3 Planning", "body": "Please join the meeting to discuss our strategy for the next quarter."}
]

def classify_email(email):
    """模拟分类逻辑"""
    subject = email['subject'].lower()
    body = email['body'].lower()
    
    if any(word in subject or word in body for word in ['security', 'alert', 'login', 'bank']):
        return "transactional/security"
    elif any(word in subject or word in body for word in ['order', 'shipped', 'package']):
        return "transactional/shipping"
    elif any(word in subject or word in body for word in ['sale', 'off', 'discount', 'marketing']):
        return "promotional"
    elif any(word in subject or word in body for word in ['meeting', 'hr', 'planning']):
        return "internal/work"
    else:
        return "newsletter/general"

def main():
    # 确保输出目录存在
    output_dir = "data/output"
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    for email in MOCK_EMAILS:
        category = classify_email(email)
        results.append({
            "email_id": email["id"],
            "timestamp": datetime.now().isoformat(),
            "original_subject": email["subject"],
            "assigned_category": category
        })
    
    output_path = os.path.join(output_dir, "email_classification_results.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
    
    print(f"Classification complete. {len(results)} emails processed.")
    print(f"Results saved to: {output_path}")

if __name__ == "__main__":
    main()
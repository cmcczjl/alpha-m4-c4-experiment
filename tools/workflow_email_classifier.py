#!/usr/bin/env python3
"""
Email Subject Keyword Classifier
根据邮件主题中的关键词进行分类，输出 JSON 格式的结果。
"""

import json
import os
import sys
from typing import List, Dict, Any

# 定义分类规则：关键词列表 -> 分类标签
CLASSIFICATION_RULES: Dict[str, List[str]] = {
    "security": ["password reset", "suspicious activity", "security alert", "2fa", "verification code"],
    "finance": ["invoice", "payment", "billing", "refund", "transaction", "receipt"],
    "marketing": ["discount", "sale", "coupon", "limited offer", "newsletter", "special deal"],
    "technical": ["server down", "bug report", "error log", "maintenance", "system update", "crash"],
    "hr": ["interview", "resume", "candidate", "job offer", "performance review"]
}

def classify_email_subject(subject: str) -> Dict[str, Any]:
    """
    对邮件主题进行分类
    
    Args:
        subject: 邮件主题字符串
        
    Returns:
        包含分类标签和置信度的字典
    """
    if not subject or not isinstance(subject, str):
        return {
            "original_subject": subject,
            "category": "unknown",
            "confidence": 0.0,
            "matched_keywords": []
        }
    
    subject_lower = subject.lower()
    best_category = "unknown"
    best_confidence = 0.0
    all_matched_keywords = []
    
    for category, keywords in CLASSIFICATION_RULES.items():
        matched = []
        for keyword in keywords:
            if keyword in subject_lower:
                matched.append(keyword)
        
        if matched:
            all_matched_keywords.extend(matched)
            # 简单置信度计算：匹配关键词数量 / 该类别总关键词数量
            confidence = len(matched) / len(keywords)
            if confidence > best_confidence:
                best_confidence = confidence
                best_category = category
    
    # 如果多个类别置信度相同，选择第一个出现的（或保持 unknown）
    return {
        "original_subject": subject,
        "category": best_category,
        "confidence": round(best_confidence, 2),
        "matched_keywords": list(set(all_matched_keywords))
    }

def classify_multiple_subjects(subjects: List[str]) -> List[Dict[str, Any]]:
    """
    批量分类多个邮件主题
    
    Args:
        subjects: 邮件主题列表
        
    Returns:
        分类结果列表
    """
    return [classify_email_subject(s) for s in subjects]

def main():
    """
    主函数：从命令行参数或标准输入读取邮件主题，输出 JSON 结果
    """
    # 测试数据
    test_subjects = [
        "Your password has been reset",
        "Invoice #12345 for your recent purchase",
        "50% off sale - Limited time only!",
        "Server maintenance scheduled for tonight",
        "Interview invitation for Senior Engineer position",
        "New product newsletter: What's coming in 2024"
    ]
    
    results = classify_multiple_subjects(test_subjects)
    
    # 输出 JSON 格式
    print(json.dumps({
        "total_classified": len(results),
        "results": results
    }, indent=2, ensure_ascii=False))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
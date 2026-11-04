import json
import re

class EmailClassifier:
    """
    邮件分类器工作流模板
    功能：根据预设规则和关键词对邮件内容进行分类（工作、个人、广告、验证码）
    """
    def __init__(self):
        self.categories = {
            "WORK": ["meeting", "project", "deadline", "report", "client", "update"],
            "PERSONAL": ["family", "friend", "vacation", "hobby"],
            "PROMOTION": ["sale", "discount", "offer", "limited time", "buy now"],
            "VERIFICATION": ["code", "otp", "verification", "secret"]
        }

    def classify(self, subject, body):
        text = f"{subject} {body}".lower()
        scores = {cat: 0 for cat in self.categories}
        
        # 1. 关键词匹配得分
        for cat, keywords in self.categories.items():
            for kw in keywords:
                if kw in text:
                    scores[cat] += 1
        
        # 2. 特殊规则：验证码提取逻辑（模拟 extract_code 核心能力）
        # 匹配 4-8 位数字
        if re.search(r'\b\d{4,8}\b', text):
            scores["VERIFICATION"] += 2

        # 找到最高分的分类
        best_cat = max(scores, key=scores.get)
        
        # 如果得分都为0，归类为 UNKNOWN
        if scores[best_cat] == 0:
            best_cat = "UNKNOWN"
            
        return {
            "category": best_cat,
            "confidence": min(scores[best_cat] / 3.0, 1.0) if best_cat != "UNKNOWN" else 0.0,
            "scores": scores
        }

def run_template_test():
    """验证脚本"""
    classifier = EmailClassifier()
    
    test_cases = [
        {
            "name": "工作邮件",
            "subject": "Project Update",
            "body": "Please review the latest report before the deadline.",
            "expected": "WORK"
        },
        {
            "name": "验证码邮件",
            "subject": "Your login code",
            "body": "Your verification code is 123456. Do not share it.",
            "expected": "VERIFICATION"
        },
        {
            "name": "广告邮件",
            "subject": "Big Sale!",
            "body": "Get 50% discount on all items. Limited time offer!",
            "expected": "PROMOTION"
        },
        {
            "name": "未知邮件",
            "subject": "Hello",
            "body": "Just saying hi.",
            "expected": "UNKNOWN"
        }
    ]

    print(f"--- Starting Email Classifier Template Validation ---")
    success_count = 0
    for case in test_cases:
        result = classifier.classify(case["subject"], case["body"])
        passed = result["category"] == case["expected"]
        status = "PASS" if passed else "FAIL"
        if passed: success_count += 1
        
        print(f"[{status}] Case: {case['name']}")
        print(f"      Input: {case['subject']}")
        print(f"      Result: {result['category']} (Conf: {result['confidence']:.2f})")
        print(f"      Expected: {case['expected']}")
        print("-" * 40)

    print(f"Summary: {success_count}/{len(test_cases)} passed.")
    if success_count != len(test_cases):
        exit(1)

if __name__ == "__main__":
    run_template_test()
#!/usr/bin/env python3
import pathlib

# Paths
root = pathlib.Path(__file__).resolve().parents[1]
pricing_path = root / "data" / "pricing.md"
readme_path = root / "README.md"
output_path = root / "index.html"

# Helper to convert markdown headings to simple HTML sections
def md_to_html(md_text: str) -> str:
    lines = md_text.splitlines()
    html_lines = []
    for line in lines:
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:].strip()}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith("# "):
            html_lines.append(f"<h1>{line[2:].strip()}</h1>")
        else:
            html_lines.append(f"<p>{line.strip()}</p>")
    return "\n".join(html_lines)

# Load contents
pricing_md = pricing_path.read_text(encoding="utf-8") if pricing_path.exists() else ""
readme_md = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Build HTML
html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>获客 Landing Page</title>
    <style>
        body {{font-family: Arial, sans-serif; margin:0; padding:0;}}
        .container {{max-width: 960px; margin: auto; padding: 20px;}}
        .pricing {{display: flex; gap: 20px;}}
        .plan {{flex:1; border:1px solid #ddd; padding:15px; border-radius:5px;}}
        .plan h2 {{margin-top:0;}}
    </style>
</head>
<body>
<div class="container">
    <section id="problem">
        <h1>问题陈述</h1>
        {md_to_html(readme_md)}
    </section>

    <section id="solution">
        <h1>解决方案</h1>
        <p>基于已有的 M1‑M3 产出，提供以下三档定价方案，满足不同规模客户的需求。</p>
    </section>

    <section id="pricing" class="pricing">
        <h1>三档定价</h1>
        {md_to_html(pricing_md)}
    </section>

    <section id="commitment">
        <h1>验收承诺</h1>
        <p>我们承诺在交付后 30 天内完成所有验收工作，若不满意全额退款。</p>
    </section>
</div>
</body>
</html>
"""

output_path.write_text(html_content, encoding="utf-8")
print(f"Generated {output_path}")
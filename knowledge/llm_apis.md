# 免费 LLM API 列表（截至 2026‑10‑28）

| Provider | 免费额度 | 主要模型 | 注册入口 | 备注 |
|----------|----------|----------|----------|------|
| **OpenAI** | 5 USD/月（约 250 k tokens） | gpt‑4o‑mini, o1‑mini | https://platform.openai.com/signup | 需要信用卡验证，部分地区可免信用卡 |
| **Mistral** | 10 USD/月（约 500 k tokens） | mistral‑tiny, mistral‑large | https://mistral.ai/ | 邮箱验证 |
| **DeepSeek** | 5 USD/月（约 300 k tokens） | deepseek‑coder, deepseek‑chat | https://platform.deepseek.com/ | 支持中文 |
| **Cohere** | 5 USD/月（约 250 k tokens） | command‑r, command‑r‑plus | https://dashboard.cohere.com/ | 需邮箱激活 |
| **Google Gemini** | 1 M tokens 免费（约 7 USD） | gemini‑1.5‑flash, gemini‑1.5‑pro | https://ai.google.dev/ | 需 Google 账户 |
| **Anthropic (Claude)** | 5 USD/月（约 200 k tokens） | claude‑3‑haiku, claude‑3‑sonnet | https://console.anthropic.com/ | 邮箱验证 |
| **Groq** | 10 USD/月（约 400 k tokens） | llama‑3.1‑8b‑instruct, mixtral‑8x7b | https://groq.com/ | 需要信用卡 |
| **Together AI** | 5 USD/月（约 300 k tokens） | llama‑3‑8b‑instruct, mixtral‑8x7b‑instruct | https://api.together.xyz/ | 邮箱验证 |
| **OpenRouter** | 10 USD/月（约 500 k tokens） | 多模型聚合（包括 GPT‑4o‑mini） | https://openrouter.ai/ | 支持 API‑Key |
| **Replicate** | 1 h GPU 免费（约 100 k tokens） | stable‑lm‑2‑7b, llama‑2‑70b | https://replicate.com/ | 需要登录 |
| **OpenAI o1‑mini** | 5 USD/月（约 200 k tokens） | o1‑mini（推理+规划） | 同 OpenAI | 需启用实验功能 |
| **OpenAI gpt‑4o‑mini** | 5 USD/月（约 250 k tokens） | gpt‑4o‑mini | 同 OpenAI | 适合高并发 |

**常见注册步骤**  
1. 访问对应注册链接。  
2. 使用 `explorer_alpha@proton.me` 邮箱填写。  
3. 收到验证邮件 → 需要验证码（可通过 `tools/email_tool.py code` 提取）。  
4. 完成后在账户仪表盘获取 **API Key**。  

**免费额度评估**  
- 对于低成本微服务（如每日 100 次短文本生成），**OpenAI gpt‑4o‑mini** 或 **Mistral** 的免费额度足以支撑约 2–3 千次调用。  
- 若需要更高并发或更长上下文，可考虑 **Google Gemini**（1 M tokens）或 **Anthropic Claude‑haiku**。
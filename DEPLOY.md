# AGI 智能体 - 快速部署指南

## 当前状态

### ✅ 已完成
- AGI 智能体框架搭建在 `/root/agi-agent/`
- FREELLMAPI 服务器运行中（PID 1265778）
- 数据库有 285 个可用模型（Claude、Gemini、Qwen、GLM、DeepSeek 等）

### ⚠️ 需要配置

**FREELLMAPI 的 Provider Keys 未生效**

数据库中有一个 `electronhub` 平台的 key，但状态是 `invalid`。

## 解决方案

### 方案 1：添加有效的 Provider Key（推荐）

去 FREELLMAPI Dashboard 添加你的 API key：
```bash
# 方法 A: 通过 Web Dashboard
# 打开 http://你的服务器IP:3001 （需要先在服务器上暴露端口）

# 方法 B: 通过命令行
cd /root/freellmapi-server
npx freellmapi keys add --platform <平台名> --label "AGI Agent" --key <你的API Key>
```

支持的 provider 平台：
- `deepseek` - DeepSeek API
- `openai` - OpenAI API  
- `anthropic` - Claude API
- `google` - Gemini API
- `modelscope` - ModelScope（含 DeepSeek）
- `zhipu` - GLM API
- `aliyun` - Qwen API

### 方案 2：直接使用 DeepSeek API（如果有的话）

如果你有 DeepSeek API key，我可以直接对接：
```yaml
llm:
  api_base: "https://api.deepseek.com/v1"
  api_key: "你的 DeepSeek Key"
  model: "deepseek-chat"
```

### 方案 3：使用其他免费 LLM

我可以帮你配置其他免费的 LLM 服务（Google AI Studio、Together AI 等）。

## 你的选择？

请告诉我：
1. 你有哪个 LLM 的 API key？
2. 或者你想让我帮你配置哪个服务？
3. FREELLMAPI Dashboard 的访问地址是什么？

---

## 文件结构
```
/root/agi-agent/
├── agent.py           # 智能体核心
├── memory.py          # 记忆系统
├── freellm_llm.py     # FREELLMAPI 适配器
├── feishu_bot.py      # 飞书 Bot 适配器
├── config.yaml        # 配置文件 ← 需要更新
├── run.py             # 启动脚本
├── test_agent.py      # 测试脚本（Mock LLM）
└── data/              # 数据目录
    ├── agent.db       # SQLite 数据库
    ├── journal/       # 每日日记
    ├── lessons.json   # 失败教训
    └── knowledge/     # 知识库
```

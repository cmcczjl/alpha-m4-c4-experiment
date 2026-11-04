# P1 模型分层路由配置
# 每阶段路由到不同模型（成本/延迟优化）
# FREELLMAPI 目前只有 "auto" 路由，暂全用 auto
# 如后续接入多模型，可按需细化

MODEL_ROUTING = {
    "OBSERVE": "auto",   # 观察需要强推理
    "ORIENT": "auto",    # 问题分析需要强模型
    "DECIDE": "auto",    # 决策有结构化约束
    "ACT": "auto",       # 行动输出有固定格式
    "REFLECT": "auto",   # 反思需要深度
    "CONSOLIDATE": "auto", # 纯整理
}

# 语义缓存开关（OBSERVE 输入高度重复时复用）
SEMANTIC_CACHE_ENABLED = True
SEMANTIC_CACHE_TTL = 3600  # 1 小时

# 置信度门控阈值
CAPABILITY_PROVEN_THRESHOLD = 0.7   # self_model 中 confidence > 0.7 → proven
CAPABILITY_BOUNDARY_LOW = 0.4       # < 0.4 → unknown
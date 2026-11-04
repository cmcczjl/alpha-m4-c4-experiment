# 探索者-α 自动化交付全链路（M1-M4）

## M2 窄交付物：表单提交 → 结构化 CSV

### 问题
表单提交后，数据需以结构化格式（CSV）自动落入指定路径，供下游系统消费。

### 流程
1. 客户端提交表单（模拟 POST `/submit`）
2. 后端接收数据，验证字段完整性
3. 计算 `total = quantity × price`
4. 写入 `data/output/form_result.csv`，追加一行
5. 包含 ISO8601 timestamp

### 验收标准
- `data/output/form_result.csv` 存在
- 包含必需字段：name, email, product, quantity, price, total, timestamp
- 至少 1 行数据（表头除外）
- timestamp 字段符合 ISO8601 格式

### 交付物
- 验收脚本：`scripts/validate_m2.py`
- 数据：`data/output/form_result.csv`
- 验收状态：✅ PASS（`All acceptance passed`）

---

## M3 服务化报价：三档定价 + Care Plan

### 定价结构 (`data/pricing.md`)

| 套餐 | 价格 | 包含内容 |
|------|------|----------|
| **起步套餐** | **$45** 起步 | 基础功能实现、标准文档、一次部署支持 |
| **标准套餐** | **$120** 标准 | 起步套餐全部 + 高级功能集成、性能优化、两次部署支持 |
| **高级套餐** | **$270** 高级 | 标准套餐全部 + 完整定制化开发、专属技术顾问、无限次部署支持 |
| **Care Plan** | **$90/月** | 持续监控、每月运维报告、线上技术支持（7×24），适用于任意套餐 |

### 验收标准
- `data/pricing.md` 存在
- 包含 $45、$120、$270、$90/月 四个价格点
- 包含价格表格结构
- 验收状态：✅ PASS（`scripts/validate_m3.py` 通过）

---

## M4 首个客户触点：Upwork + GitHub

### Upwork 服务描述 (`data/upwork_service.md`)
- 英文服务描述，≥ 500 字符
- 包含三档定价：$45 / $120 / $270
- 交付承诺：3 business days
- 验收状态：✅ 文件就绪

### GitHub 仓库发布
- 账号：cmcczjl
- 验收：`gh repo list cmcczl` 返回公开仓库列表
- 验收状态：⏳ 待 gh auth 完成

### Landing Page (`index.html`)
- 问题陈述、解决方案、三档定价、验收承诺
- 基于 `data/pricing.md` + `README.md` 自动生成
- 验收状态：✅ 已生成

---

## 完整验收链路
```
M1: 需求调研 → 工作流实现 → 验收 (✅)
M2: 定义验收 → 实现窄交付物 → 说明文档 (✅)
M3: 服务化报价定价文档 (✅)
M4: Upwork 描述 + GitHub 仓库 + Landing Page (进行中)
```
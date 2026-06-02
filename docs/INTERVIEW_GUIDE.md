# SmartEye 面试演示指南

## 3 分钟演示流程

### [0:00-0:30] 打开质量检测页面
```yaml
操作: 打开 http://localhost:8501 → 切到 "📸 质量检测"
      → 选示例图片 "混合缺陷"
      → 确认 "启用 SAM 精细分割" 已勾选
      → 点击 "🔍 开始检测"

效果: 1-2 秒后显示标注图 (缺陷区有彩色 bbox + mask)
      下方显示缺陷明细表
      顶部显示判定横幅

你说: "这是 SmartEye——我用 LangGraph 做了 5 个 Agent 的编排系统。
        YOLO 做粗检，OpenCV 做精确测量，SAM 做像素级分割。"
```

### [0:30-1:00] 展示检测结果
```yaml
操作: 指着标注图上的缺陷框说明
      点击某个缺陷 → (如果交互模式实现了) SAM 分割

你说: "三引擎各有分工：YOLO 速度最快，负责 '哪里有嫌疑'；
       OpenCV 做 '有多严重'——比如这个焊点面积只有标准的 40%；
       SAM 给 '精确边界'——你看这个 mask 把桥接区域的轮廓精确画出来了。"
```

### [1:00-1:45] 切到 Agent 对话
```yaml
操作: 切到 "💬 Agent 对话"
      输入: "这批PCB的BGA焊点void率30%，IPC标准怎么说的？"
      发送

效果: Agent 通过 RAG 检索 IPC-A-610 标准
      返回准确阈值: Class 2 ≤25%, Class 3 ≤15%

你说: "Agent 自动调用了 RAG 知识库——查 IPC 标准、工厂 SOP、还有历史缺陷案例。
       右边 Agent Trace 可以实时看哪个 Agent 被触发、调了什么 Tool。
       这就是 JD 里说的 RAG 知识库系统。"
```

### [1:45-2:15] 展示前后端分离
```yaml
操作: 切到 "📋 质检报告" → 展示自动生成的报告
      打开新标签页: http://localhost:8000/docs
      → FastAPI 自动生成的 Swagger 文档

你说: "后端用了 FastAPI，OpenAPI 文档是自动生成的。
       前后端完全分离——Streamlit 只负责渲染，
       所有逻辑在 FastAPI 里，换 React 前端零成本。"
```

### [2:15-2:45] 展示架构思维
```yaml
你说: "整个架构的核心设计思想是——每一步都有 fallback。
       SAM 2.1 装不上？自动降级到 SAM 1 或 MobileSAM。
       YOLO 模型没训练？降级到预训练权重 + OpenCV 规则模式。
       Claude API 不可用？用规则路由兜底。
       这就是工程思维——不假设一切正常。"
```

### [2:45-3:00] 收尾
```yaml
你说: "这个项目我这周做的，覆盖了 JD 的每一个关键词——
       LangGraph 多 Agent 编排、LangChain Tool 封装、
       视觉大模型 SAM 2.1、RAG 知识库、Prompt Engineering。
       如果加入博世的苏州团队，我可以把这些技术直接用到
       Nexeed IAS 平台的 Shopfloor Management Agent 上。"

      然后: "你们目前在 Agent 编排方面用的是哪个框架？
            我看苏州工厂有 30 多个 AI 模型在跑，
            模型的版本管理和 A/B 测试怎么做的？"
      → 把面试变成讨论
```

## 常见提问 & 回答

### Q: 为什么选 LangGraph 而不是 CrewAI/AutoGen？
A: "LangGraph 的 StateGraph 模式更适合结构化工作流——质检是 '检测→分析→报告→告警' 的确定性流程，不是开放式对话。CrewAI 更偏对话式 Agent，对状态管理和流程控制的精细度不如 LangGraph。而且博世 JD 里写了 LangGraph。"

### Q: SAM 2.1 在 RTX 4060 上能跑吗？
A: "能跑。SAM 2.1 small 约 1.2GB 显存，加上 YOLO 和推理中间张量，峰值约 5GB——8GB 完全够。而且我做了显存管理——YOLO 常驻、SAM 按需加载，用信号量锁保证不会并发 OOM。"

### Q: RAG 为什么不直接用 langchain 的检索链？
A: "我拆开了——loader、vector_store、retriever 各自独立。好处是随时可以换 embedding 模型、换向量数据库、加 Rerank。langchain 的集成方案对 demo 来说太重了，自己写的 pipeline 更透明、更好调。"

### Q: 这些 PCB 图片是真实数据吗？
A: "目前示例图片是合成/公开数据集。在真实产线上部署的话，需要用工厂的历史 AOI 图像做微调。YOLO 的微调 pipeline 已经搭好了——换一批标注数据、跑一遍训练脚本就行。"

### Q: 你为什么对博世感兴趣？
A: "我看到博世苏州汽车电子工厂已经跑着类似的系统——30+ AI 模型、10+ Agent。而且这个方案反向输出到欧洲和北美工厂，是 '中国创新、服务全球' 的模式。我想参与这个——把 AI Agent 真正落地到制造业。"

## 面试前检查清单

- [ ] FastAPI 能正常启动 (http://localhost:8000/health)
- [ ] Streamlit 能正常启动 (http://localhost:8501)
- [ ] Swagger 文档可访问 (http://localhost:8000/docs)
- [ ] 质量检测页面上传图片能出结果
- [ ] Agent 对话页面能回答问题
- [ ] Agent Trace 能正确显示调用链路
- [ ] RAG 知识库已构建 (ChromaDB 目录存在)
- [ ] 仪表盘图表能正常渲染
- [ ] 报告页面能预览和下载
- [ ] 代码已推送到 GitHub (公开仓库)

## 面试结束后

- [ ] 发送感谢邮件
- [ ] 附上 GitHub 仓库链接
- [ ] 附上这篇 INTERVIEW_GUIDE 中你练熟的 3 分钟脱口内容

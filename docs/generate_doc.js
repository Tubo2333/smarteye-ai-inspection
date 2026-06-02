const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, LevelFormat,
  TableOfContents, HeadingLevel, BorderStyle, WidthType, ShadingType,
  PageNumber, PageBreak
} = require("docx");

// ═══════════════════════════════════════════
// Helper functions
// ═══════════════════════════════════════════

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };
const DXA_CONTENT = 9360; // US Letter with 1" margins

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text, bold: true })] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text, bold: true })] });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text, bold: true })] });
}
function para(text, opts = {}) {
  const runs = [];
  if (typeof text === "string") {
    runs.push(new TextRun({ text, ...opts }));
  } else if (Array.isArray(text)) {
    text.forEach(t => {
      if (typeof t === "string") runs.push(new TextRun({ text: t, ...opts }));
      else runs.push(new TextRun({ ...opts, ...t }));
    });
  }
  return new Paragraph({ children: runs, spacing: { after: 120 } });
}
function boldPara(label, text) {
  return new Paragraph({
    children: [
      new TextRun({ text: label, bold: true }),
      new TextRun({ text }),
    ],
    spacing: { after: 120 },
  });
}
function bullet(text, ref = "bullets") {
  const runs = [];
  if (typeof text === "string") {
    runs.push(new TextRun({ text, size: 22 }));
  } else if (Array.isArray(text)) {
    text.forEach(t => {
      if (typeof t === "string") runs.push(new TextRun({ text: t, size: 22 }));
      else runs.push(new TextRun({ size: 22, ...t }));
    });
  }
  return new Paragraph({ numbering: { reference: ref, level: 0 }, children: runs, spacing: { after: 60 } });
}
function numbered(text, ref = "numbers") {
  return new Paragraph({ numbering: { reference: ref, level: 0 }, children: [new TextRun({ text, size: 22 })], spacing: { after: 60 } });
}
function cell(text, opts = {}) {
  const { width, bold: b, shading } = opts;
  const runs = [new TextRun({ text, bold: b, size: 20 })];
  const cellOpts = { borders, margins: cellMargins, children: [new Paragraph({ children: runs })] };
  if (width) cellOpts.width = { size: width, type: WidthType.DXA };
  if (shading) cellOpts.shading = { fill: shading, type: ShadingType.CLEAR };
  return new TableCell(cellOpts);
}
function spacer() {
  return new Paragraph({ spacing: { after: 120 }, children: [] });
}

// ═══════════════════════════════════════════
// Document Content
// ═══════════════════════════════════════════

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, font: "Arial", color: "1A5276" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Arial", color: "2E86C1" },
        paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "3498DB" },
        paragraph: { spacing: { before: 180, after: 120 }, outlineLevel: 2 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [
    // ═══════════════════ TITLE PAGE ═══════════════════
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
        }
      },
      children: [
        spacer(), spacer(), spacer(), spacer(), spacer(), spacer(),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
          children: [new TextRun({ text: "SmartEye", size: 72, bold: true, color: "1A5276" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 },
          children: [new TextRun({ text: "汽车电子产线 AI 质检多 Agent 系统", size: 36, color: "2E86C1" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 },
          children: [new TextRun({ text: "白话说明文档 v1.0", size: 28, color: "888888" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
          children: [new TextRun({ text: "——让小白也能读懂 AI Agent 是怎么造出来的 ——", size: 24, italics: true, color: "999999" })] }),
        spacer(), spacer(), spacer(), spacer(),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
          children: [new TextRun({ text: "2026年6月", size: 24, color: "666666" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "目标岗位：博世中国 AI Agent 应用实习生", size: 22, color: "666666" })] }),
        new Paragraph({ children: [new PageBreak()] }),
      ]
    },

    // ═══════════════════ MAIN CONTENT ═══════════════════
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
        }
      },
      headers: {
        default: new Header({ children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "SmartEye 白话说明文档", size: 18, color: "999999", italics: true })]
        })] })
      },
      footers: {
        default: new Footer({ children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "第 ", size: 18, color: "999999" }),
                     new TextRun({ children: [PageNumber.CURRENT], size: 18, color: "999999" })]
        })] })
      },
      children: [
        // ═══════ TOC ═══════
        h1("目录"),
        new TableOfContents("目录", { hyperlink: true, headingStyleRange: "1-3" }),
        new Paragraph({ children: [new PageBreak()] }),

        // ═══════════════════ CHAPTER 1 ═══════════════════
        h1("第一章  项目概述 —— SmartEye 是什么？"),

        h2("1.1 一句话说清楚"),
        para("SmartEye 是一个用 AI 做工厂质检的软件系统。你给它一张电路板（PCB）的照片，它能自动找出上面的缺陷——哪里焊坏了、哪里元件歪了、哪里少了零件。找完之后，还能自动生成质检报告，告诉工厂的工程师该怎么修。"),

        h2("1.2 它解决什么问题？"),
        para("在博世这样的汽车零部件工厂里，每天有成千上万块电路板从生产线上下来。传统做法是：工人用显微镜或自动光学检测设备（AOI）看每一块板子，肉眼找缺陷。这有几个问题："),
        bullet("人有疲劳极限。连续看 4 小时后，检出率显著下降。"),
        bullet("标准不统一。不同工人对「这个焊点行不行」有不同判断。"),
        bullet("只知道有缺陷，不知道为什么。一个工人可能发现桥接变多了，但不会自动联想到「可能是印刷机的钢网该换了」。"),
        bullet("报告是手写的，没法分析趋势。"),

        para("SmartEye 就是来解决这些问题的。它把 AI Agent、计算机视觉和工厂知识库结合起来，让机器替人做质检——更快、更准、还能自动分析原因、生成报告。"),

        h2("1.3 对标博世什么？"),
        para("博世苏州汽车电子工厂已经有一个类似的系统：用了 30 多个 AI 模型和 10 多个智能 Agent 来做质量检测。他们的 Shopfloor Management AI Agent（产线管理智能助手）跑在 Nexeed IAS 平台上。SmartEye 就是用同样的技术路线做的一个个人 demo 版本——麻雀虽小，五脏俱全。"),

        h2("1.4 本文档的阅读指南"),
        para("这份文档是用大白话写的，目的是让你——不管有没有技术背景——都能理解 SmartEye 从头到尾是怎么设计的、为什么这么设计。"),
        bullet("如果你完全不懂技术：从第一章按顺序读，遇到不懂的词翻到最后的术语表。"),
        bullet("如果你有一些编程基础：重点看第二章（技术选型的理由）和第五章（Agent 怎么工作）。"),
        bullet("如果你是面试官：看第四章（完整工作流程）和第六章（为什么这套架构能落地）。"),

        new Paragraph({ children: [new PageBreak()] }),

        // ═══════════════════ CHAPTER 2 ═══════════════════
        h1("第二章  技术栈全解析 —— 每个技术名词是什么意思？为什么选它？"),

        para("这一章我用最土的方式解释项目中用到的每一个技术。每一个名词我都会回答三个问题：它是什么？它解决什么问题？我们为什么选它而不是别的？"),

        h2("2.1 AI Agent（智能体）"),
        boldPara("是什么？", "AI Agent 就是「有目标、能思考、会动手」的 AI。普通 AI 你问它一句它答一句。Agent 不一样——你给它一个目标（比如「检查这张电路板有没有缺陷」），它会自己想办法：先调用视觉工具做检测，然后分析检测结果，觉得有问题就查标准，最后写一份报告。整个过程不需要你一步步告诉它怎么做。"),
        boldPara("类比：", "普通 AI 像一个只会答题的学生。Agent 像一个能独立完成项目的小组长——你说「把这个项目做完」，他会自己安排步骤、分配任务、检查结果。"),
        boldPara("我们为什么用 Agent？", "质检不是一个简单的问答问题。它需要多个步骤：识别缺陷 → 测量严重度 → 查标准 → 判断是否告警 → 生成报告。Agent 恰好适合这种多步骤、需要调用不同工具的复杂任务。"),

        h2("2.2 LLM（大语言模型）"),
        boldPara("是什么？", "LLM 就是像 ChatGPT、Claude 这样的 AI 模型。它们读了几万亿字的文本，学会了理解语言、推理问题、写文章。"),
        boldPara("它在项目里的作用：", "LLM 是 Agent 的「大脑」。Agent 的所有决策——路由到哪个子 Agent、怎么分析检测结果、怎么写报告——都是 LLM 在做。"),
        boldPara("我们为什么选 Claude？", "Claude 在 Tool Use（调用工具）方面表现最好。我们项目的核心就是 Agent 调用各种工具（视觉检测、数据分析、报告生成），Claude 的这个能力是业内最强的。而且面试时提到 Anthropic 的 Claude 有加分——博世也在用。"),

        h2("2.3 LangChain 和 LangGraph"),
        boldPara("LangChain 是什么？", "一个 Python 库，让你方便地把 LLM 和各种工具、数据源连接起来。比如你可以写一句「当用户问天气时，调用天气 API」，LangChain 帮你把这个逻辑和 LLM 串起来。"),
        boldPara("LangGraph 是什么？", "LangChain 的升级版，专门用来编排多个 Agent 的协作流程。它用一个「图」（Graph）来定义 Agent 之间的调用关系——谁先执行、谁后执行、什么条件下跳到哪个 Agent。"),
        boldPara("类比：", "LangGraph 就像一个工厂的流水线设计图。每个工位（Agent）负责一件事，传送带（StateGraph 的边）把半成品从一个工位传到下一个。LangGraph 让你用代码画出这个「流水线」。"),
        boldPara("我们为什么选 LangGraph？", "博世的 JD 里明确写了 LangChain/LangGraph。而且 LangGraph 的 StateGraph 模式天然适合「检测→分析→报告→告警」这种多步骤质检流程。CrewAI 和 AutoGen 更偏向对话式 Agent，对结构化流程的支持不如 LangGraph。"),

        h2("2.4 YOLO（目标检测模型）"),
        boldPara("是什么？", "YOLO 的全称是 You Only Look Once（你只看一眼）。它是一种计算机视觉模型，能在图片里快速找到目标物体的位置和类别。比如给它一张 PCB 图片，它能标出「这里有个焊点」「这里有个元件」「这里有个划痕」。"),
        boldPara("为什么叫「只看一眼」？", "早期的目标检测方法要反复扫描图片，很慢。YOLO 的思路是一口气看完一整张图，一次就算出所有目标的位置——大幅提升了速度。"),
        boldPara("我们为什么选 YOLOv8？", "YOLOv8 是目前最主流的目标检测模型。我们用的是最小的版本 YOLOv8n——只有 320 万个参数（相当于一个非常精简的神经网络），在 RTX 4060 显卡上训练 30 分钟就能用，推理一张图只要几十毫秒。工业场景对速度要求很高——你不可能让产线等 5 秒才出结果。"),

        h2("2.5 OpenCV（计算机视觉库）"),
        boldPara("是什么？", "OpenCV 是一个开源计算机视觉库，里面包含了几乎所有传统图像处理的工具：边缘检测、颜色识别、轮廓提取、模板匹配……"),
        boldPara("YOLO 已经能找缺陷了，为什么还要 OpenCV？", "这就是本项目的设计亮点之一。YOLO 告诉你「这里有缺陷」，但它不告诉你「多严重」。比如它检测到一个焊点「少锡」——少了 5% 还是少了 70%？这决定了是放行还是返修。OpenCV 做的就是精确测量：把那个焊点区域放大，数像素面积、算圆度、量尺寸。"),
        boldPara("类比：", "YOLO 像机场安检的 X 光机——「这个包裹里有可疑物」。OpenCV 像安检员把包裹打开仔细检查——「是一瓶超过 100ml 的液体」。两者配合才完整。"),

        h2("2.6 SAM（Segment Anything Model，分割一切模型）"),
        boldPara("是什么？", "SAM 是 Meta（Facebook 的母公司）开发的一个图像分割模型。它的能力是：你告诉它「看这个区域」（点一下、画个框），它就把那个区域里物体的精确轮廓分割出来，精确到像素级别。"),
        boldPara("和 YOLO 的区别？", "YOLO 输出的是矩形框（bounding box），告诉你目标大概在哪个位置。SAM 输出的是 mask——一个和原图同样大小的黑白图，白色区域精确对应物体的形状。"),
        boldPara("我们为什么选 SAM 2.1？", "博世的 JD 里明确提到了 SAM 2.x。SAM 2.1 是最新版本，比第一代更快更准。我们在项目里把它做成「交互模式」——用户在图像上点一下缺陷区域，SAM 立刻分割出精确轮廓。这种交互感在面试 demo 时非常加分。"),
        boldPara("如果装不上怎么办？", "我们设计了三层 fallback（降级方案）：SAM 2.1 → SAM 1 → MobileSAM。后两者更轻量但接口完全一样，对 Agent 来说完全透明——它不关心底层用哪个模型。"),

        h2("2.7 RAG（检索增强生成）"),
        boldPara("是什么？", "RAG 是目前最流行的一种让 AI 能「引用资料」的技术。传统的 LLM 只能靠训练时记住的知识回答问题——如果问它「IPC-A-610 标准里 BGA 焊点空洞率不能超过多少」，它可能编一个答案（这叫「幻觉」）。RAG 的做法是：先从一个知识库里搜索相关文档，把搜到的内容作为参考喂给 LLM，让 LLM 基于真实资料来回答。"),
        boldPara("类比：", "普通 LLM 像一个裸考的学生，只能凭记忆回答。加了 RAG 的 LLM 像一个开卷考试的学生，能翻书找答案。"),

        h2("2.8 向量数据库（Vector Database）和 Embedding（嵌入）"),
        boldPara("Embedding 是什么？", "一句话：把文字变成一串数字。比如「焊点不良」四个字 → Embedding 模型 → [0.23, -0.15, 0.87, ...]（一个 512 维的向量）。神奇之处在于：意思相近的文字，它们的向量距离也近。「焊点不良」和「焊接质量差」的向量会很接近，「焊点不良」和「今天天气好」的向量会离得很远。"),
        boldPara("向量数据库是什么？", "一个专门存储和搜索向量的数据库。你把所有知识库文档都转成向量存进去。用户提问时，把问题也转成向量，然后在数据库里搜「哪些文档的向量和问题最接近」。这就是语义搜索——不靠关键词匹配，靠意思匹配。"),
        boldPara("我们为什么选 ChromaDB？", "ChromaDB 是最轻量的向量数据库，纯 Python 实现，不需要额外安装服务器。对于 demo 项目来说零部署成本。而且它支持本地持久化——数据存成文件，下次启动还在。"),

        h2("2.9 FastAPI（后端框架）"),
        boldPara("是什么？", "FastAPI 是一个 Python 的 Web 后端框架。它让你用极少的代码定义 API 接口（URL 地址），前端通过访问这些 URL 来调用后端功能。"),
        boldPara("为什么选 FastAPI 而不是 Flask/Django？", "第一，FastAPI 原生支持异步——这对我们的项目很重要，因为调用 Claude API 和 GPU 推理都是耗时操作，异步能大幅提升并发能力。第二，FastAPI 自动生成 Swagger 文档——你在浏览器打开 http://localhost:8000/docs 就能看到一个漂亮的 API 文档页面，可以直接在页面上试接口。面试时打开这个页面非常加分。"),

        h2("2.10 Streamlit（前端框架）"),
        boldPara("是什么？", "Streamlit 是一个纯 Python 写 Web 界面的框架。你不需要写 HTML/CSS/JavaScript，直接写 Python 代码就能生成网页。"),
        boldPara("为什么选 Streamlit？", "我们的目标是快速做一个可 demo 的产品。Streamlit 是 Python 生态里最快出活的方案。而且面试官看到你用纯 Python 搭出了完整的 Web 界面，会认可你的全栈能力。"),

        h2("2.11 几个制造领域的基础名词"),
        para("面试时需要用到这些词，但不需要深入："),
        boldPara("PCB（印刷电路板）：", "Printed Circuit Board。就是电子产品里那块绿色的板子，上面焊满了各种芯片和元件。"),
        boldPara("SMT（表面贴装技术）：", "Surface Mount Technology。把元件贴到电路板表面的工艺。现代电子制造的主流方式。"),
        boldPara("AOI（自动光学检测）：", "Automated Optical Inspection。用摄像头拍照然后自动检查缺陷的设备。SmartEye 做的就是这个事——只不过我们加了 AI Agent。"),
        boldPara("IPC 标准：", "IPC 是国际电子工业连接协会。他们发布了一系列电子制造的质量标准（比如 IPC-A-610），全球工厂都在用。"),

        new Paragraph({ children: [new PageBreak()] }),

        // ═══════════════════ CHAPTER 3 ═══════════════════
        h1("第三章  系统架构白话版 —— 整个系统长什么样？"),

        h2("3.1 用餐厅类比整个系统"),
        para("把 SmartEye 理解成一个智能餐厅："),
        bullet([{ text: "Streamlit 前端", bold: true }, { text: " = 餐厅的前厅。客人在这里看菜单（上传图片）、点菜（点击检测按钮）、看菜品（查看检测结果）。" }]),
        bullet([{ text: "FastAPI 后端", bold: true }, { text: " = 餐厅的后厨入口。服务员把订单送到后厨窗口，窗口把做好的菜传回来。" }]),
        bullet([{ text: "LangGraph 编排器", bold: true }, { text: " = 厨房的总厨（Chef）。他拿到订单后决定：这个菜要先煎再烤，那个菜要先切再拌。他指挥各个厨师干活。" }]),
        bullet([{ text: "五个 Agent", bold: true }, { text: " = 五个专业厨师。InspectionAgent 是切菜师傅（做视觉检测），AnalysisAgent 是品控师傅（分析数据），ReportAgent 是摆盘师傅（写报告），AlertAgent 是安全员（发现问题喊停），SupervisorAgent 是总厨本人（分配任务）。" }]),
        bullet([{ text: "Tool 层", bold: true }, { text: " = 厨房的设备。刀具（YOLO+OpenCV）、量杯（统计分析）、烤箱（SAM 分割）、打印机（报告导出）。" }]),
        bullet([{ text: "RAG 知识库", bold: true }, { text: " = 厨房墙上的菜谱和标准手册。厨师不确定怎么做时翻一下。" }]),

        h2("3.2 真正的技术架构（简化版）"),
        para("下面是简化后的架构图——你不需要完全理解，只要知道有这四层就行："),

        new Paragraph({ spacing: { before: 120, after: 60 },
          children: [new TextRun({ text: "第一层：用户界面（Streamlit）", bold: true, size: 24 })] }),
        para("→ 四个页面：质量检测、Agent 对话、分析仪表盘、质检报告"),

        new Paragraph({ spacing: { before: 120, after: 60 },
          children: [new TextRun({ text: "第二层：API 接口（FastAPI）", bold: true, size: 24 })] }),
        para("→ 前端和后端之间的桥梁。前端发 HTTP 请求，后端返回 JSON 数据。"),

        new Paragraph({ spacing: { before: 120, after: 60 },
          children: [new TextRun({ text: "第三层：Agent 编排引擎（LangGraph）", bold: true, size: 24 })] }),
        para("→ 系统的核心。总 Agent 接收任务 → 分派给专业 Agent → 专业 Agent 调用工具完成任务 → 结果汇总。"),

        new Paragraph({ spacing: { before: 120, after: 60 },
          children: [new TextRun({ text: "第四层：能力层（Tool + RAG + CV）", bold: true, size: 24 })] }),
        para("→ 各种实际干活的功能：YOLO 检测缺陷、OpenCV 测量尺寸、SAM 分割轮廓、统计分析数据、生成报告、检索知识库。"),

        h2("3.3 为什么这样分层？"),
        para("核心原则只有一个：每一层只和它相邻的层打交道。"),
        bullet("前端不直接调用 CV 模型——它只跟 API 说话。好处：哪天你想把 Streamlit 换成 React，后端一行不用改。"),
        bullet("Agent 不直接操作文件或 GPU——它只调用 Tool。好处：Tool 的实现可以随便换（比如换一个更好的缺陷检测模型），Agent 不需要知道。"),
        bullet("Supervisor 集中做路由决策——Worker Agent 只汇报结果不做决策。好处：新增一个 Agent 只需要在 Supervisor 的「花名册」里加一行，不用改任何已有代码。"),

        new Paragraph({ children: [new PageBreak()] }),

        // ═══════════════════ CHAPTER 4 ═══════════════════
        h1("第四章  详细工作流程 —— 从上传图片到生成报告，一步步发生了什么？"),

        h2("4.1 完整流程（以检测一张 PCB 缺陷图为例）"),
        para("假设你打开 SmartEye，上传了一张有桥接缺陷（两根导线中间有短路锡桥）的 PCB 图片，点击了「开始检测」按钮。接下来会发生下面的事："),

        h3("第 1 步：Streamlit 把图片发给 FastAPI"),
        para("Streamlit 把图片转成 base64 编码（一种把二进制文件变成纯文本的方式），然后用 HTTP POST 请求发给 http://localhost:8000/api/inspect。同时告诉后端：置信度阈值 0.25（低于这个置信度的检测结果不要），开启 SAM 精细分割。"),

        h3("第 2 步：FastAPI 创建任务，启动 Agent 流程"),
        para("FastAPI 收到请求后，创建一个任务 ID（一个随机字符串，用来追踪这次任务），然后初始化一个「状态对象」（SmartEyeState）——这是一个大字典，里面会记录这个任务的所有信息：原始图片、检测结果、分析结论、报告内容……初始时大部分字段都是空的。然后把这个状态对象交给 LangGraph 编排引擎。"),

        h3("第 3 步：SupervisorAgent 做第一次路由决策"),
        para("SupervisorAgent（总 Agent）检查状态对象：任务类型是 inspection（检测），有图片但没有检测结果。它判断：「这种情况应该交给 InspectionAgent」。它在状态的 next_agent 字段里写入了 inspection。"),

        h3("第 4 步：InspectionAgent 执行视觉检测"),
        para("InspectionAgent（检测 Agent）收到指令后，调用 detect_defects 这个 Tool。这个 Tool 内部执行了一个五阶段的检测流水线："),
        numbered("YOLO 粗检：YOLOv8 模型快速扫描整张图，发现 3 个候选缺陷——一个桥接（92% 置信度）、一个少锡（78%）、一个偏移（65%）。"),
        numbered("OpenCV 精确测量：对每个 YOLO 找到的缺陷区域，用 OpenCV 做精确测量。桥接的锡桥宽度 0.8mm，远超安全阈值。少锡的焊点面积只有标准的 40%。偏移量 0.32mm，超出 15% 的允许范围。"),
        numbered("OpenCV 盲区扫描：有些缺陷 YOLO 可能漏掉，OpenCV 独立执行颜色异常检测和丝印 OCR 识别作为补充。"),
        numbered("SAM 精细分割：对置信度 >70% 的缺陷（桥接和少锡），自动调用 SAM 做像素级分割。精确勾画出锡桥的轮廓和少锡区域的边界，计算出精确的面积值。"),
        numbered("融合判定：把 YOLO 的检测、OpenCV 的测量、SAM 的分割结果综合起来，给每个缺陷打上最终标签——桥接是 CONFIRMED + CRITICAL，少锡是 CONFIRMED + CRITICAL，偏移是 SUSPICIOUS + WARN。"),

        h3("第 5 步：结果返回 Supervisor，再次决策"),
        para("InspectionAgent 把检测结果写回状态对象，然后返回给 SupervisorAgent。Supervisor 检查结果：「有 CRITICAL 级别的缺陷，而且还没告警。应该先告警，再生成报告。」它路由到 AlertAgent。"),

        h3("第 6 步：AlertAgent 触发告警"),
        para("AlertAgent（告警 Agent）评估检测结果：桥接是 CRITICAL 缺陷，而且集中在 S2 工位。它调用规则引擎——触发 CRITICAL 级别告警。然后调用 RAG 知识库搜索「桥接缺陷的处置措施」——知识库返回：「检查印刷机钢网张力、检查回流焊 Zone2-3 温度曲线」。AlertAgent 生成告警消息："),

        new Paragraph({
          children: [new TextRun({ text: "「⚠️ CRITICAL 告警：S2 工位检测到桥接缺陷（锡桥宽度 0.8mm，超标）。建议：1. 暂停 S2 产线，检查印刷机钢网张力。2. 复查回流焊 Zone3 温度曲线。3. 本批次产品隔离待复检。」", italics: true, size: 20, color: "C0392B" })],
          spacing: { before: 80, after: 80 },
        }),

        h3("第 7 步：ReportAgent 生成报告"),
        para("AlertAgent 完成后退回 Supervisor。Supervisor 判断还需要生成报告，路由到 ReportAgent。ReportAgent 调用 generate_report_md Tool，用 Jinja2 模板引擎生成一份 Markdown 格式的质检报告，包含：批次号、检测时间、缺陷汇总表、帕累托图、处置建议。"),

        h3("第 8 步：任务完成，返回前端"),
        para("ReportAgent 完成后，Supervisor 判断所有任务完成，路由到 END。FastAPI 从最终的状态对象里提取检测结果、汇总、标注图、报告内容，打包成 JSON 返回给 Streamlit。Streamlit 收到后渲染：左边显示标注后的图片（缺陷区域有红色框和 SAM mask 叠加），下面显示缺陷明细表（类型、置信度、测量值、严重度），以及告警横幅和「生成 PDF 报告」的按钮。"),

        h2("4.2 整个流程用时"),
        para("从用户点击按钮到看到完整结果，大约 3 秒。时间分配大约是：YOLO 推理 0.05 秒、OpenCV 测量 0.1 秒、SAM 分割 0.3 秒、Claude API（3 次 LLM 调用）2 秒、网络传输 0.5 秒。"),

        new Paragraph({ children: [new PageBreak()] }),

        // ═══════════════════ CHAPTER 5 ═══════════════════
        h1("第五章  五个 Agent 的工作原理 —— 每个智能体干了什么？"),

        para("这一章详细介绍五个 Agent 的角色、它们拿到的「使用说明书」（System Prompt）、以及它们能用的「工具箱」。"),

        h2("5.1 什么是 System Prompt（系统提示词）？"),
        para("每一个 Agent 都有一份用 Markdown 写成的「使用说明书」——这就是 System Prompt。它告诉 Agent：你是谁（角色）、你能做什么（能力边界）、你应该怎么做（工作流程）、你不应该做什么（约束条件）。写出好的 System Prompt 是 Prompt Engineering 的核心——也是博世 JD 里明确要求的能力。"),

        h2("5.2 SupervisorAgent（总调度）"),
        boldPara("角色：", "工厂质检总调度。不亲自干活，只做决策。"),
        boldPara("核心能力：", "根据当前任务状态判断下一步该找谁。有图片没检测 → 找 InspectionAgent。有检测结果但没报告 → 找 ReportAgent。检测到严重缺陷 → 先找 AlertAgent 告警。"),
        boldPara("设计精妙之处：", "路由逻辑不是写死的 if-else。SupervisorAgent 是一个 LLM——它用「自然语言理解」来判断下一步该做什么。增加新 Agent 不需要改代码，只需要在 Supervisor 的 Prompt 里加一句话：「如果用户问 XX，路由到 NewAgent」。这比硬编码灵活得多，也是 LangGraph 的核心价值。"),

        h2("5.3 InspectionAgent（视觉检测专家）"),
        boldPara("角色：", "经验丰富的 AOI 质检员。"),
        boldPara("可用工具：", "detect_defects（三引擎全流程检测）、measure_component（指定区域精确测量）、segment_region（SAM 交互分割）、ocr_part_number（丝印文字识别）。"),
        boldPara("工作方式：", "收到 Supervisor 的指令后，判断需要哪些工具，依次调用。比如对于一张新上传的图，它会调 detect_defects 执行完整的五阶段检测 pipeline。如果 Supervisor 说「重点看左上角那个焊点」，它就会调 measure_component 做专项测量。"),

        h2("5.4 AnalysisAgent（统计分析师）"),
        boldPara("角色：", "SPC（统计过程控制）质量分析师。"),
        boldPara("可用工具：", "calculate_defect_rate（缺陷率计算）、trend_analysis（趋势分析）、pareto_analysis（帕累托分析）、severity_assessment（严重度评定）。"),
        boldPara("它判断什么：", "关键是区分「随机波动」和「系统性异常」。如果一个缺陷在这批里偶然出现——随机波动，正常放行但记录。如果连续 3 批都出现同一类缺陷——系统性异常，需要触发调查。这背后是 SPC 的方法论——控制图、帕累托法则。"),

        h2("5.5 ReportAgent（报告撰写员）"),
        boldPara("角色：", "工厂质检报告撰写员。"),
        boldPara("可用工具：", "generate_report_md（用模板生成 Markdown）、render_chart（画图表）、format_defect_table（做缺陷表格）、export_report（导出 PDF/DOCX）。"),
        boldPara("报告内容：", "按博世 Nexeed IAS 平台的格式生成中文报告——批次信息、缺陷汇总表、帕累托图、处置建议。结论必须明确（PASS / WARN / FAIL），建议必须具体可执行（「检查 S2 印刷机钢网」而不是「检查设备」）。"),

        h2("5.6 AlertAgent（安全哨兵）"),
        boldPara("角色：", "产线安全哨兵。"),
        boldPara("触发条件：", "不是每次都调用。只有检测到 CRITICAL 级别缺陷，或者连续多批次出现同类问题时才触发。"),
        boldPara("可用工具：", "check_alert_threshold（规则引擎判定是否告警）、format_alert_message（格式化为工厂告警模板）、suggest_corrective_action（从 RAG 知识库推荐处置措施）、escalate_alert（告警升级：INFO→班组长/WARN→质量工程师/CRITICAL→生产经理）。"),

        new Paragraph({ children: [new PageBreak()] }),

        // ═══════════════════ CHAPTER 6 ═══════════════════
        h1("第六章  计算机视觉怎么工作？—— 三引擎检测详解"),

        h2("6.1 为什么要三个引擎？"),
        para("只用一个引擎不够好。YOLO 快但只会画框，OpenCV 能精确测量但需要你告诉它测哪里，SAM 能精确分割但需要人告诉它看哪个区域。三个引擎互补：YOLO 找到「哪里有嫌疑」→ OpenCV 测量「有多严重」→ SAM 给出「精确边界」。这就是工业界标准的 hybrid approach（混合方法）。"),

        h2("6.2 YOLO 的「学习」过程"),
        para("YOLO 不是天生就会看 PCB 缺陷的。它需要「学习」——这个过程叫训练（Training）。"),
        para("训练过程简单来说："),
        numbered("准备几百张 PCB 图片，每张图上人工标注好缺陷位置和类别（比如「这张图的 (234,156) 到 (312,198) 这个区域是桥接缺陷」）。"),
        numbered("让 YOLO 看这些图片，它一开始会瞎猜。"),
        numbered("拿它的猜测和人工标注对比，算出「猜错了多少」（这个值叫 loss）。"),
        numbered("根据 loss 反向调整模型的参数，让它下一次猜得更准。"),
        numbered("重复几万次，直到 loss 降到足够低——这时候 YOLO 就「学会」了看 PCB 缺陷。"),

        para("我们用 YOLOv8n（n 代表 nano，是最小的版本），只有 320 万个参数。在 RTX 4060 上训练 30 分钟就能达到 >85% 的准确率。选最小的模型是因为：工业场景对速度要求极高，每张图的推理时间不能超过 100 毫秒。"),

        h2("6.3 OpenCV 的「规则」"),
        para("YOLO 是数据驱动的——它从标注数据里学。OpenCV 是规则驱动的——它执行人类写的固定规则。"),
        para("我们写了 5 个规则器："),
        bullet([{ text: "焊点质量检测：", bold: true }, { text: "把焊点区域从 BGR 转到 HSV 色彩空间 → 用颜色阈值把锡膏分离出来 → 找到锡膏区域的轮廓 → 计算面积和圆度。面积小于标准的 70% 就是少锡，圆度小于 0.6 就是形状不良。" }]),
        bullet([{ text: "元件偏移检测：", bold: true }, { text: "用阈值分割找到元件区域 → 计算质心位置 → 和预期位置比较距离 → 超过元件尺寸的 15% 就是偏移。" }]),
        bullet([{ text: "划痕检测：", bold: true }, { text: "Canny 边缘检测找边缘 → Hough 变换找直线 → 统计最长划痕长度 → 超过 2mm 就报警。" }]),
        bullet([{ text: "颜色异常检测：", bold: true }, { text: "转换到 Lab 色彩空间 → 和「金板」（完美的参考板）比颜色差异（ΔE）→ 超过 15 就是颜色异常。" }]),
        bullet([{ text: "丝印 OCR：", bold: true }, { text: "用 PaddleOCR 识别芯片上的文字 → 和物料清单（BOM）比对 → 不一致就是错件。" }]),

        h2("6.4 SAM 的「魔法」"),
        para("SAM 的神奇之处在于——它不需要针对 PCB 缺陷专门训练。它是一个「通用」分割模型，见过几百万张各种类型的图片，学会了「什么是物体的边界」这个通用概念。"),
        para("在 SmartEye 里，SAM 有两种使用方式："),
        bullet([{ text: "自动模式：", bold: true }, { text: "YOLO 找到的高置信度缺陷 → 用 YOLO 的边界框作为 SAM 的提示 → SAM 在框内精确分割。比如 YOLO 框住了一个焊点区域，SAM 把焊点的精确轮廓画出来。" }]),
        bullet([{ text: "交互模式：", bold: true }, { text: "用户在图像上点击某个位置 → SAM 以那个点击点为中心分割出整个物体。这是面试 live demo 的核心亮点——点点图片就能看到 AI 精确识别缺陷边界。" }]),

        h2("6.5 显存管理——为什么 RTX 4060 8GB 够用？"),
        para("这是一个实际工程问题。8GB 显存同时加载 YOLO 和 SAM 会爆。我们的解决方案是："),
        bullet("YOLO 常驻显存（它最常用，每次检测都需要）。"),
        bullet("SAM 按需加载——需要时才从硬盘加载到显存，用完了立刻卸载，释放空间给 YOLO。"),
        bullet("用一个叫 ModelRegistry 的单例类统一管理所有模型的加载和卸载，确保同一时间只有一个大模型在 GPU 上。"),
        bullet("加上一个信号量（Semaphore）锁——同一时间只允许一个推理任务运行，防止用户快速点击两次导致两个模型同时加载到显存。"),
        para("峰值显存约 5GB，8GB 绰绰有余。"),

        new Paragraph({ children: [new PageBreak()] }),

        // ═══════════════════ CHAPTER 7 ═══════════════════
        h1("第七章  RAG 知识库 —— AI 怎么「翻书」找答案？"),

        h2("7.1 知识库里有什么？"),
        para("我们准备了四类知识文档："),
        bullet([{ text: "IPC 标准摘要：", bold: true }, { text: "从 IPC-A-610 的公开培训材料和学术论文中整理的电子组件质量标准。比如 BGA 焊点 void 率——Class 2（专用电子产品）不能超过 25%，Class 3（高可靠性，如汽车电子）不能超过 15%。" }]),
        bullet([{ text: "工厂质检 SOP：", bold: true }, { text: "一份模拟的标准作业程序文档。包含来料检验、首件检验、过程抽检、不合格品处置的标准流程。虽然是模拟的，但格式和内容参考了真实的电子制造 SOP 模板。" }]),
        bullet([{ text: "历史缺陷案例库：", bold: true }, { text: "30-50 条结构化的缺陷案例。每条包含缺陷类型、严重度、根因分析、处置措施、效果验证。比如「案例 C2024-0152：BGA 虚焊，根因是回流焊 Zone3 温度偏低，处置措施是调高 5°C 并验证测温板 Profile」。" }]),
        bullet([{ text: "设备参数参考：", bold: true }, { text: "回流焊温度曲线标准参数、AOI 设备检测能力参数等。" }]),

        h2("7.2 AI 怎么从知识库里找东西？"),
        para("整个流程分四步："),
        numbered([{ text: "分块（Chunking）：", bold: true }, { text: "把每篇文档切成 512 个字左右的小段，段落之间有 64 个字的交叠（防止关键信息正好被切断）。" }]),
        numbered([{ text: "向量化（Embedding）：", bold: true }, { text: "每一小段文字通过 Embedding 模型转成一个 512 维的向量。这就像给每一小段文字分配了一个唯一的「语义坐标」。" }]),
        numbered([{ text: "检索（Retrieval）：", bold: true }, { text: "用户提问 → 也转成向量 → 在 ChromaDB 里搜索距离最近的 8 个文档片段。距离近 = 语义相关。" }]),
        numbered([{ text: "去重 + 重排序（Rerank）：", bold: true }, { text: "同一篇文档最多取 2 段（避免被一篇文档霸占结果）。然后用重排序模型重新评估 8 个候选的相关性，取最相关的 4 段喂给 Agent。" }]),

        h2("7.3 一个 RAG 的实际使用场景"),
        para("用户在 Agent 对话里问：「这批 PCB 的 BGA 焊点 void 率 30%，IPC 标准怎么说的？」"),
        numbered("Agent（ReportAgent）调用 search_knowledge_base Tool，查询「BGA 焊点 void 率 标准」。"),
        numbered("ChromaDB 找到 8 个相关片段，去重后剩 5 个，Rerank 后取 Top 4。"),
        numbered("回来的片段：「IPC-A-610 §8.3.2：BGA/CSP 焊接空洞可接受标准——Class 1 ≤30%，Class 2 ≤25%，Class 3 ≤15%。空洞率按 X-Ray 图像中空洞面积占焊球投影面积百分比计算。」"),
        numbered("Agent 基于这段真实资料回答：「根据 IPC-A-610 标准，30% 的 void 率——对于 Class 2（专用电子产品）已超标（限值 25%），对于 Class 3（高可靠性/汽车电子）严重超标（限值 15%）。建议确认产品等级后决定是否判退。」"),
        new Paragraph({ children: [new PageBreak()] }),

        // ═══════════════════ CHAPTER 8 ═══════════════════
        h1("第八章  前端界面 —— 四个页面分别能干什么？"),

        h2("8.1 页面一：质量检测（Hero Page）"),
        para("这是面试 demo 的核心页面。功能："),
        bullet("上传 PCB 图片（或从预设的示例图片中选择）→ 设置检测参数 → 点击「开始检测」。"),
        bullet("检测完成后：左侧显示标注图（缺陷区域有彩色框 + mask 蒙版），右侧显示缺陷明细表（类型、置信度、测量值、严重度）。"),
        bullet("交互功能：点击图像上的任意区域 → SAM 实时分割 → 显示精确轮廓和面积。"),
        bullet("一键跳转到生成报告或 Agent 对话。"),

        h2("8.2 页面二：Agent 对话"),
        para("一个聊天界面。你可以："),
        bullet("问质量标准：「BGA 焊点 void 率不能超过多少？」→ Agent 通过 RAG 查 IPC 标准回答。"),
        bullet("问处置方案：「虚焊率高该怎么办？」→ Agent 查历史案例库推荐方案。"),
        bullet("上传图片到对话中：「帮我看看这张图」→ Agent 自动触发视觉检测。"),
        para("右侧栏显示 Agent Trace——实时展示每个 Agent 被调用的时间、做了什么、调了什么 Tool。这是面试时展示「Agent 编排」的最佳方式。"),

        h2("8.3 页面三：分析仪表盘"),
        para("展示统计数据（用模拟数据做演示）："),
        bullet("帕累托图：显示哪些缺陷类型占比最高（80/20 法则——80% 的问题来自 20% 的原因）。"),
        bullet("P-Chart 趋势图：批次缺陷率的控制图，标注了 UCL（上控制限）——超出就说明有系统性异常。"),
        bullet("热力图：按工位 × 缺陷类型的分布矩阵，一眼看出哪个工位问题最集中。"),
        bullet("实时统计卡片：总检测数、合格率、平均检测时间、今日告警次数。"),

        h2("8.4 页面四：质检报告"),
        para("报告列表 + 预览 + 导出。Agent 自动生成的报告可以直接预览（Markdown 渲染），也可以下载为 PDF 或 DOCX 文件。PDF 导出用 Playwright 的 headless 浏览器做——这个技术细节面试时可以提到：「你们 Nexeed 平台也是 web 技术栈，我用 Playwright 做 PDF 渲染，思路是一样的。」"),

        new Paragraph({ children: [new PageBreak()] }),

        // ═══════════════════ CHAPTER 9 ═══════════════════
        h1("第九章  常见问题 FAQ"),

        h2("9.1 为什么不用一个大模型一次性完成所有事？"),
        para("一个全能大模型看起来更简单，但在质检场景里不靠谱。"),
        bullet("幻觉问题：大模型会编造信息。没有 RAG 约束，它可能发明一个不存在的 IPC 标准。"),
        bullet("专业性不足：通用大模型不知道 PCB 焊点的圆度阈值应该是多少。YOLO 和 OpenCV 经过专门训练/调试，在视觉检测上远比通用大模型准确。"),
        bullet("可追溯性：多 Agent 架构里，每一步决策都有记录（哪个 Agent、调了什么 Tool、输入输出是什么），出了问题能溯源。一个大模型「一口闷」，结果不可解释。"),

        h2("9.2 如果 YOLO 模型没训练好怎么办？"),
        para("有三层保障：第一，OpenCV 规则引擎独立工作，不需要训练。第二，合成数据脚本能生成基本的缺陷图片，确保 pipeline 能跑通。第三，面试 demo 用的是准备好的示例图片——YOLO 在这些图片上的表现已经验证过。"),

        h2("9.3 为什么选 Streamlit 而不是做一个好看的 React 页面？"),
        para("时间——2-3 周做一个完整项目，用 React 会导致大部分时间花在调 CSS 上而不是核心功能上。Streamlit 让你用纯 Python 快速出活。而且面试时你可以说：「我刻意做了前后端分离——FastAPI 的接口和 Streamlit 完全解耦，哪天需要换成 React 前端，后端一行不用改。」这证明了你的架构意识。"),

        h2("9.4 这个项目到底能不能在真实工厂用？"),
        para("诚实地说：作为 demo，不能直接部署到产线。但它展示的技术路线是完整的——Agent 编排、多引擎视觉检测、RAG 知识库、前后端分离——这些和博世苏州工厂的实际系统是同一条技术路线。demo 和产品的差距主要在：数据量（真实工厂需要几万张训练数据）、可靠性（需要更完善的异常处理和回退策略）、集成（需要对接真实的 MES 系统和 PLC 设备）。但作为实习面试的作品，它证明了「我知道这条技术路线怎么走」。"),

        h2("9.5 如果面试官问「你为什么不直接用 GPT-4 来识别缺陷」，怎么回答？"),
        para("「GPT-4 是多模态的，确实能看图片。但有两个核心问题：第一，速度——GPT-4 推理一张高分辨率 PCB 图像需要几秒，而 YOLO 只需要几十毫秒。产线上一天要检测几千张图，速度差距是致命的。第二，精度——通用视觉模型的泛化能力虽强，但在 PCB 缺陷这种专业领域，不如在专业数据集上微调的小模型准确。我们的方案是用专业模型做精确检测，用 LLM 做推理和决策——各自发挥长处。」"),

        new Paragraph({ children: [new PageBreak()] }),

        // ═══════════════════ APPENDIX: GLOSSARY ═══════════════════
        h1("附录  术语表 —— 碰到不懂的词来这里查"),

        para("按照在项目中出现的频率和重要程度排序。每个词都配了最土的解释。"),

        new Table({
          width: { size: DXA_CONTENT, type: WidthType.DXA },
          columnWidths: [2400, 6960],
          rows: [
            new TableRow({ children: [
              cell("术语", { width: 2400, bold: true, shading: "1A5276" }),
              new TableCell({ borders, margins: cellMargins, width: { size: 6960, type: WidthType.DXA },
                shading: { fill: "1A5276", type: ShadingType.CLEAR },
                children: [new Paragraph({ children: [new TextRun({ text: "大白话解释", bold: true, color: "FFFFFF", size: 20 })] })] })
            ]}),
            ...[
              ["AI Agent", "能自己想办法完成任务、会调用工具的 AI，不是一个只会答题的机器人。"],
              ["LLM / 大语言模型", "ChatGPT、Claude 这类读了几万亿字文本后学会语言理解和推理的 AI 模型。"],
              ["LangChain", "把 LLM 和各种工具、数据源串起来的 Python 库。"],
              ["LangGraph", "用「图」来编排多个 Agent 协作流程的框架——定义谁先执行、谁后执行。"],
              ["Prompt / 提示词", "给 AI 的「使用说明书」。告诉它你是谁、要做什么、怎么做好。"],
              ["Prompt Engineering", "设计和调优 Prompt 的工程方法——写出好的使用说明书是一门手艺。"],
              ["Function Calling", "LLM 调用外部函数/工具的能力。Agent 通过这个能力来「动手」而不是光说。"],
              ["Tool / 工具", "Agent 能调用的具体功能，比如「检测图片里的缺陷」「查数据库」「生成图表」。"],
              ["StateGraph", "LangGraph 的核心概念：用一个有状态（会记东西）的图来编排流程。"],
              ["State / 状态", "在流程中传递和积累信息的大字典。比如「检测结果」「分析结论」都存在 State 里。"],
              ["Supervisor Pattern", "一种 Agent 设计模式：一个总 Agent 做决策，多个专业 Agent 干具体活。"],
              ["RAG", "检索增强生成——先从一个知识库里搜相关文档，再基于文档回答。防止 AI 凭空编造。"],
              ["Embedding", "把文字变成一串数字（向量），意思相近的文字向量也相近。语义搜索的基础。"],
              ["Vector Database", "专门存向量和搜向量的数据库。ChromaDB 是其中最轻量的一个。"],
              ["ChromaDB", "一个轻量向量数据库，纯 Python，本地运行，零部署成本。"],
              ["YOLO", "一个快速目标检测模型，能在一张图里找到多个物体的位置和类别。"],
              ["YOLOv8n", "YOLO 第 8 版的 nano 变体——最小最快，只有 320 万个参数。"],
              ["OpenCV", "开源计算机视觉库，包含各种传统图像处理工具。做精确测量的主力。"],
              ["SAM", "Meta 开发的「分割一切」模型——点一下就能把物体精确轮廓画出来。"],
              ["PaddleOCR", "百度开发的开源 OCR（文字识别）工具，中文英文都识别得很好。"],
              ["FastAPI", "一个 Python Web 后端框架，写 API 接口特别快，自动生成交互式文档。"],
              ["Streamlit", "用纯 Python 写网页界面的框架，不需要 HTML/CSS，最快出活的方案。"],
              ["REST API", "一种 Web 接口设计规范：前端用 HTTP 请求访问后端的 URL 来获取数据。"],
              ["JSON", "一种通用的数据交换格式。前端和后端之间传各种数据都用这个格式。"],
              ["Base64", "把图片等二进制文件转成纯文本字符串的编码方式。方便在 JSON 里传输图片。"],
              ["Jinja2", "Python 的模板引擎。把数据填入预定义的模板生成报告——类似 Word 的邮件合并。"],
              ["Pydantic", "Python 的数据验证库。定义「这个 API 输入必须是 string，那个必须是 int」，自动校验。"],
              ["TDD", "测试驱动开发——先写测试再写代码，用测试来定义「这个功能应该怎么做」。"],
              ["SPC", "统计过程控制。用统计方法监控生产过程，区分随机波动和系统异常。"],
              ["Pareto / 帕累托", "80/20 法则。80% 的问题来自 20% 的原因。找到那 20% 关键原因优先解决。"],
              ["P-Chart / P 控制图", "一种统计控制图，追踪批次缺陷率的趋势，上下控制限帮助判断是否失控。"],
              ["PCB", "印刷电路板——所有电子产品里的那块绿色板子。"],
              ["SMT", "表面贴装技术——把元件焊到 PCB 表面，现代电子制造的主流工艺。"],
              ["AOI", "自动光学检测——用摄像头拍照检查 PCB 缺陷的设备。"],
              ["BGA", "球栅阵列封装——一种芯片封装方式，底部全是小球焊点，X-Ray 才能看到焊接质量。"],
              ["IPC-A-610", "全球通用的电子组装质量验收标准。定义了什么是可接受的焊点、什么不是。"],
              ["SOP", "标准作业程序——每一步怎么做的标准流程文档。工厂里几乎所有操作都有 SOP。"],
              ["MES", "制造执行系统——管工厂车间的软件，追踪每一批产品从投料到出货的全过程。"],
              ["PLC", "可编程逻辑控制器——控制产线机器的工业电脑，工厂自动化的基石。"],
              ["ONNX", "开放神经网络交换格式——一种通用模型格式，让不同框架训练的模型能互通。"],
              ["mAP@0.5", "目标检测模型的评价指标。IoU 阈值 0.5 时的平均精度，越高越好。"],
              ["CUDA", "NVIDIA 的 GPU 编程平台。PyTorch 用 CUDA 来让神经网络在显卡上跑。"],
              ["OOM", "Out of Memory——显存爆了。GPU 内存不够用，程序崩溃。我们的显存管理就是为了防这个。"],
            ].map(([term, def]) => new TableRow({
              children: [
                cell(term, { width: 2400, bold: true }),
                new TableCell({ borders, margins: cellMargins, width: { size: 6960, type: WidthType.DXA },
                  children: [new Paragraph({ children: [new TextRun({ text: def, size: 20 })] })] }),
              ]
            }))
          ]
        }),

        spacer(),
        spacer(),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 400 },
          children: [new TextRun({ text: "— 文档结束 —", size: 22, italics: true, color: "999999" })] }),
        new Paragraph({ alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "祝你面试成功！🚀", size: 24, bold: true, color: "1A5276" })] }),
      ]
    }
  ]
});

// ═══════════════════════════════════════════
// Generate DOCX
// ═══════════════════════════════════════════

const OUTPUT = "d:/C-file/smarteye/docs/SmartEye-白话说明文档.docx";

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(OUTPUT, buffer);
  console.log("DOCX generated successfully at: " + OUTPUT);
  console.log("File size: " + (buffer.length / 1024).toFixed(1) + " KB");
}).catch(err => {
  console.error("Failed to generate DOCX:", err);
  process.exit(1);
});

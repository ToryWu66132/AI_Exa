RAG Exa MVP
一个面向 AI SaaS 产品调研场景的竞品研究助手。用户输入产品名、官网和一句话描述后，系统会自动完成产品画像、竞品发现、网页证据收集、结构化分析、来源归档，并输出可下载、可保存的调研报告。

这个项目不是一个泛化的“问答型 RAG Demo”，而是一个更接近真实业务场景的垂直 MVP：把 Web Search + LLM + 结构化输出 组合成一个可交付的竞品调研工作流。

项目定位
这个项目适合用来展示以下能力：

将通用 RAG 原型重构为垂直产品工具
基于网页检索做 AI 产品竞品研究
用 LLM 生成结构化分析结果，而不是只输出自然语言答案
给结论补充来源编号，提高可追溯性
用 Streamlit 快速搭建可演示的产品界面
核心功能
输入 产品名 / 官网 / 一句话描述
自动生成目标产品基础画像
自动发现 3-5 个相关竞品
自动收集官网、定价页、文档页、评测页等网页证据
生成高层结论与竞品推荐理由
生成功能对比表和定价对比表
将结论中的引用统一编号为 [S1]、[S2] 等
按来源类型分组展示证据
支持导出 Markdown 报告
支持导出 PDF 报告
支持保存调研记录到本地
为什么这个项目有意思
很多 RAG Demo 的终点是“回答一个问题”，但这类产品很容易和通用 AI 搜索产品同质化。

这个项目的改造重点在于：

从“通用检索问答”转向“AI 产品竞品调研”
从“聊天回答”转向“结构化报告”
从“看起来像对”转向“可以回溯来源”
从“单轮体验”转向“可保存、可导出、可复用的结果”
这会让项目更像一个真实的产品 MVP，而不是一个只展示技术堆栈的实验脚本。

技术栈
Streamlit
用于快速搭建交互式前端页面
Exa
用于网页搜索和检索候选资料
DeepSeek
用于产品画像、竞品识别和结构化报告生成
Python
用于流程编排和数据处理
ReportLab
用于 PDF 导出
sentence-transformers
当前仓库中保留了向量评估相关实验代码
系统流程
整个调研流程大致如下：

用户输入目标产品信息
LLM 先生成目标产品画像
系统基于产品名、描述和赛道发起多轮 Exa 检索
LLM 根据候选资料识别最相关竞品
系统分别为目标产品和竞品补充官网、功能、定价、评测等来源
所有来源去重、编号，并映射到证据链
LLM 根据产品画像、竞品识别结果、证据地图和来源目录生成结构化报告
前端展示产品画像、竞品推荐、功能对比、定价对比、机会点、风险项和来源
用户可下载 Markdown/PDF，或保存本地 JSON + Markdown 结果
项目结构
RAG_Exa_MVP/
├── app/
│   ├── app.py                 # Streamlit 页面
│   └── main.py                # 命令行入口
├── core/
│   ├── pipeline.py            # 调研主流程编排
│   ├── reporting.py           # Markdown / PDF 报告生成
│   ├── storage.py             # 本地保存与历史记录读取
│   └── settings.py            # 预留配置模块
├── llm/
│   ├── deepseek.py            # DeepSeek 调用封装
│   ├── generator.py
│   ├── embedding.py
│   └── base.py
├── retrieval/
│   ├── web_search.py          # Exa 检索封装
│   └── vector_store.py
├── prompt/
│   └── template.py            # 产品画像 / 竞品发现 / 报告生成 Prompt
├── processing/
│   ├── cleaner.py
│   └── chunker.py
├── evaluation/
│   ├── eval.py                # 嵌入模型评估实验
│   └── test_data.py
├── data/
│   ├── cache/
│   └── saved_reports/         # 已保存调研结果
├── requirements.txt
├── README.md
├── INTERVIEW_GUIDE.md
└── INTERVIEW_QA.md
核心模块说明
core/pipeline.py
这是整个项目最核心的文件，负责把多个阶段串起来：

生成产品画像
收集竞品候选来源
识别竞品
为目标产品和竞品补充来源
去重与来源编号
建立证据映射
调用模型输出最终结构化报告
规范化引用编号和对比表结构
retrieval/web_search.py
封装 Exa 搜索，并对结果做了基础来源类型判断：

official
pricing
review
documentation
web
这让后续前端展示和报告分组更清晰。

prompt/template.py
包含三类关键 Prompt：

产品画像 Prompt
竞品发现 Prompt
最终报告 Prompt
Prompt 的重点不在“让模型更能聊”，而在“强约束输出 JSON 结构”，这是这个项目能稳定落地为工具的关键。

core/reporting.py
负责把结构化结果转成：

Markdown 报告
PDF 报告
这一步把分析结果从“模型输出”变成了“可交付文档”。

core/storage.py
用于：

保存 JSON 调研结果
保存 Markdown 报告
列出最近保存的调研记录
这让项目具备了最基础的结果沉淀能力。

前端体验
项目使用 Streamlit 构建了一个完整的 MVP 页面，包含：

调研输入表单
最近保存记录侧边栏
产品画像展示
竞品列表展示
功能对比表
定价对比表
机会点与风险说明
来源分组展示
Markdown / PDF 下载按钮
本地保存按钮
对于课程项目、作品集展示或面试演示来说，这种可视化交互会比纯脚本版更完整。

安装与运行
1. 创建虚拟环境
python -m venv .venv
source .venv/bin/activate
Windows:

.venv\Scripts\activate
2. 安装依赖
pip install -r requirements.txt
3. 配置环境变量
在项目根目录创建 .env 文件：

DEEPSEEK_API_KEY=your_deepseek_api_key
EXA_API_KEY=your_exa_api_key
启动方式
方式一：启动 Streamlit Web 应用
streamlit run app/app.py
启动后可以在浏览器中使用图形界面完成调研。

方式二：命令行模式
python app/main.py
命令行模式会提示你输入：

产品名
官网
一句话描述
然后直接打印调研结果对象。

输入与输出示例
输入示例
产品名：Perplexity
官网：https://www.perplexity.ai
一句话描述：面向知识工作者的 AI 搜索与问答产品
输出内容通常包括
产品画像
推荐竞品名单
执行摘要
功能对比表
定价对比表
机会点
风险与不确定项
带编号的来源列表
报告导出
当前版本支持两种导出方式：

Markdown
适合继续编辑、发给团队或存入知识库
PDF
适合汇报、提交作业或对外展示
如果使用“保存到本地”，系统会在 data/saved_reports/ 下生成：

一个 .json 文件
一个 .md 文件
文件名带时间戳，便于后续查找和归档。

证据链设计
这个项目比较有价值的一点，是它没有停留在“模型说了什么”，而是尝试把“为什么这么说”展示出来。

当前做法包括：

检索结果统一去重
每条来源分配 S1、S2 这类编号
报告中的结论、理由、定价备注、机会点、风险项尽量引用这些编号
前端按来源类型分组展示证据
这虽然不是严格意义上的事实校验系统，但已经比“纯自然语言总结”更接近真实研究工作的交付方式。

当前局限
竞品识别仍然依赖 LLM，对检索质量比较敏感
来源编号是后处理和 Prompt 约束结合完成的，稳定性有限
对价格、功能等信息的抽取还比较粗糙，没有做字段级校验
没有数据库和用户系统，结果只保存在本地文件
没有异步任务和缓存调度，连续调研时延会比较明显
PDF 是从 Markdown 近似转换，版式还比较基础
评估模块目前主要是嵌入相似度实验，不是完整的端到端评测
后续可扩展方向
增加结构化网页抽取，而不只依赖搜索摘要
引入更细粒度的字段校验，例如价格、套餐、是否支持 API
对来源做可信度评分和冲突检测
增加调研历史检索、标签和筛选功能
接入数据库替代本地 JSON 存储
增加批量调研模式
增加面向不同行业的模板，比如 AI Coding、AI Search、AI Agent、AI Design
增加真正的评估集，衡量竞品发现准确率和报告完整性
适合写进简历或作品集的描述
你可以这样概括这个项目：

设计并实现了一个面向 AI SaaS 场景的竞品调研助手，基于 Exa 网页检索与 DeepSeek 大模型完成产品画像、竞品发现、证据收集、结构化对比分析与可追溯报告生成，并通过 Streamlit 构建了可导出 Markdown/PDF 的 MVP 应用。

如果想更强调产品思维，也可以写成：

将一个通用 RAG 原型重构为垂直竞品研究工具，重点解决“结构化交付”和“来源可追溯”问题，而非停留在通用问答层面。

额外提醒
压缩包里包含 .env 文件。如果其中放的是可用的真实 API Key，建议不要把它继续放进公开仓库或分享压缩包里，最好改成：

保留 .env.example
将真实 .env 加入 .gitignore
轮换已经暴露过的密钥
License
如果你准备公开发布，建议补充正式许可证，例如 MIT License。

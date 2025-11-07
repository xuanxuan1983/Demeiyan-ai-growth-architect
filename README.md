【德美颜】AI增长架构师 / DeMeiYan AI Growth Architect
一个专为创业者和医美行业打造的AI驱动产品增长助手
An AI-powered growth architecture assistant for entrepreneurs and medical aesthetics professionals
一款面向企业家和医疗美容专业人士的 AI 驱动型增长架构助手
English | 中文
🚀 Live Demo / 在线演示
   Try it now:[https://streamlit-ai-assistant-xuanxuanchen198.replit.app](https://streamlit-ai-assistant-xuanxuanchen198.replit.app)

中文
📖 项目简介
【德美颜】AI增长架构师是一个基于Streamlit的AI驱动应用程序，旨在帮助创业者和医美行业从业者识别真实的市场需求、验证商业想法并跟踪增长实验。通过专业的AI代理团队，从需求洞察到产品上市和营销推广，全流程智能化支持您的业务增长。

✨ 核心功能
🎯 需求洞察引擎
需求雷达Agent：分析市场需求，识别真实痛点
用户画像建模Agent：提取用户痛点，创建精准用户画像
文件上传支持：支持上传调研报告（.txt, .md, .pdf, .docx）进行深度分析
📊 精益复盘中心
数据罗盘Agent：指导MVP实验，记录和分析实验结果
实验跟踪：全面的实验数据持久化和历史对比
🤝 AI团队协作中心
五位专业AI经理为您的产品提供全方位支持：

产品经理Agent：生成产品战略报告（SSR框架）
市场经理Agent：制定营销策略和品牌传播计划
医学经理Agent：提供医学可信度和合规审查
新媒体经理Agent：创建社交媒体内容策略（小红书、Instagram、抖音、微博、B站、知乎、微信公众号）
设计经理Agent：推荐品牌视觉方案和设计策略
📈 数据看板
可视化需求分析趋势
用户画像分布统计
MVP实验成功率分析
🌐 中英文双语支持
完整的界面翻译系统
AI输出支持简体中文、繁体中文、English
运行时动态切换，无需刷新
💾 全面的数据持久化
PostgreSQL数据库存储所有分析结果
支持历史记录查询和对比
分页浏览历史数据
📄 报告导出
Markdown格式导出
PDF格式导出（支持完整中文字符）
🎨 设计特色
深色主题：专业的紫蓝渐变背景（#7e5bff to #00c7ff）
玻璃态设计：现代化的玻璃态卡片和容器
发光效果：精美的边框发光和悬停动画
流畅动画：使用cubic-bezier缓动函数的交互动画
🛠 技术栈
前端框架：Streamlit
AI服务：Google Gemini API (gemini-2.5-flash)
AI 服务 ：Google Gemini API (gemini-2.5-flash)
数据库：PostgreSQL
数据可视化：Plotly
PDF生成：FPDF2（支持中文）
包管理器：uv
📦 依赖包
[project.dependencies]
streamlit
google-genai
psycopg2-binary
plotly
fpdf2
pypdf
python-docx

🚀 快速开始
1. 环境准备
确保您已安装Python 3.11或更高版本。

2. 克隆项目
git clone https://github.com/您的用户名/demeiyan-ai-growth-architect.git
cd demeiyan-ai-growth-architect

3. 安装依赖
使用uv（推荐）：  使用 uv（推荐）：

uv pip install -e .

或使用pip：

pip install streamlit google-genai psycopg2-binary plotly fpdf2 pypdf python-docx

4. 配置环境变量
创建.env文件或在Replit Secrets中设置以下环境变量：

GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=your_postgresql_database_url_here

获取API密钥：

Google Gemini API: https://ai.google.dev/
Google Gemini API： https://ai.google.dev/
5. 初始化数据库
首次运行时，应用程序会自动创建所需的数据库表：

demand_analysis：需求分析记录
user_persona：用户画像记录
mvp_experiment：MVP实验记录
6. 运行应用
streamlit run app.py --server.port 5000

访问 http://localhost:5000 即可使用应用。

📂 项目结构
.
├── app.py                 # 主应用程序文件
├── database.py            # 数据库操作模块
├── .streamlit/
│   └── config.toml        # Streamlit配置文件
├── fonts/
│   └── 华文中宋.ttf        # 中文字体（用于PDF导出）
├── pyproject.toml         # 项目依赖配置
├── replit.md              # 项目技术文档
└── README.md              # 本文件

🔧 主要配置
Streamlit配置 (.streamlit/config.toml)
Streamlit 配置(.streamlit/config.toml)
[server]
port = 5000
address = "0.0.0.0"
headless = true
[theme]
base = "dark"
primaryColor = "#9D7EFF"
backgroundColor = "#0A0B1E"
secondaryBackgroundColor = "#1A1B3D"
textColor = "#E8E9F3"

💡 使用指南
选择语言：在侧边栏顶部选择您偏好的语言（简体中文/English）

需求洞察：

输入您的产品概念或上传调研报告
使用需求雷达Agent分析市场需求
使用用户画像Agent创建精准用户画像
精益复盘：

记录您的MVP实验数据
使用数据罗盘Agent获取AI复盘建议
AI团队协作：

填写项目总览信息
选择需要咨询的AI经理
获取专业的策略报告
查看历史：

浏览所有历史分析记录
支持分页查询
数据看板：

可视化查看趋势和统计数据
导出报告：

点击导出按钮下载Markdown或PDF格式报告
🔐 安全提示
切勿提交API密钥到代码仓库：始终使用环境变量或Secrets管理
数据库连接：确保DATABASE_URL配置正确且安全
生产部署：建议使用Replit的内置发布功能或其他专业托管服务
🤝 贡献指南
欢迎贡献代码、报告问题或提出新功能建议！

Fork 本项目
创建您的特性分支 (git checkout -b feature/AmazingFeature)
提交您的更改 (git commit -m 'Add some AmazingFeature')
推送到分支 (git push origin feature/AmazingFeature)
开启一个Pull Request  开启一个拉取请求
📝 许可证
本项目采用 MIT 许可证 - 查看 LICENSE 文件了解详情

📧 联系方式
如有问题或建议，欢迎通过以下方式联系：

项目Issue: GitHub Issues
项目问题： GitHub 问题
Email: your-email@example.com
电子邮件： 您的电子邮件地址@example.com
English  英语
📖 Project Overview  📖 项目概览
DeMeiYan AI Growth Architect is a Streamlit-based AI-driven application designed to help entrepreneurs and medical aesthetics professionals identify genuine market needs, validate business ideas, and track growth experiments. With a team of specialized AI agents, it provides intelligent support throughout your business growth journey—from demand insights to product launch and marketing.
DeMeiYan AI Growth Architect 是一款基于 Streamlit 的人工智能驱动型应用程序，旨在帮助企业家和医疗美容专业人士识别真正的市场需求、验证商业理念并跟踪增长实验。它拥有一支专业的 AI 代理团队，可在您的业务增长之旅中提供智能支持——从需求洞察到产品发布和市场营销。

✨ Key Features  ✨ 主要特点
🎯 Demand Insight Engine
🎯 需求洞察引擎
Demand Radar Agent: Analyzes market demand and identifies real pain points
需求雷达代理 ：分析市场需求并识别真正的痛点
User Persona Modeling Agent: Extracts user pain points and creates precise personas
用户画像建模代理 ：提取用户痛点并创建精准的用户画像
File Upload Support: Upload research reports (.txt, .md, .pdf, .docx) for deep analysis
文件上传支持 ：可上传研究报告（.txt、.md、.pdf、.docx）进行深度分析
📊 Lean Retrospective Center
📊精益回顾中心
Data Compass Agent: Guides MVP experimentation and analyzes results
数据指南针代理 ：指导 MVP 实验并分析结果
Experiment Tracking: Comprehensive experiment data persistence and historical comparison
实验跟踪 ：全面的实验数据保存和历史对比
🤝 AI Team Collaboration Center
🤝 AI 团队协作中心
Five professional AI managers providing comprehensive support:
五位专业的 AI 经理提供全方位支持：

Product Manager Agent: Generates product strategy reports (SSR framework)
产品经理代理 ：生成产品策略报告（SSR 框架）
Marketing Manager Agent: Develops marketing strategies and brand communication plans
市场经理代理 ：制定市场营销策略和品牌传播计划
Medical Manager Agent: Provides medical credibility and compliance review
医疗管理代理 ：提供医疗资质和合规性审查
Social Media Manager Agent: Creates content strategies for major platforms (XiaoHongShu, Instagram, TikTok, Weibo, Bilibili, Zhihu, WeChat)
社交媒体经理代理 ：为主要平台（小红书、Instagram、TikTok、微博、哔哩哔哩、知乎、微信）制定内容策略
Design Manager Agent: Recommends brand visual solutions and design strategies
设计经理代理 ：推荐品牌视觉解决方案和设计策略
📈 Data Dashboard  📈 数据仪表盘
Visualize demand analysis trends
可视化需求分析趋势
User persona distribution statistics
用户画像分布统计
MVP experiment success rate analysis
MVP 实验成功率分析
🌐 Bilingual Support  🌐 双语支持
Complete interface translation system
完整的界面翻译系统
AI output supports Simplified Chinese, Traditional Chinese, and English
AI 输出支持简体中文、繁体中文和英文。
Dynamic language switching without page refresh
无需页面刷新即可实现语言切换
💾 Comprehensive Data Persistence
💾 全面数据持久化
PostgreSQL database for all analysis results
所有分析结果均存储在 PostgreSQL 数据库中
Historical query and comparison support
历史查询和比较支持
Paginated browsing of historical data
分页浏览历史数据
📄 Report Export  📄 报告导出
Markdown format export  Markdown 格式导出
PDF format export (full Chinese character support)
PDF 格式导出（完全支持中文字符）
🎨 Design Features  🎨 设计特点
Dark Theme: Professional purple-blue gradient background (#7e5bff to #00c7ff)
深色主题 ：专业紫蓝色渐变背景（#7e5bff 至 #00c7ff）
Glassmorphism Design: Modern glass-effect cards and containers
玻璃变形设计 ：现代玻璃效果卡片和容器
Glow Effects: Elegant border glows and hover animations
发光效果 ：优雅的边框发光和悬停动画
Smooth Animations: Interactive animations with cubic-bezier easing
流畅动画 ：具有三次贝塞尔缓动效果的交互式动画
🛠 Tech Stack  🛠 技术栈
Frontend Framework: Streamlit
前端框架 ：Streamlit
AI Service: Google Gemini API (gemini-2.5-flash)
人工智能服务 ：Google Gemini API (gemini-2.5-flash)
Database: PostgreSQL
数据库 ：PostgreSQL
Data Visualization: Plotly
数据可视化 ：Plotly
PDF Generation: FPDF2 (with Chinese support)
PDF 生成 ：FPDF2（支持中文）
Package Manager: uv
包管理器 ：uv
📦 Dependencies  📦 依赖项
[project.dependencies]
streamlit
google-genai
psycopg2-binary
plotly
fpdf2
pypdf
python-docx

🚀 Quick Start  🚀 快速入门
1. Prerequisites  1. 先决条件
Ensure you have Python 3.11 or higher installed.
请确保您已安装 Python 3.11 或更高版本。

2. Clone the Repository
2. 克隆代码库
git clone https://github.com/yourusername/demeiyan-ai-growth-architect.git
cd demeiyan-ai-growth-architect

3. Install Dependencies  3. 安装依赖项
Using uv (recommended):  使用紫外线（推荐）：

uv pip install -e .

Or using pip:  或者使用 pip：

pip install streamlit google-genai psycopg2-binary plotly fpdf2 pypdf python-docx

4. Configure Environment Variables
4. 配置环境变量
Create a .env file or set in Replit Secrets:
创建 .env 文件或在 Replit Secrets 中进行设置：

GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=your_postgresql_database_url_here

Obtain API Keys:  获取 API 密钥：

Google Gemini API: https://ai.google.dev/
Google Gemini API： https://ai.google.dev/
5. Initialize Database  5. 初始化数据库
On first run, the application will automatically create required database tables:
首次运行时，应用程序将自动创建所需的数据库表：

demand_analysis: Demand analysis records
demand_analysis ：需求分析记录
user_persona: User persona records
user_persona ：用户角色记录
mvp_experiment: MVP experiment records
mvp_experiment ：MVP 实验记录
6. Run the Application
6. 运行应用程序
streamlit run app.py --server.port 5000

Visit http://localhost:5000 to use the application.
访问 http://localhost:5000 即可使用该应用程序。

📂 Project Structure  📂 项目结构
.
├── app.py                 # Main application file
├── database.py            # Database operations module
├── .streamlit/
│   └── config.toml        # Streamlit configuration
├── fonts/
│   └── 华文中宋.ttf        # Chinese font (for PDF export)
├── pyproject.toml         # Project dependencies
├── replit.md              # Technical documentation
└── README.md              # This file

🔧 Main Configuration  🔧 主配置
Streamlit Configuration (.streamlit/config.toml)
Streamlit 配置（.streamlit/config.toml）
[server]
port = 5000
address = "0.0.0.0"
headless = true
[theme]
base = "dark"
primaryColor = "#9D7EFF"
backgroundColor = "#0A0B1E"
secondaryBackgroundColor = "#1A1B3D"
textColor = "#E8E9F3"

💡 User Guide  💡 用户指南
Select Language: Choose your preferred language (简体中文/English) in the sidebar
选择语言 ：请在侧边栏选择您偏好的语言（简体中文/英文）。

Demand Insights:
需求洞察 ：

Enter your product concept or upload research reports
输入您的产品概念或上传研究报告
Use Demand Radar Agent to analyze market demand
使用需求雷达代理分析市场需求
Use User Persona Agent to create precise user personas
使用用户角色代理创建精确的用户角色
Lean Retrospective:
精益回顾 ：

Record your MVP experiment data
记录你的 MVP 实验数据
Get AI-powered retrospective insights with Data Compass Agent
借助数据指南针代理获取 AI 驱动的回顾性洞察
AI Team Collaboration:
AI 团队协作 ：

Fill in project overview information
填写项目概述信息
Select the AI manager you want to consult
选择您想咨询的人工智能经理
Receive professional strategy reports
接收专业战略报告
View History:
查看历史记录 ：

Browse all historical analysis records
浏览所有历史分析记录
Supports paginated queries
支持分页查询
Data Dashboard:
数据仪表盘 ：

Visualize trends and statistics
可视化趋势和统计数据
Export Reports:
导出报告 ：

Click export buttons to download Markdown or PDF reports
点击导出按钮下载 Markdown 或 PDF 报告
🔐 Security Tips  🔐 安全提示
Never commit API keys to repository: Always use environment variables or Secrets
永远不要将 API 密钥提交到代码仓库 ：始终使用环境变量或 Secret。
Database Connection: Ensure DATABASE_URL is configured correctly and securely
数据库连接 ：确保 DATABASE_URL 配置正确且安全。
Production Deployment: Recommended to use Replit's built-in publishing or other professional hosting services
生产环境部署 ：建议使用 Replit 内置的发布功能或其他专业的托管服务。
🤝 Contributing  🤝 贡献
Contributions, issues, and feature requests are welcome!
欢迎提出贡献、问题和功能建议！

Fork the project  分支该项目
Create your feature branch (git checkout -b feature/AmazingFeature)
创建你的特性分支（ git checkout -b feature/AmazingFeature ）
Commit your changes (git commit -m 'Add some AmazingFeature')
提交更改（ git commit -m 'Add some AmazingFeature' ）
Push to the branch (git push origin feature/AmazingFeature)
推送到分支（ git push origin feature/AmazingFeature ）
Open a Pull Request
提交拉取请求
📝 License  📝 许可证
This project is licensed under the MIT License - see the LICENSE file for details
本项目采用 MIT 许可证，详情请参阅 LICENSE 文件。

📧 Contact  📧 联系方式
For questions or suggestions, please contact:
如有任何疑问或建议，请联系：

Project Issues: GitHub Issues
项目问题： GitHub Issues
Email: your-email@example.com
电子邮件： 您的电子邮件地址@example.com
Made with ❤️ for entrepreneurs and growth professionals
用心打造，献给企业家和成长型专业人士

为创业者和增长专业人士用心打造


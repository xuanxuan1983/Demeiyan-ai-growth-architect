import streamlit as st
from google import genai
from google.genai import types
import time
import os
import plotly.graph_objects as go
import plotly.express as px
from database import Database
from datetime import datetime
from fpdf import FPDF
import re
from pypdf import PdfReader
from docx import Document
import io

# 使用Google Gemini API
# 最新的Gemini模型是 "gemini-2.5-flash" 和 "gemini-2.5-pro"
# 除非用户明确要求，否则不要更改

# --- 1. 配置 Gemini API Key ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("错误：请设置 GEMINI_API_KEY 环境变量。")
    st.info("您可以通过 Replit 的 Secrets 功能添加 GEMINI_API_KEY。请使用您的Google AI API密钥：AIzaSyC3tDHVxVetVjefUn-5bC_3mdqxHNV7qaA")
    st.stop()

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    st.error(f"初始化Gemini客户端失败: {e}")
    st.stop()

# --- 初始化数据库 ---
try:
    db = Database()
except Exception as e:
    st.error(f"数据库连接失败: {e}")
    st.stop()

# --- Gemini API调用辅助函数 ---
def call_gemini(system_prompt, user_prompt, model="gemini-2.5-flash"):
    """
    统一的Gemini API调用函数
    
    Args:
        system_prompt: 系统提示（角色和任务描述）
        user_prompt: 用户提示（具体请求）
        model: 使用的模型，默认为 gemini-2.5-flash
    
    Returns:
        生成的文本内容
    """
    try:
        # 将系统提示和用户提示组合
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        response = client.models.generate_content(
            model=model,
            contents=full_prompt
        )
        
        return response.text or ""
    except Exception as e:
        raise Exception(f"Gemini API调用失败: {e}")


# --- 文件内容提取函数 ---
def extract_file_content(uploaded_file):
    """
    从上传的文件中提取文本内容
    
    支持的格式：
    - 文本文件 (.txt, .md)
    - PDF文件 (.pdf)
    - Word文档 (.docx)
    
    Args:
        uploaded_file: Streamlit上传的文件对象
    
    Returns:
        提取的文本内容，如果失败则返回None
    """
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension in ['txt', 'md']:
            # 处理文本文件
            content = uploaded_file.read().decode('utf-8')
            return content
        
        elif file_extension == 'pdf':
            # 处理PDF文件
            pdf_reader = PdfReader(io.BytesIO(uploaded_file.read()))
            text_content = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    extracted_text = page.extract_text()
                    # 只添加非空文本
                    if extracted_text and extracted_text.strip():
                        text_content.append(extracted_text.strip())
                except Exception as e:
                    # 记录提取失败的页面，但继续处理其他页面
                    print(f"[PDF提取警告] 第{page_num + 1}页提取失败: {e}")
                    continue
            
            if not text_content:
                return "PDF文件内容提取为空，可能是扫描件或图片PDF。"
            return '\n\n'.join(text_content)
        
        elif file_extension == 'docx':
            # 处理Word文档
            doc = Document(io.BytesIO(uploaded_file.read()))
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)
            return '\n\n'.join(text_content)
        
        else:
            return None
    
    except Exception as e:
        st.error(f"文件内容提取失败: {e}")
        return None


# --- PDF生成辅助函数 ---
class ChinesePDF(FPDF):
    """支持中文的PDF生成器"""
    def header(self):
        try:
            # 使用已添加的中文字体
            self.set_font('NotoSansSC', '', 12)
            self.cell(0, 10, '【德美颜】AI增长架构师', 0, 1, 'C')
        except:
            # 如果字体未加载，使用默认字体
            self.set_font('helvetica', '', 12)
            self.cell(0, 10, 'AI Growth Architect', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        try:
            self.set_font('NotoSansSC', '', 8)
            self.cell(0, 10, f'第 {self.page_no()} 页', 0, 0, 'C')
        except:
            self.set_font('helvetica', '', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(title, content, metadata=None):
    """
    生成PDF报告（支持中文）
    
    Args:
        title: 报告标题
        content: 报告内容（支持简单的Markdown格式）
        metadata: 元数据字典（如项目名称、生成时间等）
    
    Returns:
        PDF文件的bytes数据
    """
    try:
        print("[PDF] 开始生成PDF...")  # 调试日志
        # 创建PDF对象（A4纸张，纵向，单位mm）
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        print(f"[PDF] PDF对象已创建，页面宽度: {pdf.w}")
        
        # 先设置边距，再添加页面
        pdf.set_margins(left=15, top=15, right=15)
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        print(f"[PDF] 页面已添加，有效宽度: {pdf.w - pdf.l_margin - pdf.r_margin}mm")
        
        # 尝试加载中文字体
        use_chinese = False
        try:
            font_path = 'fonts/ChineseFont.ttf'
            if os.path.exists(font_path):
                pdf.add_font('ChineseFont', '', font_path)
                use_chinese = True
                print("[PDF] 成功加载中文字体")
        except Exception as e:
            print(f"[PDF] 加载中文字体失败: {e}")
            pass
        
        # 标题
        print("[PDF] 准备写入标题...")
        if use_chinese:
            pdf.set_font('ChineseFont', '', 16)
            # 使用传入的标题
            title_w = pdf.get_string_width(title) + 6
            pdf.set_x((pdf.w - title_w) / 2)
            pdf.cell(title_w, 10, title)
        else:
            pdf.set_font('helvetica', 'B', 14)
            title_w = pdf.get_string_width('AI Growth Architect Report') + 6
            pdf.set_x((pdf.w - title_w) / 2)
            pdf.cell(title_w, 10, 'AI Growth Architect Report')
        pdf.ln(15)
        print("[PDF] 标题写入成功")
        
        # 元数据
        if metadata:
            if use_chinese:
                pdf.set_font('ChineseFont', '', 9)
            else:
                pdf.set_font('helvetica', '', 8)
            
            for key, value in metadata.items():
                if use_chinese:
                    # 使用中文字体，可以显示中文
                    pdf.cell(0, 5, f'{key}: {value}')
                else:
                    # 只显示ASCII字符
                    safe_value = str(value).encode('ascii', 'ignore').decode('ascii')
                    if safe_value:
                        pdf.cell(0, 4, f'Info: {safe_value}')
                pdf.ln(6)
            pdf.ln(3)
        
        # 内容处理 - 优化排版
        if use_chinese:
            pdf.set_font('ChineseFont', '', 10)
        else:
            pdf.set_font('helvetica', '', 9)
        
        print("[PDF] 开始处理内容...")
        
        # 处理内容
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                pdf.ln(4)  # 空行留更多空间
                continue
            
            if use_chinese:
                # 使用中文字体，可以显示完整内容
                # 处理Markdown标记
                if line.startswith('###'):
                    # 三级标题
                    pdf.ln(3)
                    pdf.set_font('ChineseFont', '', 11)
                    pdf.multi_cell(0, 7, line.replace('###', '').strip())
                    pdf.set_font('ChineseFont', '', 10)
                    pdf.ln(2)
                elif line.startswith('##'):
                    # 二级标题
                    pdf.ln(4)
                    pdf.set_font('ChineseFont', '', 13)
                    pdf.multi_cell(0, 8, line.replace('##', '').strip())
                    pdf.set_font('ChineseFont', '', 10)
                    pdf.ln(3)
                elif line.startswith('#'):
                    # 一级标题
                    pdf.ln(5)
                    pdf.set_font('ChineseFont', '', 14)
                    pdf.multi_cell(0, 9, line.replace('#', '').strip())
                    pdf.set_font('ChineseFont', '', 10)
                    pdf.ln(4)
                elif line.startswith('-') or line.startswith('•'):
                    # 列表项 - 使用更好的行高和缩进
                    text = line[1:].strip()
                    # 保存当前位置
                    x_start = pdf.get_x()
                    y_start = pdf.get_y()
                    # 写入bullet
                    pdf.set_font('ChineseFont', '', 10)
                    pdf.cell(5, 6, '•')
                    # 写入内容，限制宽度以实现缩进
                    pdf.set_xy(x_start + 5, y_start)
                    pdf.multi_cell(0, 6, text)
                    pdf.ln(1)
                else:
                    # 普通段落 - 去掉Markdown粗体标记
                    clean_line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
                    pdf.set_font('ChineseFont', '', 10)
                    pdf.multi_cell(0, 6, clean_line)
                    pdf.ln(2)
            else:
                # ASCII模式
                clean_line = line.encode('ascii', 'ignore').decode('ascii').strip()
                if clean_line and len(clean_line) >= 2:
                    pdf.multi_cell(0, 5, clean_line)
                    pdf.ln(2)
        
        print(f"[PDF] 内容处理完成，共处理{len(lines)}行")
        
        # 返回PDF的bytes数据
        return pdf.output()
    
    except Exception as e:
        # 后备方案：生成包含错误信息的PDF
        print(f"[PDF] 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('helvetica', '', 12)
        pdf.cell(0, 10, 'PDF Generation Error')
        pdf.ln(10)
        pdf.set_font('helvetica', '', 10)
        pdf.cell(0, 8, 'Please use Markdown export for full content.')
        return pdf.output()


# --- 2. 页面基本设置 ---
st.set_page_config(
    page_title="【德美颜】AI增长架构师",
    page_icon="✨",
    layout="wide"
)

# --- 深色主题 - 紫蓝渐变、发光效果、流畅动画 ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* 整体应用布局 */
    body {
        margin: 0;
        padding: 0;
        background-color: #0d0c1d;
    }
    
    .stApp {
        display: flex;
        min-height: 100vh;
        background-color: #0d0c1d;
    }
    
    /* 全局样式 - 更深的紫蓝渐变背景 */
    .main {
        background: linear-gradient(135deg, #0d0c1d 0%, #1a0b2e 50%, #0d1b2e 100%);
        background-size: 200% 200%;
        background-attachment: fixed;
        animation: gradientShift 15s ease infinite;
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        line-height: 1.65;
        padding: 2.5rem 3rem;
        flex-grow: 1;
        max-width: 1100px;
        margin: 0 auto;
    }
    
    /* 主内容区域布局 */
    .main > div {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }
    
    /* Streamlit容器间距优化 - 统一间距系统 */
    .element-container {
        margin-bottom: 0.5rem;
    }
    
    .stMarkdown {
        margin-bottom: 0.5rem;
    }
    
    /* 功能区块间距 */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* 发光粒子背景效果 */
    .main::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at 20% 30%, rgba(157, 126, 255, 0.15) 0%, transparent 50%),
                    radial-gradient(circle at 80% 70%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
                    radial-gradient(circle at 50% 50%, rgba(168, 85, 247, 0.1) 0%, transparent 50%);
        pointer-events: none;
        z-index: 0;
        animation: particleFloat 20s ease-in-out infinite;
    }
    
    @keyframes particleFloat {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 0.6; }
    }
    
    /* 侧边栏样式 - 更深的渐变 */
    [data-testid="stSidebar"] {
        background: #1a192f;
        border-right: none;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        padding: 20px 10px;
    }
    
    [data-testid="stSidebar"] > div {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
    }
    
    [data-testid="stSidebar"] * {
        color: #b0b0d0 !important;
    }
    
    /* 二级标题 - 渐变文字（页面内容标题） */
    h2 {
        background: linear-gradient(90deg, #7e5bff, #00e0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 600;
        font-size: 1.6rem;
        letter-spacing: -0.01em;
        line-height: 1.35;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    
    /* 三级标题（功能模块标题） */
    h3 {
        background: linear-gradient(90deg, #7e5bff, #00e0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 500;
        font-size: 1.15rem;
        letter-spacing: 0;
        line-height: 1.4;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }
    
    /* 段落和文本样式 */
    p {
        font-size: 0.95rem;
        color: #b0b0d0;
        margin-bottom: 0.75rem;
        line-height: 1.65;
        font-weight: 400;
    }
    
    span, div, label {
        color: #b0b0d0;
        line-height: 1.65;
        font-size: 0.95rem;
        font-weight: 400;
    }
    
    /* 正文加粗文本 */
    strong, b {
        font-weight: 600;
        color: #FFFFFF;
    }
    
    /* 描述性文字（subheader等） */
    .stMarkdown p,
    [data-testid="stMarkdownContainer"] p {
        font-size: 0.95rem;
        color: #b0b0d0;
        margin-bottom: 0.75rem;
        line-height: 1.65;
        font-weight: 400;
    }
    
    /* 移除全局卡片样式，避免过度应用 */
    /* 仅在特定组件上应用卡片效果 */
    
    /* 输入框样式 - 统一设计语言 */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        width: 100%;
        padding: 0.75rem 1rem;
        background-color: #0d0c1d;
        border: 1px solid rgba(80, 70, 150, 0.6);
        border-radius: 10px;
        color: #e0e0e0;
        font-size: 0.95rem;
        font-weight: 400;
        line-height: 1.5;
        transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    
    /* 输入框标签 */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label {
        font-size: 0.9rem;
        font-weight: 500;
        color: #b0b0d0;
        margin-bottom: 0.5rem;
        display: block;
    }
    
    /* 输入框聚焦效果 - 统一发光强度 */
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        outline: none;
        border-color: #00c7ff;
        box-shadow: 0 0 0 3px rgba(0, 199, 255, 0.15),
                    0 0 15px rgba(0, 199, 255, 0.25);
        background-color: #0d0c1d;
    }
    
    /* 按钮样式 - 紫蓝渐变发光 */
    .stButton > button {
        background: linear-gradient(135deg, #9D7EFF 0%, #6366F1 100%);
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 0.95rem;
        line-height: 1;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 20px rgba(157, 126, 255, 0.4),
                    0 0 40px rgba(157, 126, 255, 0.2);
        position: relative;
        overflow: hidden;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        vertical-align: middle;
        text-align: center;
        min-height: 2.5rem;
    }
    
    /* 按钮内文字强制居中 */
    .stButton > button > div {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
    }
    
    /* 按钮文字垂直对齐 */
    .stButton > button * {
        vertical-align: middle;
        line-height: 1;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #A78BFF 0%, #7C7EFF 100%);
        box-shadow: 0 8px 32px rgba(157, 126, 255, 0.6),
                    0 0 60px rgba(157, 126, 255, 0.4);
        transform: translateY(-4px) scale(1.02);
    }
    
    .stButton > button:active {
        transform: translateY(-2px) scale(0.98);
    }
    
    /* 下载按钮样式 */
    .stDownloadButton > button {
        background: rgba(26, 25, 47, 0.8);
        color: #9D7EFF;
        border: 2px solid #9D7EFF;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 0.95rem;
        line-height: 1;
        transition: all 0.4s ease;
        box-shadow: 0 0 15px rgba(157, 126, 255, 0.25);
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        vertical-align: middle;
        text-align: center;
        min-height: 2.5rem;
    }
    
    /* 下载按钮内文字强制居中 */
    .stDownloadButton > button > div {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
    }
    
    /* 下载按钮文字垂直对齐 */
    .stDownloadButton > button * {
        vertical-align: middle;
        line-height: 1;
    }
    
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #9D7EFF 0%, #6366F1 100%);
        color: #FFFFFF;
        box-shadow: 0 4px 20px rgba(157, 126, 255, 0.4),
                    0 0 40px rgba(157, 126, 255, 0.3);
        transform: translateY(-4px);
    }
    
    /* 信息提示框样式 - 玻璃态 */
    .stAlert {
        background: rgba(26, 25, 47, 0.75);
        backdrop-filter: blur(12px);
        border-radius: 10px;
        border: 1px solid rgba(157, 126, 255, 0.3);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        animation: fadeIn 0.5s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* 成功提示 */
    .stSuccess {
        border-left: 4px solid #10B981;
        background: rgba(16, 185, 129, 0.1);
    }
    
    /* 警告提示 */
    .stWarning {
        border-left: 4px solid #F59E0B;
        background: rgba(245, 158, 11, 0.1);
    }
    
    /* 错误提示 */
    .stError {
        border-left: 4px solid #EF4444;
        background: rgba(239, 68, 68, 0.1);
    }
    
    /* 信息提示 */
    .stInfo {
        border-left: 4px solid #9D7EFF;
        background: rgba(157, 126, 255, 0.1);
    }
    
    /* 指标卡片样式 - 发光卡片 */
    [data-testid="stMetric"],
    [data-testid="stMetricValue"],
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, rgba(26, 25, 47, 0.8) 0%, rgba(26, 25, 47, 0.65) 100%);
        backdrop-filter: blur(12px);
        padding: 1.5rem !important;
        border-radius: 15px !important;
        border: 1px solid rgba(157, 126, 255, 0.3);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3),
                    0 0 30px rgba(157, 126, 255, 0.1);
        transition: all 0.4s ease;
    }
    
    [data-testid="stMetric"]:hover {
        border-color: rgba(157, 126, 255, 0.6);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.4),
                    0 0 40px rgba(157, 126, 255, 0.2);
        transform: translateY(-4px);
    }
    
    /* 分隔线样式 - 发光效果 */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, 
            transparent 0%, 
            rgba(157, 126, 255, 0.5) 50%, 
            transparent 100%);
        box-shadow: 0 0 10px rgba(157, 126, 255, 0.5);
        margin: 2rem 0;
    }
    
    /* 展开器样式 */
    .streamlit-expanderHeader {
        background: rgba(26, 25, 47, 0.65);
        backdrop-filter: blur(12px);
        border-radius: 12px;
        border: 1px solid rgba(157, 126, 255, 0.25);
        color: #e0e0e0;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(26, 25, 47, 0.85);
        border-color: rgba(157, 126, 255, 0.4);
        box-shadow: 0 4px 20px rgba(157, 126, 255, 0.2);
    }
    
    /* Radio按钮样式 - 自定义外观 */
    .stRadio > div {
        display: flex;
        flex-direction: column;
        gap: 15px;
        margin-bottom: 20px;
        background: transparent;
        padding: 0;
        border: none;
    }
    
    .stRadio > div > label {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        font-size: 0.95rem;
        font-weight: 400;
        line-height: 1.5;
        color: #b0b0d0;
        cursor: pointer;
        padding: 0.625rem;
        border-radius: 10px;
        transition: background-color 0.2s ease;
        vertical-align: middle;
    }
    
    .stRadio > div > label:hover {
        background-color: rgba(60, 50, 90, 0.2);
    }
    
    /* 自定义单选框圆圈 */
    .stRadio input[type="radio"] {
        appearance: none;
        -webkit-appearance: none;
        width: 20px;
        height: 20px;
        border-radius: 50%;
        border: 2px solid #6a4bff;
        margin-right: 0.75rem;
        flex-shrink: 0;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
        position: relative;
        cursor: pointer;
        vertical-align: middle;
    }
    
    .stRadio input[type="radio"]:checked {
        background: linear-gradient(45deg, #6a4bff, #00c7ff);
        border-color: transparent;
        box-shadow: 0 0 10px rgba(106, 75, 255, 0.6);
    }
    
    .stRadio input[type="radio"]:checked::before {
        content: '';
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #ffffff;
        position: absolute;
    }
    
    /* 侧边栏标题样式 */
    [data-testid="stSidebar"] h1 {
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 1.25rem;
        padding-bottom: 0.75rem;
        border-bottom: none;
        background: linear-gradient(90deg, #7e5bff, #00e0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 1.25rem;
        margin-bottom: 0.65rem;
        color: #ffcc00 !important;
    }
    
    /* 侧边栏文本 */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div:not(.stRadio) {
        font-size: 0.95rem;
        color: #d0d0e0 !important;
        line-height: 1.5;
    }
    
    /* 侧边栏分隔线 */
    [data-testid="stSidebar"] hr {
        border: none;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        margin: 20px 0;
    }
    
    /* 侧边栏信息提示框样式 */
    [data-testid="stSidebar"] .stAlert,
    [data-testid="stSidebar"] .element-container .stAlert {
        background-color: #2a284a !important;
        padding: 1rem;
        border-radius: 10px;
        color: #d0d0e0 !important;
        font-size: 0.95rem;
        line-height: 1.65;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        border: none !important;
        margin-top: 1rem;
    }
    
    [data-testid="stSidebar"] .stAlert * {
        color: #d0d0e0 !important;
    }
    
    /* 侧边栏指标卡片 */
    [data-testid="stSidebar"] [data-testid="stMetric"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0.5rem 0 !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetric"] label {
        color: #b0b0d0 !important;
        font-size: 0.9rem;
    }
    
    [data-testid="stSidebar"] [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 1.6rem;
        font-weight: 700;
    }
    
    /* 侧边栏Radio选项 */
    [data-testid="stSidebar"] .stRadio > label {
        display: none;
    }
    
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.5rem;
    }
    
    /* 导航项样式 - 参考您的设计 */
    [data-testid="stSidebar"] .stRadio > div > label {
        background: transparent;
        border: none;
        border-radius: 10px;
        padding: 0.625rem 1rem;
        margin-bottom: 0.5rem;
        transition: background-color 0.3s ease, color 0.3s ease, box-shadow 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: flex-start;
        line-height: 1.5;
        vertical-align: middle;
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: normal;
        color: #b0b0d0 !important;
    }
    
    /* 导航项悬停效果 */
    [data-testid="stSidebar"] .stRadio > div > label:hover {
        background-color: rgba(60, 50, 90, 0.4);
        color: #ffffff !important;
        box-shadow: none;
    }
    
    [data-testid="stSidebar"] .stRadio > div > label:hover * {
        color: #ffffff !important;
    }
    
    /* 选中导航项 - 紫蓝渐变发光 */
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background: linear-gradient(90deg, #6a4bff, #00c7ff);
        color: #FFFFFF !important;
        font-weight: bold;
        border: none;
        box-shadow: 0 0 15px rgba(106, 75, 255, 0.6);
    }
    
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] * {
        color: #FFFFFF !important;
    }
    
    /* 状态容器样式 */
    .stStatus {
        border-radius: 12px;
        background: rgba(26, 25, 47, 0.65);
        border: 1px solid rgba(157, 126, 255, 0.25);
        backdrop-filter: blur(12px);
    }
    
    /* 数据框样式 */
    .dataframe {
        background: rgba(26, 25, 47, 0.65);
        border: 1px solid rgba(157, 126, 255, 0.25) !important;
        border-radius: 12px;
        color: #e0e0e0;
    }
    
    /* 滚动条样式 - 紫蓝渐变 */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(13, 12, 29, 0.4);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #9D7EFF 0%, #6366F1 100%);
        border-radius: 5px;
        box-shadow: 0 0 10px rgba(157, 126, 255, 0.5);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #A78BFF 0%, #7C7EFF 100%);
        box-shadow: 0 0 20px rgba(157, 126, 255, 0.8);
    }
    
    /* 文件上传器样式 */
    [data-testid="stFileUploader"] {
        background: rgba(26, 25, 47, 0.65);
        border: 2px dashed rgba(157, 126, 255, 0.4);
        border-radius: 15px;
        padding: 2rem;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #9D7EFF;
        box-shadow: 0 0 30px rgba(157, 126, 255, 0.3);
    }
    
    /* Slider样式 */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #9D7EFF 0%, #6366F1 100%);
    }
    
    /* 加载动画增强 */
    .stSpinner > div {
        border-top-color: #9D7EFF !important;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* 信息提示框字号 */
    .stAlert p,
    .stInfo p,
    .stSuccess p,
    .stWarning p,
    .stError p {
        font-size: 0.9rem;
        line-height: 1.5;
    }
    
    /* 指标文字大小 */
    [data-testid="stMetric"] label {
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.75rem;
        font-weight: 700;
    }
    
    /* 链接样式 */
    a {
        color: #9D7EFF;
        text-decoration: none;
        transition: all 0.3s ease;
    }
    
    a:hover {
        color: #A78BFF;
        text-shadow: 0 0 10px rgba(157, 126, 255, 0.6);
    }
</style>
""", unsafe_allow_html=True)


# --- 3. 语言选择 & 翻译系统 ---
# 初始化语言选择
if 'language' not in st.session_state:
    st.session_state.language = '简体中文'

# 完整翻译字典
translations = {
    '简体中文': {
        # 主标题和导航
        'title': '【德美颜】AI增长架构师',
        'subtitle': '剥离运气，构建系统能力，实现智慧增长',
        'nav_title': '🚀 功能导航',
        'nav_demand': '需求洞察',
        'nav_ai': 'AI协作',
        'nav_lean': '精益复盘',
        'nav_history': '历史记录',
        'nav_dashboard': '数据看板',
        'tips_title': '💡 萱宜小贴士：',
        'stats_title': '📊 使用统计',
        'stats_demand': '需求分析次数',
        'stats_persona': '用户画像次数',
        'stats_mvp': 'MVP实验次数',
        
        # 需求洞察模块
        'demand_header': '🔍 【需求洞察引擎】',
        'demand_desc': '利用AI智能分析市场趋势与用户声音，锚定真正有价值的需求。',
        'choose_tool': '选择洞察工具：',
        'radar_agent': '「需求雷达Agent」',
        'persona_agent': '「用户画像建模Agent」',
        'radar_title': '🎯 「需求雷达Agent」',
        'keyword_label': '请输入您想分析的医美/创业关键词：',
        'keyword_placeholder': '例如：医美抗衰、AI工具提升效率、一人公司变现',
        'data_source_label': '模拟数据源类型：',
        'data_source_help': 'MVP阶段AI将模拟从这些类型的数据中进行分析。',
        'upload_title': '📂 上传调研报告（可选）',
        'upload_info': '💡 您可以上传现有的调研报告（PDF、Word、TXT等格式），AI将结合文件内容进行更深入的分析。',
        'choose_file': '选择文件上传：',
        'file_support': '支持格式：.txt, .md, .pdf, .docx',
        'view_file': '📄 查看上传文件信息',
        'file_name': '文件名',
        'file_size': '文件大小',
        'extracting': '正在提取文件内容...',
        'extract_success': '✅ 文件内容提取成功！共',
        'chars': '字符',
        'extract_fail': '❌ 文件内容提取失败，请检查文件格式是否正确。',
        'content_preview': '内容预览：',
        'start_insight': '开始洞察',
        'analyzing': 'AI正在启动需求雷达，深度分析市场中...',
        'analyzing_file': '正在分析上传的调研报告和',
        'about': '关于',
        'user_voice': '的用户声音...',
        'simulating': '正在模拟分析',
        'insight_complete': '洞察完成！',
        'saved': '分析已保存（ID:',
        'insight_result': '✅ 洞察结果：',
        
        # 用户画像Agent
        'persona_title': '👤 「用户画像建模Agent」',
        'user_desc': '请描述您的目标用户群体或产品/服务概念：',
        'user_placeholder': '例如：希望改善皮肤问题的25-35岁都市女性',
        'start_modeling': '开始建模',
        'modeling': 'AI正在构建用户画像，深入洞察目标用户...',
        'modeling_for': '正在为目标用户群体建模：',
        'modeling_complete': '建模完成！',
        'persona_result': '✅ 用户画像：',
        
        # AI协作模块
        'ai_collab_header': '🤝 【AI团队协作中心】',
        'ai_collab_desc': '召唤您的专属AI经理团队，协同推进产品和市场策略！',
        'project_overview': '📋 项目总览（为AI经理提供上下文）',
        'current_project': '当前项目名称：',
        'product_concept': '产品/服务核心概念：',
        'target_users': '主要目标用户画像：',
        'choose_manager': '选择您想召唤的AI经理：',
        'pm_agent': '「产品经理Agent」',
        'marketing_agent': '「市场经理Agent」',
        'medical_agent': '「医学经理Agent」',
        'social_agent': '「新媒体经理Agent」',
        'design_agent': '「设计经理Agent」',
        'pm_title': '👨‍💻 「产品经理Agent」',
        'pm_desc': '基于SSR框架，为您提供结构化的市场与用户洞察报告。',
        'use_insight': '📥 使用需求洞察报告的信息',
        'project_name_label': '【项目名称】（若与项目总览不同，可在此覆盖）：',
        'product_concept_label': '【产品概念】（若与项目总览不同，可在此覆盖）：',
        'target_users_label': '【目标用户画像】（若与项目总览不同，可在此覆盖）：',
        'output_language': '输出语言：',
        'generate_report': '生成产品策略报告',
        'pm_analyzing': '产品经理Agent正在分析并生成报告...',
        'pm_working': '正在运用SSR框架，模拟用户反馈...',
        
        # 精益复盘模块
        'lean_header': '📊 【精益复盘中心】',
        'lean_desc': '记录每一次MVP实验，数据驱动决策，持续优化增长策略。',
        'compass_title': '🧭 「数据罗盘Agent」',
        'compass_info': '💡 记录您的MVP实验数据，AI将辅助您进行深度复盘思考。',
        'experiment_name': '实验名称：',
        'experiment_placeholder': '例如：首页CTA按钮颜色测试',
        'hypothesis': '假设（您认为改进后会发生什么）：',
        'hypothesis_placeholder': '例如：将按钮从蓝色改为橙色，点击率会提升20%',
        'result': '实际结果（数据或观察）：',
        'result_placeholder': '例如：点击率从2.5%提升至3.1%，提升24%',
        'submit_think': '提交并让AI辅助思考',
        'thinking': 'AI数据罗盘正在为您分析实验数据，提供洞察与建议...',
        'thinking_complete': '复盘完成！',
        'retro_result': '✅ 复盘洞察：',
        
        # 历史记录模块
        'history_header': '📚 【历史记录】',
        'history_desc': '回顾所有洞察与实验记录，发现规律与趋势。',
        'view_type': '查看类型：',
        'demand_analysis': '需求分析',
        'user_personas': '用户画像',
        'mvp_experiments': 'MVP实验',
        'demand_history_title': '🎯 需求雷达分析历史',
        'persona_history_title': '👤 用户画像建模历史',
        'mvp_history_title': '📊 MVP实验复盘历史',
        'total_records': '共',
        'records': '条记录',
        'no_records': '暂无历史记录',
        'page': '第',
        'of': '/',
        'pages': '页',
        'prev_page': '◀ 上一页',
        'next_page': '下一页 ▶',
        
        # 数据看板模块
        'dashboard_header': '📊 【数据看板】',
        'dashboard_desc': '可视化您的增长数据，一目了然掌握趋势。',
        'total_demand': '需求分析总数',
        'total_persona': '用户画像总数',
        'total_mvp': 'MVP实验总数',
        'trend_title': '📈 分析趋势（最近30天）',
        'demand_trend': '需求分析趋势',
        'persona_trend': '用户画像趋势',
        'mvp_trend': 'MVP实验趋势',
        'date': '日期',
        'count': '数量',
        
        # 其他
        'social_media': '社交媒体讨论',
        'ecommerce': '电商评论',
        'industry_report': '行业报告摘要',
        'export_md': '📥 导出为Markdown',
        'export_pdf': '📥 导出为PDF',
        'export_success': '✅ 导出成功！',
    },
    'English': {
        # Main titles and navigation
        'title': '【DeMeiYan】AI Growth Architect',
        'subtitle': 'Strip Luck, Build Systematic Capability, Achieve Intelligent Growth',
        'nav_title': '🚀 Navigation',
        'nav_demand': 'Demand Insights',
        'nav_ai': 'AI Collaboration',
        'nav_lean': 'Lean Retrospective',
        'nav_history': 'History',
        'nav_dashboard': 'Dashboard',
        'tips_title': '💡 Pro Tips:',
        'stats_title': '📊 Statistics',
        'stats_demand': 'Demand Analyses',
        'stats_persona': 'User Personas',
        'stats_mvp': 'MVP Experiments',
        
        # Demand Insights Module
        'demand_header': '🔍 【Demand Insights Engine】',
        'demand_desc': 'Leverage AI to analyze market trends and user voices, pinpointing truly valuable demands.',
        'choose_tool': 'Choose Insights Tool:',
        'radar_agent': '「Demand Radar Agent」',
        'persona_agent': '「User Persona Agent」',
        'radar_title': '🎯 「Demand Radar Agent」',
        'keyword_label': 'Enter your keyword for analysis:',
        'keyword_placeholder': 'e.g.: Anti-aging skincare, AI productivity tools, Solopreneur monetization',
        'data_source_label': 'Simulated Data Source Type:',
        'data_source_help': 'In MVP phase, AI will simulate analysis from these data types.',
        'upload_title': '📂 Upload Research Report (Optional)',
        'upload_info': '💡 You can upload existing research reports (PDF, Word, TXT formats). AI will combine file content for deeper analysis.',
        'choose_file': 'Choose file to upload:',
        'file_support': 'Supported formats: .txt, .md, .pdf, .docx',
        'view_file': '📄 View Upload File Info',
        'file_name': 'File Name',
        'file_size': 'File Size',
        'extracting': 'Extracting file content...',
        'extract_success': '✅ File content extracted successfully!',
        'chars': 'characters',
        'extract_fail': '❌ File content extraction failed. Please check file format.',
        'content_preview': 'Content Preview:',
        'start_insight': 'Start Analysis',
        'analyzing': 'AI Demand Radar is analyzing the market...',
        'analyzing_file': 'Analyzing uploaded report and',
        'about': 'about',
        'user_voice': 'user discussions...',
        'simulating': 'Simulating analysis of',
        'insight_complete': 'Analysis Complete!',
        'saved': 'Analysis saved (ID:',
        'insight_result': '✅ Analysis Result:',
        
        # User Persona Agent
        'persona_title': '👤 「User Persona Agent」',
        'user_desc': 'Describe your target user group or product/service concept:',
        'user_placeholder': 'e.g.: Urban women aged 25-35 seeking skin improvement',
        'start_modeling': 'Start Modeling',
        'modeling': 'AI is building user persona, diving deep into target users...',
        'modeling_for': 'Building persona for target user group:',
        'modeling_complete': 'Modeling Complete!',
        'persona_result': '✅ User Persona:',
        
        # AI Collaboration Module
        'ai_collab_header': '🤝 【AI Team Collaboration Center】',
        'ai_collab_desc': 'Summon your dedicated AI manager team to collaboratively advance product and market strategies!',
        'project_overview': '📋 Project Overview (Providing Context for AI Managers)',
        'current_project': 'Current Project Name:',
        'product_concept': 'Product/Service Core Concept:',
        'target_users': 'Target User Personas:',
        'choose_manager': 'Choose the AI Manager you want to summon:',
        'pm_agent': '「Product Manager Agent」',
        'marketing_agent': '「Marketing Manager Agent」',
        'medical_agent': '「Medical Manager Agent」',
        'social_agent': '「Social Media Manager Agent」',
        'design_agent': '「Design Manager Agent」',
        'pm_title': '👨‍💻 「Product Manager Agent」',
        'pm_desc': 'Based on SSR framework, provides structured market and user insight reports.',
        'use_insight': '📥 Use Information from Demand Insights',
        'project_name_label': '【Project Name】 (Override if different from project overview):',
        'product_concept_label': '【Product Concept】 (Override if different from project overview):',
        'target_users_label': '【Target User Persona】 (Override if different from project overview):',
        'output_language': 'Output Language:',
        'generate_report': 'Generate Product Strategy Report',
        'pm_analyzing': 'Product Manager Agent is analyzing and generating report...',
        'pm_working': 'Applying SSR framework, simulating user feedback...',
        
        # Lean Retrospective Module
        'lean_header': '📊 【Lean Retrospective Center】',
        'lean_desc': 'Record every MVP experiment, make data-driven decisions, continuously optimize growth strategies.',
        'compass_title': '🧭 「Data Compass Agent」',
        'compass_info': '💡 Record your MVP experiment data, AI will assist you with in-depth retrospective thinking.',
        'experiment_name': 'Experiment Name:',
        'experiment_placeholder': 'e.g.: Homepage CTA button color test',
        'hypothesis': 'Hypothesis (what you expect to happen):',
        'hypothesis_placeholder': 'e.g.: Changing button from blue to orange will increase CTR by 20%',
        'result': 'Actual Result (data or observation):',
        'result_placeholder': 'e.g.: CTR increased from 2.5% to 3.1%, up 24%',
        'submit_think': 'Submit for AI Analysis',
        'thinking': 'AI Data Compass is analyzing your experiment data and providing insights...',
        'thinking_complete': 'Retrospective Complete!',
        'retro_result': '✅ Retrospective Insights:',
        
        # History Module
        'history_header': '📚 【History】',
        'history_desc': 'Review all insights and experiment records, discover patterns and trends.',
        'view_type': 'View Type:',
        'demand_analysis': 'Demand Analysis',
        'user_personas': 'User Personas',
        'mvp_experiments': 'MVP Experiments',
        'demand_history_title': '🎯 Demand Radar Analysis History',
        'persona_history_title': '👤 User Persona Modeling History',
        'mvp_history_title': '📊 MVP Experiment Retrospective History',
        'total_records': 'Total',
        'records': 'records',
        'no_records': 'No history records',
        'page': 'Page',
        'of': 'of',
        'pages': '',
        'prev_page': '◀ Previous',
        'next_page': 'Next ▶',
        
        # Dashboard Module
        'dashboard_header': '📊 【Dashboard】',
        'dashboard_desc': 'Visualize your growth data, grasp trends at a glance.',
        'total_demand': 'Total Demand Analyses',
        'total_persona': 'Total User Personas',
        'total_mvp': 'Total MVP Experiments',
        'trend_title': '📈 Analysis Trend (Last 30 Days)',
        'demand_trend': 'Demand Analysis Trend',
        'persona_trend': 'User Persona Trend',
        'mvp_trend': 'MVP Experiment Trend',
        'date': 'Date',
        'count': 'Count',
        
        # Others
        'social_media': 'Social Media Discussions',
        'ecommerce': 'E-commerce Reviews',
        'industry_report': 'Industry Report Summary',
        'export_md': '📥 Export as Markdown',
        'export_pdf': '📥 Export as PDF',
        'export_success': '✅ Export successful!',
    }
}

# 侧边栏语言选择器
st.sidebar.selectbox(
    "🌐 Language / 语言",
    options=['简体中文', 'English'],
    key='language',
    label_visibility="visible"
)

t = translations[st.session_state.language]

# --- 4. 主标题区域 ---
st.markdown(f"""
<div style='text-align: center; margin-bottom: 3rem; padding: 1rem 0;'>
    <h1 style='background: linear-gradient(90deg, #7e5bff, #00e0ff); 
               -webkit-background-clip: text; 
               -webkit-text-fill-color: transparent;
               font-size: 2.8rem;
               font-weight: 700;
               margin-bottom: 0.75rem;
               line-height: 1.2;
               letter-spacing: 0.01em;'>
        {t['title']}
    </h1>
    <p style='color: #9d7eff; font-size: 1rem; margin: 0.5rem 0; font-weight: 500; letter-spacing: 0.1em;'>（MVP）</p>
    <p style='color: #b0b0d0; font-size: 1rem; margin-top: 0.75rem; opacity: 0.9;'>{t['subtitle']}</p>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# --- 5. 侧边栏导航 ---

st.sidebar.markdown("---")
st.sidebar.title(t['nav_title'])
selected_function = st.sidebar.radio(
    "选择功能模块",
    (t['nav_demand'], t['nav_ai'], t['nav_lean'], t['nav_history'], t['nav_dashboard']),
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.subheader(t['tips_title'])

# 提示信息翻译
tips = {
    '简体中文': {
        t['nav_demand']: "真需求是普遍、强烈、频繁的！多尝试不同的关键词，对比AI的洞察结果，找到市场的核心痛点。",
        t['nav_lean']: "精益增长，始于数据，成于认知。每次实验，无论成败，都是宝贵的学习机会！",
        t['nav_history']: "回顾过往分析，从历史中发现规律和趋势，让每一次洞察都成为未来决策的基石。",
        t['nav_dashboard']: "数据可视化让趋势一目了然，帮助您快速把握增长节奏。",
        t['nav_ai']: "您的专属AI团队已就位！请清晰地给出指令，让AI经理们协同助您增长。"
    },
    'English': {
        t['nav_demand']: "Real demand is universal, strong, and frequent! Try different keywords to compare AI insights and find core market pain points.",
        t['nav_lean']: "Lean growth starts with data and succeeds with insight. Every experiment, success or failure, is a valuable learning opportunity!",
        t['nav_history']: "Review past analyses to discover patterns and trends, making each insight a cornerstone for future decisions.",
        t['nav_dashboard']: "Data visualization makes trends clear at a glance, helping you quickly grasp growth momentum.",
        t['nav_ai']: "Your dedicated AI team is ready! Give clear instructions and let AI managers collaborate to boost your growth."
    }
}

if selected_function in tips[st.session_state.language]:
    st.sidebar.info(tips[st.session_state.language][selected_function])

# 显示统计数据
stats = db.get_experiment_stats()
st.sidebar.markdown("---")
st.sidebar.subheader(t['stats_title'])
st.sidebar.metric(t['stats_demand'], stats['total_analyses'])
st.sidebar.metric(t['stats_persona'], stats['total_personas'])
st.sidebar.metric(t['stats_mvp'], stats['total_experiments'])


# --- 4. 功能模块实现 ---

# --- 模块一：需求洞察 ---
if selected_function == t['nav_demand']:
    st.header(t['demand_header'])
    st.write(t['demand_desc'])

    insight_tool = st.radio(
        t['choose_tool'],
        (t['radar_agent'], t['persona_agent']),
        key="insight_tool_radio"
    )
    st.markdown("---")

    if insight_tool == t['radar_agent']:
        st.subheader(t['radar_title'])
        keyword = st.text_input(
            t['keyword_label'],
            "皮肤屏障修复" if st.session_state.language == '简体中文' else "Skin barrier repair",
            placeholder=t['keyword_placeholder']
        )
        data_source = st.radio(
            t['data_source_label'],
            (t['social_media'], t['ecommerce'], t['industry_report']),
            index=0,
            help=t['data_source_help']
        )
        
        # 添加文件上传功能
        st.markdown("---")
        st.markdown(f"#### {t['upload_title']}")
        st.info(t['upload_info'])
        
        uploaded_file = st.file_uploader(
            t['choose_file'],
            type=['txt', 'md', 'pdf', 'docx'],
            help=t['file_support'],
            key="radar_file_upload"
        )
        
        # 显示上传文件信息
        file_content = None
        if uploaded_file is not None:
            with st.expander(t['view_file'], expanded=False):
                st.write(f"**{t['file_name']}**: {uploaded_file.name}")
                st.write(f"**{t['file_size']}**: {uploaded_file.size / 1024:.2f} KB")
                
                with st.spinner(t['extracting']):
                    file_content = extract_file_content(uploaded_file)
                    
                if file_content:
                    st.success(f"{t['extract_success']} {len(file_content)} {t['chars']}")
                    # 显示前500字符作为预览
                    preview_text = file_content[:500] + ("..." if len(file_content) > 500 else "")
                    st.text_area(t['content_preview'], preview_text, height=150, disabled=True)
                else:
                    st.error(t['extract_fail'])
        
        st.markdown("---")

        if st.button(t['start_insight'], key="run_radar"):
            if keyword:
                with st.status(t['analyzing'], expanded=True) as status:
                    if file_content:
                        st.write(f"{t['analyzing_file']} '{data_source}' {t['about']} '{keyword}' {t['user_voice']}")
                    else:
                        st.write(f"{t['simulating']} '{data_source}' {t['about']} '{keyword}' {t['user_voice']}")
                    time.sleep(2)
                    try:
                        # 构建基础提示词
                        radar_prompt = f"""
                        你是一位拥有15年医美行业和创业市场分析经验的资深专家，现在你的任务是扮演"需求雷达Agent"。
                        你的目标是根据用户提供的关键词{' 和调研报告' if file_content else ''}，模拟分析当前互联网上（特别是{data_source}）关于此关键词的讨论，
                        洞察并总结市场中**普遍、强烈、频繁**出现的真实需求和痛点。

                        请以清晰的Markdown格式输出，内容应包含以下四个部分：

                        ### 1. 核心痛点提炼
                        - 列举3-5个最常被提及的、困扰用户的问题点。
                        - 提炼的痛点应具体，而非泛泛而谈。

                        ### 2. 用户情绪分析
                        - 总结用户对这些痛点和现有解决方案的整体情绪倾向（如：焦虑、期待、不满、兴奋等），并举例说明。
                        - 说明情绪来源和驱动因素。

                        ### 3. 真需求识别（基于"普遍、强烈、频繁"标准）
                        - 从提炼的痛点中，识别出1-3个最具潜力的"真需求"，即符合"普遍性、强烈性、频繁性"标准的深层需求。
                        - 解释为什么这些是真需求，它们如何未被充分满足。

                        ### 4. 市场机会点简述
                        - 针对识别出的真需求，提供2-3个初步的市场机会点思考，例如可以开发的产品方向、服务模式或创新点。

                        用户输入的关键词是：'{keyword}'
                        """
                        
                        # 构建用户提示词，加入文件内容
                        if file_content:
                            # 限制文件内容长度，避免超过API限制
                            max_file_length = 8000
                            truncated_content = file_content[:max_file_length] + ("...\n[文件内容过长，已截取前8000字符]" if len(file_content) > max_file_length else "")
                            
                            user_prompt = f"""
请针对关键词 '{keyword}' 进行深入分析。

用户已上传调研报告文件（{uploaded_file.name}），以下是文件内容摘要：

---
{truncated_content}
---

请结合以上调研报告的内容和你对市场的理解，进行全面的需求分析。
                            """
                        else:
                            user_prompt = f"请针对关键词 '{keyword}' 进行分析。"

                        analysis_result = call_gemini(
                            system_prompt=radar_prompt,
                            user_prompt=user_prompt,
                            model="gemini-2.5-flash"
                        )
                        
                        # 保存到数据库和session_state
                        saved_id = db.save_demand_analysis(keyword, data_source, analysis_result)
                        st.session_state['radar_report'] = analysis_result
                        st.session_state['radar_keyword'] = keyword
                        st.session_state['radar_data_source'] = data_source
                        
                        status.update(label=t['insight_complete'], state="complete", expanded=False)
                        st.success(f"✅ {t['saved']} {saved_id}）")
                        st.subheader(t['insight_result'])
                        st.markdown(analysis_result)
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.download_button(
                                label="📥 导出为Markdown",
                                data=f"# 需求雷达分析\n\n**关键词**: {keyword}\n**数据源**: {data_source}\n**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{analysis_result}",
                                file_name=f"需求分析_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown"
                            ):
                                st.success("文件已准备下载！")
                        with col2:
                            pdf_data = generate_pdf_report(
                                title="需求雷达分析",
                                content=analysis_result,
                                metadata={
                                    "关键词": keyword,
                                    "数据源": data_source,
                                    "分析时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                }
                            )
                            if st.download_button(
                                label="📄 导出为PDF",
                                data=pdf_data,
                                file_name=f"需求分析_{keyword}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf"
                            ):
                                st.success("PDF已准备下载！")

                    except Exception as e:
                        status.update(label="洞察失败！", state="error", expanded=True)
                        st.error(f"分析失败，请检查API Key或稍后重试: {e}")
            else:
                st.warning("请输入关键词才能进行分析哦！")

    elif insight_tool == t['persona_agent']:
        st.subheader(t['persona_title'])
        default_text_cn = """我是一名35岁的公司白领，最近经常熬夜加班，皮肤变得很暗沉，还老是长痘。
我很想改善，但市面上太多产品了，不知道哪个适合我，怕踩雷。
也去过医美机构咨询，但觉得推销太厉害，价格也不透明。
希望能有一种产品能真正改善我的皮肤，最好是能长期调理，而不是短期见效后就反弹。
对那种'网红'产品不太信任，更看重成分和科学依据。"""
        default_text_en = """I'm a 35-year-old office worker who frequently stays up late for work. My skin has become dull and I keep getting breakouts.
I want to improve my skin, but there are so many products on the market. I don't know which one suits me and I'm afraid of making the wrong choice.
I've consulted with medical aesthetics clinics, but felt the sales pressure was too strong and pricing was not transparent.
I hope to find a product that can truly improve my skin, preferably with long-term conditioning rather than short-term effects followed by rebound.
I don't trust 'influencer' products much, and I value ingredients and scientific evidence more."""
        user_text = st.text_area(
            t['user_desc'],
            default_text_cn if st.session_state.language == '简体中文' else default_text_en,
            height=250,
            placeholder=t['user_placeholder']
        )

        if st.button(t['start_modeling'], key="run_persona"):
            if user_text:
                with st.status(t['modeling'], expanded=True) as status:
                    st.write(f"{t['modeling_for']} {user_text[:50]}...")
                    time.sleep(1.5)
                    try:
                        persona_prompt = f"""
                        你是一位专业的用户研究专家，现在你的任务是扮演"用户画像建模Agent"。
                        请根据用户提供的文本信息，深度分析并提炼出核心用户画像。

                        请以清晰的Markdown格式输出，内容应包含以下四个部分：

                        ### 1. 核心痛点与焦虑
                        - 总结用户当前面临的主要问题和困扰。

                        ### 2. 未满足的需求
                        - 从痛点出发，推断用户深层、尚未被有效满足的需求。

                        ### 3. 用户特征与偏好
                        - 提取文本中暗示的用户基本特征（如年龄段、职业、生活习惯等）。
                        - 总结用户的购买决策偏好、对产品/服务的期望、信任来源等。

                        ### 4. 潜在市场机会
                        - 基于用户画像的洞察，提供2-3个潜在的产品或服务优化机会点。

                        用户提供的文本是：
                        ```
                        {user_text}
                        ```
                        """

                        persona_result = call_gemini(
                            system_prompt=persona_prompt,
                            user_prompt=f"请对以下用户描述进行画像建模：\n{user_text}",
                            model="gemini-2.5-flash"
                        )
                        
                        # 保存到数据库和session_state
                        saved_id = db.save_user_persona(user_text, persona_result)
                        st.session_state['persona_report'] = persona_result
                        st.session_state['persona_user_text'] = user_text
                        
                        status.update(label=t['modeling_complete'], state="complete", expanded=False)
                        st.success(f"✅ {t['saved']} {saved_id}）")
                        st.subheader(t['persona_result'])
                        st.markdown(persona_result)
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.download_button(
                                label="📥 导出为Markdown",
                                data=f"# 用户画像分析\n\n**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n## 用户原文\n\n{user_text}\n\n## 分析结果\n\n{persona_result}",
                                file_name=f"用户画像_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown"
                            ):
                                st.success("文件已准备下载！")
                        with col2:
                            pdf_data = generate_pdf_report(
                                title="用户画像分析",
                                content=f"## 用户原文\n\n{user_text}\n\n## 分析结果\n\n{persona_result}",
                                metadata={"分析时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            )
                            if st.download_button(
                                label="📄 导出为PDF",
                                data=pdf_data,
                                file_name=f"用户画像_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf"
                            ):
                                st.success("PDF已准备下载！")

                    except Exception as e:
                        status.update(label="画像构建失败！", state="error", expanded=True)
                        st.error(f"构建用户画像失败，请检查API Key或稍后重试: {e}")
            else:
                st.warning("请输入用户文本才能进行画像建模哦！")


# --- 模块二：【精益复盘中心】---
elif selected_function == t['nav_lean']:
    st.header(t['lean_header'])
    st.write(t['lean_desc'])

    st.subheader(t['compass_title'])
    st.info(t['compass_info'])

    experiment_name = st.text_input(t['experiment_name'], 
                                    "首次用户需求验证MVP" if st.session_state.language == '简体中文' else "First user demand validation MVP")
    experiment_goal = st.text_area("本次MVP的核心目标是什么？" if st.session_state.language == '简体中文' else "What is the core goal of this MVP?", 
                                  "验证用户对'个性化皮肤屏障修复方案'的真实兴趣和付费意愿" if st.session_state.language == '简体中文' else "Validate user interest and willingness to pay for 'personalized skin barrier repair solutions'", height=100)
    metrics_data = st.text_area(t['result'] if 'result' in t else "关键数据和观察：",
                                "测试了20位用户，其中15位表示有强烈兴趣，5位表示价格过高。收到10条积极反馈，3条负面反馈集中在价格。" if st.session_state.language == '简体中文' else "Tested with 20 users, 15 showed strong interest, 5 felt price was too high. Received 10 positive feedbacks, 3 negative feedbacks focused on pricing.", height=200)

    if st.button(t['submit_think'], key="run_compass"):
        if experiment_name and experiment_goal and metrics_data:
            with st.status(t['thinking'], expanded=True) as status:
                st.write("正在分析您的实验数据和目标..." if st.session_state.language == '简体中文' else "Analyzing your experiment data and goals...")
                time.sleep(2)
                try:
                    compass_prompt = f"""
                    你是一位经验丰富的精益创业导师，现在你的任务是扮演"数据罗盘Agent"。
                    请根据用户提供的MVP实验信息，引导用户进行结构化复盘，并帮助他们从数据中提炼"经证实的认知"。

                    请以清晰的Markdown格式输出，内容应包含以下三个部分：

                    ### 1. 实验回顾与数据摘要
                    - 简要回顾本次实验的目标和关键数据。

                    ### 2. AI辅助思考：经证实的认知
                    - 结合实验目标和数据，引导用户思考：
                        - "本次实验中，哪些假设得到了验证？哪些被证伪？"
                        - "用户真正的痛点和需求是什么？是否与我们最初的设想一致？"
                        - "哪些地方超出了预期？哪些地方低于预期？"
                    - 请不要直接给出结论，而是提出启发性的问题，帮助用户自己得出"经证实的认知"。

                    ### 3. 下一步行动建议（启发式）
                    - 基于上述思考，为用户提供2-3个启发性的、可迭代的下一步行动建议，例如：
                        - "是否需要调整MVP的功能？"
                        - "是否需要重新定义目标用户？"
                        - "是否需要优化定价策略？"
                        - "下一次实验的目标应该是什么？"

                    用户提供的实验信息如下：
                    - 实验名称: {experiment_name}
                    - 实验目标: {experiment_goal}
                    - 关键数据和观察: {metrics_data}
                    """

                    compass_result = call_gemini(
                        system_prompt=compass_prompt,
                        user_prompt=f"请帮助我复盘名为'{experiment_name}'的MVP实验。",
                        model="gemini-2.5-flash"
                    )
                    
                    saved_id = db.save_mvp_experiment(experiment_name, experiment_goal, metrics_data, compass_result)
                    
                    status.update(label=t['thinking_complete'], state="complete", expanded=False)
                    st.success(f"✅ {t['saved']} {saved_id}）")
                    st.subheader(t['retro_result'])
                    st.markdown(compass_result)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.download_button(
                            label="📥 导出为Markdown",
                            data=f"# MVP实验复盘\n\n**实验名称**: {experiment_name}\n**实验时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n## 实验目标\n\n{experiment_goal}\n\n## 关键数据\n\n{metrics_data}\n\n## AI复盘分析\n\n{compass_result}",
                            file_name=f"MVP复盘_{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown"
                        ):
                            st.success("文件已准备下载！")
                    with col2:
                        pdf_data = generate_pdf_report(
                            title="MVP实验复盘",
                            content=f"## 实验目标\n\n{experiment_goal}\n\n## 关键数据\n\n{metrics_data}\n\n## AI复盘分析\n\n{compass_result}",
                            metadata={
                                "实验名称": experiment_name,
                                "实验时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            }
                        )
                        if st.download_button(
                            label="📄 导出为PDF",
                            data=pdf_data,
                            file_name=f"MVP复盘_{experiment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        ):
                            st.success("PDF已准备下载！")

                except Exception as e:
                    status.update(label="复盘失败！", state="error", expanded=True)
                    st.error(f"复盘失败，请检查API Key或稍后重试: {e}")
        else:
            st.warning("请填写所有实验信息才能进行复盘哦！")


# --- 模块三：【历史记录】---
elif selected_function == t['nav_history']:
    st.header(t['history_header'])
    st.write(t['history_desc'])
    
    tabs_labels = [t['demand_analysis'], t['user_personas'], t['mvp_experiments']]
    tab1, tab2, tab3 = st.tabs(tabs_labels)
    
    with tab1:
        st.subheader(t['demand_history_title'])
        
        if 'analysis_page' not in st.session_state:
            st.session_state.analysis_page = 0
        
        total_analyses = db.get_demand_analyses_count()
        items_per_page = 10
        total_pages = max(1, (total_analyses + items_per_page - 1) // items_per_page)
        
        if total_analyses > 0:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button(t['prev_page'], key="prev_analysis", disabled=st.session_state.analysis_page == 0):
                    st.session_state.analysis_page -= 1
                    st.rerun()
            with col2:
                if st.session_state.language == '简体中文':
                    page_info = f"第 {st.session_state.analysis_page + 1} / {total_pages} 页 （共 {total_analyses} 条）"
                else:
                    page_info = f"Page {st.session_state.analysis_page + 1} of {total_pages} (Total: {total_analyses} records)"
                st.markdown(f"<div style='text-align: center'>{page_info}</div>", unsafe_allow_html=True)
            with col3:
                if st.button(t['next_page'], key="next_analysis", disabled=st.session_state.analysis_page >= total_pages - 1):
                    st.session_state.analysis_page += 1
                    st.rerun()
        
        analyses = db.get_demand_analyses(limit=items_per_page, offset=st.session_state.analysis_page * items_per_page)
        if analyses:
            for analysis in analyses:
                with st.expander(f"📊 {analysis['keyword']} - {analysis['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                    st.markdown(f"**数据源**: {analysis['data_source']}")
                    st.markdown("---")
                    st.markdown(analysis['analysis_result'])
                    if st.download_button(
                        label="📥 导出",
                        data=f"# 需求雷达分析\n\n**关键词**: {analysis['keyword']}\n**数据源**: {analysis['data_source']}\n**分析时间**: {analysis['created_at']}\n\n{analysis['analysis_result']}",
                        file_name=f"需求分析_{analysis['keyword']}_{analysis['id']}.md",
                        mime="text/markdown",
                        key=f"download_analysis_{analysis['id']}"
                    ):
                        st.success("已导出！")
        else:
            st.info("暂无需求分析记录，快去试试「需求雷达Agent」吧！")
    
    with tab2:
        st.subheader(t['persona_history_title'])
        
        if 'persona_page' not in st.session_state:
            st.session_state.persona_page = 0
        
        total_personas = db.get_user_personas_count()
        items_per_page = 10
        total_pages = max(1, (total_personas + items_per_page - 1) // items_per_page)
        
        if total_personas > 0:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button(t['prev_page'], key="prev_persona", disabled=st.session_state.persona_page == 0):
                    st.session_state.persona_page -= 1
                    st.rerun()
            with col2:
                if st.session_state.language == '简体中文':
                    page_info = f"第 {st.session_state.persona_page + 1} / {total_pages} 页 （共 {total_personas} 条）"
                else:
                    page_info = f"Page {st.session_state.persona_page + 1} of {total_pages} (Total: {total_personas} records)"
                st.markdown(f"<div style='text-align: center'>{page_info}</div>", unsafe_allow_html=True)
            with col3:
                if st.button(t['next_page'], key="next_persona", disabled=st.session_state.persona_page >= total_pages - 1):
                    st.session_state.persona_page += 1
                    st.rerun()
        
        personas = db.get_user_personas(limit=items_per_page, offset=st.session_state.persona_page * items_per_page)
        if personas:
            for persona in personas:
                with st.expander(f"👥 {persona['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                    st.markdown("**用户原文**:")
                    st.text(persona['user_text'][:200] + "..." if len(persona['user_text']) > 200 else persona['user_text'])
                    st.markdown("---")
                    st.markdown(persona['persona_result'])
                    if st.download_button(
                        label="📥 导出",
                        data=f"# 用户画像分析\n\n**分析时间**: {persona['created_at']}\n\n## 用户原文\n\n{persona['user_text']}\n\n## 分析结果\n\n{persona['persona_result']}",
                        file_name=f"用户画像_{persona['id']}.md",
                        mime="text/markdown",
                        key=f"download_persona_{persona['id']}"
                    ):
                        st.success("已导出！")
        else:
            st.info("暂无用户画像记录，快去试试「用户画像建模Agent」吧！")
    
    with tab3:
        st.subheader(t['mvp_history_title'])
        
        if 'experiment_page' not in st.session_state:
            st.session_state.experiment_page = 0
        
        total_experiments = db.get_mvp_experiments_count()
        items_per_page = 10
        total_pages = max(1, (total_experiments + items_per_page - 1) // items_per_page)
        
        experiments = db.get_mvp_experiments(limit=total_experiments)
        
        if experiments and len(experiments) >= 2:
            st.markdown("### 实验对比")
            exp_names = [f"{exp['experiment_name']} ({exp['created_at'].strftime('%m-%d')})" for exp in experiments]
            selected_exps = st.multiselect("选择实验进行对比（最多选3个）", exp_names, max_selections=3)
            
            if len(selected_exps) >= 2:
                st.markdown("#### 对比视图")
                cols = st.columns(len(selected_exps))
                for idx, exp_name in enumerate(selected_exps):
                    exp_idx = exp_names.index(exp_name)
                    exp = experiments[exp_idx]
                    with cols[idx]:
                        st.markdown(f"**{exp['experiment_name']}**")
                        st.caption(exp['created_at'].strftime('%Y-%m-%d'))
                        st.markdown(f"**目标**: {exp['experiment_goal'][:100]}...")
                        st.markdown(f"**数据**: {exp['metrics_data'][:100]}...")
        
        if total_experiments > 0:
            st.markdown("---")
            st.markdown("### 所有实验记录")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button(t['prev_page'], key="prev_experiment", disabled=st.session_state.experiment_page == 0):
                    st.session_state.experiment_page -= 1
                    st.rerun()
            with col2:
                if st.session_state.language == '简体中文':
                    page_info = f"第 {st.session_state.experiment_page + 1} / {total_pages} 页 （共 {total_experiments} 条）"
                else:
                    page_info = f"Page {st.session_state.experiment_page + 1} of {total_pages} (Total: {total_experiments} records)"
                st.markdown(f"<div style='text-align: center'>{page_info}</div>", unsafe_allow_html=True)
            with col3:
                if st.button(t['next_page'], key="next_experiment", disabled=st.session_state.experiment_page >= total_pages - 1):
                    st.session_state.experiment_page += 1
                    st.rerun()
        
        page_experiments = db.get_mvp_experiments(limit=items_per_page, offset=st.session_state.experiment_page * items_per_page)
        if page_experiments:
            for experiment in page_experiments:
                with st.expander(f"🧪 {experiment['experiment_name']} - {experiment['created_at'].strftime('%Y-%m-%d %H:%M')}"):
                    st.markdown(f"**实验目标**: {experiment['experiment_goal']}")
                    st.markdown(f"**关键数据**: {experiment['metrics_data']}")
                    st.markdown("---")
                    st.markdown("**AI复盘分析**:")
                    st.markdown(experiment['compass_result'])
                    if st.download_button(
                        label="📥 导出",
                        data=f"# MVP实验复盘\n\n**实验名称**: {experiment['experiment_name']}\n**实验时间**: {experiment['created_at']}\n\n## 实验目标\n\n{experiment['experiment_goal']}\n\n## 关键数据\n\n{experiment['metrics_data']}\n\n## AI复盘分析\n\n{experiment['compass_result']}",
                        file_name=f"MVP复盘_{experiment['experiment_name']}_{experiment['id']}.md",
                        mime="text/markdown",
                        key=f"download_experiment_{experiment['id']}"
                    ):
                        st.success("已导出！")
        else:
            st.info("暂无实验记录，快去试试「数据罗盘Agent」吧！")


# --- 模块四：【数据看板】---
elif selected_function == t['nav_dashboard']:
    st.header(t['dashboard_header'])
    st.write(t['dashboard_desc'])
    
    experiments = db.get_mvp_experiments(limit=10)
    analyses = db.get_demand_analyses(limit=10)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总实验次数", stats['total_experiments'])
    with col2:
        st.metric("需求分析次数", stats['total_analyses'])
    with col3:
        st.metric("用户画像次数", stats['total_personas'])
    
    st.markdown("---")
    
    if experiments:
        st.subheader("📈 MVP实验时间线")
        exp_dates = [exp['created_at'] for exp in reversed(experiments)]
        exp_names = [exp['experiment_name'] for exp in reversed(experiments)]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=exp_dates,
            y=list(range(1, len(exp_dates) + 1)),
            mode='lines+markers',
            name='实验次数',
            line=dict(color='#FF6B6B', width=2),
            marker=dict(size=10)
        ))
        fig.update_layout(
            title="实验累计趋势",
            xaxis_title="时间",
            yaxis_title="累计实验次数",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("🎯 近期实验概览")
        for exp in experiments[:5]:
            st.markdown(f"- **{exp['experiment_name']}** ({exp['created_at'].strftime('%Y-%m-%d')})")
    
    if analyses:
        st.markdown("---")
        st.subheader("🔍 需求分析关键词云")
        keywords = [analysis['keyword'] for analysis in analyses]
        keyword_counts = {}
        for kw in keywords:
            keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
        
        if keyword_counts:
            fig = go.Figure(data=[go.Bar(
                x=list(keyword_counts.keys()),
                y=list(keyword_counts.values()),
                marker_color='#4ECDC4'
            )])
            fig.update_layout(
                title="需求分析关键词频率",
                xaxis_title="关键词",
                yaxis_title="分析次数"
            )
            st.plotly_chart(fig, use_container_width=True)


# --- 模块五：【AI团队协作中心】---
elif selected_function == t['nav_ai']:
    st.header(t['ai_collab_header'])
    st.write(t['ai_collab_desc'])
    
    st.markdown(f"### {t['project_overview']}")
    
    # 智能默认值：从需求洞察报告自动同步
    default_project_name_global = "智能定制化护肤产品上市项目" if st.session_state.language == '简体中文' else "Smart Customized Skincare Product Launch"
    default_product_concept_global = "一款针对敏感肌的 AI 定制化护肤产品，主打成分温和且效果精准" if st.session_state.language == '简体中文' else "An AI-powered customized skincare product for sensitive skin, featuring gentle and precise ingredients"
    
    if st.session_state.language == '简体中文':
        default_target_users_global = """客户1-职业女性（35-50岁）：高收入群体（企业高管、律师、医生），痛点包括皮肤老化、敏感肌肤、效果不持久、安全性担忧、抗衰成本高。

客户2-退休女性（45-60岁）：退休/半退休状态，痛点包括皮肤松弛深层皱纹、对化学成分谨慎、抗衰需求强烈但费用顾虑、信息获取有限、对效果有高期待。

客户3-社交媒体影响者（30-45岁）：电商主、内容创作者，痛点包括需保持年轻形象、快速见效产品难持久、对化学成分担忧、工作压力大缺少时间、对价格较敏感。"""
    else:
        default_target_users_global = """Persona 1 - Professional Women (35-50 years old): High-income groups (executives, lawyers, doctors). Pain points include skin aging, sensitive skin, non-lasting effects, safety concerns, high anti-aging costs.

Persona 2 - Retired Women (45-60 years old): Retired/semi-retired. Pain points include skin sagging and deep wrinkles, cautious about chemical ingredients, strong anti-aging needs but budget concerns, limited information access, high expectations for results.

Persona 3 - Social Media Influencers (30-45 years old): E-commerce hosts, content creators. Pain points include need to maintain youthful appearance, fast-acting products lack durability, concerns about chemical ingredients, high work pressure with limited time, price-sensitive."""
    
    # 如果有需求洞察报告，自动同步到项目总览
    if 'radar_keyword' in st.session_state and st.session_state.get('radar_keyword'):
        radar_keyword = st.session_state['radar_keyword']
        default_project_name_global = f"{radar_keyword}创新产品项目"
        default_product_concept_global = f"针对【{radar_keyword}】需求的创新解决方案（基于需求雷达洞察）"
    
    # 如果有用户画像报告，自动同步到项目总览
    if 'persona_user_text' in st.session_state and st.session_state.get('persona_user_text'):
        persona_text = st.session_state['persona_user_text']
        if len(persona_text) > 50:
            default_target_users_global = f"基于用户画像建模的目标用户：\n{persona_text[:500]}"
            if len(persona_text) > 500:
                default_target_users_global += "..."
    
    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input(t['current_project'], default_project_name_global)
        product_concept_global = st.text_area(t['product_concept'], 
                                             default_product_concept_global, height=100)
    with col2:
        target_users_global = st.text_area(t['target_users'], 
                                          default_target_users_global, height=200)
    
    st.markdown("---")
    
    manager_tool = st.radio(
        t['choose_manager'],
        (t['pm_agent'], t['marketing_agent'], t['medical_agent'], t['social_agent'], t['design_agent']),
        key="manager_tool_radio"
    )
    st.markdown("---")
    
    if manager_tool == t['pm_agent']:
        st.subheader(t['pm_title'])
        st.write(t['pm_desc'])
        
        # 检测需求洞察报告
        has_insight_reports = 'radar_report' in st.session_state or 'persona_report' in st.session_state
        if has_insight_reports:
            insight_info = []
            if 'radar_report' in st.session_state:
                insight_keyword_label = "「需求雷达」关键词:" if st.session_state.language == '简体中文' else "「Demand Radar」Keyword:"
                insight_info.append(f"{insight_keyword_label} {st.session_state.get('radar_keyword', '')}")
            if 'persona_report' in st.session_state:
                persona_label = "「用户画像建模」报告" if st.session_state.language == '简体中文' else "「User Persona」Report"
                insight_info.append(persona_label)
            
            detected_msg = "💡 已检测到需求洞察报告！" if st.session_state.language == '简体中文' else "💡 Demand insight reports detected!"
            st.info(f"{detected_msg} {' / '.join(insight_info)}")
            if st.button(t['use_insight'], key="use_insight_reports"):
                st.session_state['auto_fill_pm_from_insight'] = True
                st.rerun()
        
        # 自动填充逻辑
        if st.session_state.get('auto_fill_pm_from_insight', False):
            # 从需求雷达提取项目名称和产品概念
            if 'radar_report' in st.session_state:
                radar_keyword = st.session_state.get('radar_keyword', '')
                # 填充项目名称
                st.session_state['pm_filled_project_name'] = f"{radar_keyword}创新产品项目"
                # 填充产品概念
                st.session_state['pm_filled_product_concept'] = f"针对【{radar_keyword}】需求的创新解决方案（基于需求雷达洞察）"
            
            # 从用户画像提取目标用户
            if 'persona_report' in st.session_state:
                persona_text = st.session_state.get('persona_user_text', '')
                if persona_text and len(persona_text) > 50:
                    filled_users = f"基于用户画像建模的目标用户：\n{persona_text[:300]}"
                    if len(persona_text) > 300:
                        filled_users += "..."
                    st.session_state['pm_filled_target_users'] = filled_users
            
            st.session_state['auto_fill_pm_from_insight'] = False
        
        # 确定默认值：优先使用已填充的值，否则使用全局值
        default_project_name = st.session_state.get('pm_filled_project_name', project_name)
        default_product_concept = st.session_state.get('pm_filled_product_concept', product_concept_global)
        default_target_users = st.session_state.get('pm_filled_target_users', target_users_global)
        
        project_name_pm = st.text_input(
            t['project_name_label'], 
            value=default_project_name
        )
        product_concept_pm = st.text_area(
            t['product_concept_label'], 
            value=default_product_concept, 
            height=100
        )
        target_users_pm = st.text_area(
            t['target_users_label'], 
            value=default_target_users, 
            height=150
        )
        output_language_pm = st.radio(t['output_language'], ("简体中文", "繁体中文", "English"), index=0, key="pm_lang")

        if st.button(t['generate_report'], key="run_pm_agent"):
            if project_name_pm and product_concept_pm and target_users_pm:
                with st.status(t['pm_analyzing'], expanded=True) as status:
                    st.write(t['pm_working'])
                    time.sleep(2)
                    try:
                        pm_prompt = f"""
                        你现在是一名资深 AI 产品经理 Agent，专注于 医美与健康科技领域。你的任务是基于用户提供的初步产品概念，运用 语义相似度评分（SSR）调研框架 输出一份结构化的市场与用户洞察报告。请以 逻辑清晰、数据驱动、专业严谨 的商业分析口吻撰写内容。

                        ---

                        ### 输出目标
                        针对用户提供的医美产品／服务概念，综合用户调研、竞品分析与功能规划，完成一份完整的产品策略报告。
                        输出语言：{output_language_pm}
                        篇幅建议：800～1200 字
                        语气风格：专业、分析性、避免营销腔。

                        ---

                        ### 执行步骤

                        1. 角色与背景设定
                        - 你是一名资深 AI 产品经理，擅长将医美领域的用户需求转化为具有商业潜力的产品方案。
                        - 使用 SSR 框架，可模拟不同虚拟用户角色的反馈，量化他们对产品概念的兴趣与购买意愿。

                        2. 输入信息
                        - 医美产品／服务概念：{product_concept_pm}
                        - 目标用户画像：{target_users_pm}

                        3. 分析任务
                        请按以下结构输出内容：
                        (1) 用户洞察与 SSR 模拟分析
                        - 扮演所设虚拟用户角色，基于用户画像进行需求与痛点推演。
                        - 为每个角色估算其对产品概念的 SSR（语义相似度评分），描述兴趣强度与购买动机逻辑。
                        (2) 市场趋势与竞品格局
                        - 概述当前同类医美／健康科技产品的解决方案。
                        - 对比功能定位、定价、目标人群、市场声量等维度。
                        - 指出潜在"蓝海"细分市场或竞争挑战。
                        (3) 产品功能规划与价值主张
                        - 提出 3–5 个核心功能建议，并说明与目标用户需求的对应关系。
                        - 提炼 1 个明确的差异化价值主张，解释其"爆款基因"（如技术壁垒、用户情绪共鸣、场景粘性等）。
                        (4) 建议的产品方向总结
                        - 提出后续验证步骤或 MVP 实验思路（如可行性调研、功能优先级排序）。

                        4. 输出格式要求（示例）
                        # 医美产品概念市场与用户洞察报告
                        ## 一、用户画像与 SSR 分析
                        （每个虚拟用户 1 段描述，附 SSR 评分与痛点摘要）
                        ## 二、行业趋势与竞品分析
                        （竞品表格可含：品牌、功能定位、主要卖点、目标人群、市场评价）
                        ## 三、功能建议与价值主张
                        （3–5 条功能要点 + 1 条差异化主张说明）
                        ## 四、结论与建议
                        （总结产品策略方向与后续验证计划）
                        ---
                        请在接收到用户输入的产品概念与目标用户画像后，依照上述结构输出一份完整报告。
                        """
                        pm_report = call_gemini(
                            system_prompt=pm_prompt,
                            user_prompt="请生成产品策略报告。",
                            model="gemini-2.5-flash"
                        )
                        
                        # 保存产品经理报告到session_state
                        st.session_state['pm_report'] = pm_report
                        st.session_state['pm_project_name'] = project_name_pm
                        st.session_state['pm_product_concept'] = product_concept_pm
                        st.session_state['pm_target_users'] = target_users_pm
                        
                        status.update(label="报告生成完成！", state="complete", expanded=False)
                        st.success("✅ 产品经理报告已生成！其他AI经理现在可以使用此报告了。")
                        st.subheader("✅ 产品经理报告：")
                        st.markdown(pm_report)
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.download_button(
                                label="📥 导出为Markdown",
                                data=f"# 产品经理报告\n\n**项目**: {project_name_pm}\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{pm_report}",
                                file_name=f"产品经理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown"
                            ):
                                st.success("文件已准备下载！")
                        with col2:
                            pdf_data = generate_pdf_report(
                                title="产品经理报告",
                                content=pm_report,
                                metadata={"项目": project_name_pm, "生成时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            )
                            if st.download_button(
                                label="📄 导出为PDF",
                                data=pdf_data,
                                file_name=f"产品经理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                key="pm_pdf_download"
                            ):
                                st.success("PDF已准备下载！")
                            
                    except Exception as e:
                        status.update(label="报告生成失败！", state="error", expanded=True)
                        st.error(f"生成报告失败: {e}")
            else:
                st.warning("请输入项目名称、产品概念和目标用户画像。")
        
        # 持久显示已生成的产品经理报告（在按钮回调之外）
        if 'pm_report' in st.session_state and manager_tool == "「产品经理Agent」":
            st.markdown("---")
            st.subheader("✅ 产品经理报告：")
            st.markdown(st.session_state['pm_report'])
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.download_button(
                    label="📥 导出为Markdown",
                    data=f"# 产品经理报告\n\n**项目**: {st.session_state.get('pm_project_name', '')}\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{st.session_state['pm_report']}",
                    file_name=f"产品经理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="pm_md_download_persistent"
                ):
                    st.success("文件已准备下载！")
            with col2:
                pdf_data = generate_pdf_report(
                    title="产品经理报告",
                    content=st.session_state['pm_report'],
                    metadata={"项目": st.session_state.get('pm_project_name', ''), "生成时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                )
                if st.download_button(
                    label="📄 导出为PDF",
                    data=pdf_data,
                    file_name=f"产品经理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key="pm_pdf_download_persistent"
                ):
                    st.success("PDF已准备下载！")

    elif manager_tool == "「市场经理Agent」":
        st.subheader("📊 「市场经理Agent」")
        st.write("为您制定全面的市场营销策略和品牌传播计划。")
        
        # 检测上游报告状态
        has_radar_report = 'radar_report' in st.session_state
        has_pm_report = 'pm_report' in st.session_state
        
        if has_radar_report or has_pm_report:
            report_info = []
            if has_radar_report:
                report_info.append("「需求洞察」报告")
            if has_pm_report:
                report_info.append("「产品经理」报告")
            
            st.info(f"💡 已检测到 {' 和 '.join(report_info)}！您可以直接使用这些分析结果。")
            if st.button("📥 使用需求洞察和产品经理的报告信息", key="use_reports_mm"):
                st.session_state['auto_fill_mm'] = True
                st.rerun()
        
        # 自动填充逻辑
        if st.session_state.get('auto_fill_mm', False):
            # 从产品经理报告填充产品名称和目标用户
            if has_pm_report:
                st.session_state['mm_filled_product_name'] = st.session_state.get('pm_project_name', project_name)
                st.session_state['mm_filled_target_users'] = st.session_state.get('pm_target_users', target_users_global)
            
            # 从需求洞察报告提取核心需求
            filled_core_demand = "高效抗衰、安全温和、长期调理"
            if has_radar_report:
                # 提取关键词作为核心需求的一部分
                radar_keyword = st.session_state.get('radar_keyword', '')
                if radar_keyword:
                    filled_core_demand = f"{radar_keyword}相关的核心痛点和真实需求"
            
            st.session_state['mm_filled_core_demand'] = filled_core_demand
            st.session_state['auto_fill_mm'] = False  # 重置标记
        
        # 确定默认值：智能自动填充
        # 优先级：已手动填充的值 > 产品经理报告的值 > 全局默认值
        if 'mm_filled_product_name' not in st.session_state and has_pm_report:
            # 首次访问且有产品经理报告，自动使用产品经理的项目名称
            default_product_name = st.session_state.get('pm_project_name', project_name)
        else:
            default_product_name = st.session_state.get('mm_filled_product_name', project_name)
        
        if 'mm_filled_target_users' not in st.session_state and has_pm_report:
            # 首次访问且有产品经理报告，自动使用产品经理的目标用户
            default_target_users = st.session_state.get('pm_target_users', target_users_global)
        else:
            default_target_users = st.session_state.get('mm_filled_target_users', target_users_global)
        
        if 'mm_filled_core_demand' not in st.session_state and has_radar_report:
            # 首次访问且有需求洞察报告，自动提取核心需求
            radar_keyword = st.session_state.get('radar_keyword', '')
            if radar_keyword:
                default_core_demand = f"{radar_keyword}相关的核心痛点和真实需求"
            else:
                default_core_demand = "高效抗衰、安全温和、长期调理"
        else:
            default_core_demand = st.session_state.get('mm_filled_core_demand', "高效抗衰、安全温和、长期调理")

        product_name_mm = st.text_input("【医美新产品名称】：", value=default_product_name)
        target_users_mm = st.text_area("【目标用户画像】：", value=default_target_users, height=100)
        core_demand_mm = st.text_input("用户最关注的【核心需求】：", value=default_core_demand)
        marketing_goal_mm = st.text_area("设定明确的【营销目标】：", 
                                        "在上市首季实现10%的市场份额增长，品牌认知度提升20点", height=80)
        output_language_mm = st.radio("输出语言：", ("简体中文", "繁体中文", "English"), index=0, key="mm_lang")

        if st.button("制定上市营销策略", key="run_mm_agent"):
            if product_name_mm and target_users_mm and core_demand_mm and marketing_goal_mm:
                with st.status("市场经理Agent正在分析并生成策略...", expanded=True) as status:
                    st.write("正在分析市场竞争格局，制定营销策略方向...")
                    time.sleep(2)
                    try:
                        # 构建上下文信息
                        context_info = ""
                        if has_radar_report:
                            radar_summary = st.session_state.get('radar_report', '')[:600]
                            context_info += f"\n\n【需求洞察引擎的市场分析摘要】：\n{radar_summary}...\n"
                        
                        if has_pm_report:
                            pm_summary = st.session_state.get('pm_report', '')[:500]
                            context_info += f"\n【产品经理的战略分析摘要】：\n{pm_summary}...\n"
                        
                        mm_prompt = f"""
                        你现在是一名资深、全面的AI市场经理，专注于医美、皮肤科学和生物技术领域。你具备卓越的市场洞察力、战略规划能力和执行推进能力。你能够整合多维度数据（包括AI产品经理的用户洞察、AI医学经理的科学依据），制定并优化全面的市场营销策略和品牌传播计划。你擅长识别市场机会，评估营销效果，并能提供清晰、可执行的建议，驱动业务增长，实现"数据支撑下的理性决策"。

                        核心能力：
                        市场调研与分析： 深度分析行业趋势、市场规模、增长潜力，识别市场空白和竞争格局。利用各种数据（包括外部数据源和内部AI Agent提供的数据）洞察消费者行为、需求和痛点。
                        营销策略制定： 基于市场分析和产品定位，制定清晰的营销目标、定位策略、传播策略和阶段性营销计划，确保与品牌整体战略一致。
                        竞品分析与差异化： 系统性地研究主要竞争对手的产品、定价、营销手段和市场表现，提出有效的差异化竞争策略。
                        营销活动策划与执行支持： 构思并规划线上线下营销活动、公关事件，包括活动主题、内容形式、预算分配和效果评估指标。能够协助或指导其他Agent产出相关物料。
                        渠道选择与优化： 评估和选择最适合目标市场的营销渠道（如社交媒体、电商平台、线下医美机构合作、KOL/KOC矩阵），并持续监控和优化渠道表现，提升ROI。
                        品牌传播与管理： 协助建立和维护品牌形象，规划品牌故事和传播路径，提升品牌知名度、美誉度和忠诚度。

                        工作模式： 接收来自"总指挥"（用户）的产品信息、目标用户、业务目标或特定的市场挑战。输出结构化的市场分析报告、完整的营销策略提案、具体的活动策划方案、竞品分析报告或品牌传播计划。能够紧密协调和指导其他AI Agent（产品、医学、新媒体、设计）的输出，确保营销活动高效、协同推进。

                        你现在是一名专业的AI市场经理，请为我们的{product_name_mm}制定一份全面的上市营销策略。
                        AI产品经理的最新调研显示，该产品的核心用户是{target_users_mm}，用户最关注{core_demand_mm}。
                        目标是{marketing_goal_mm}。
                        {context_info}
                        
                        基于以上需求洞察和产品经理的分析，

                        请你：
                        1. 深度分析当前高端抗衰市场的竞争格局（指出3-5个主要竞品及其营销特点），并明确我们的差异化竞争优势。
                        2. 制定3-5个核心的营销策略方向（例如：高端KOL/KOC深度合作、医美机构赋能、精准社群营销、线下尊享沙龙），并说明每个策略的预期效果和与目标用户的契合点。
                        3. 针对每个策略方向，提出1-2个具体的活动策划建议或创意点，并初步评估所需的资源和效果指标。
                        4. 建议如何在品牌层面进行传播，以提升产品的高端形象和专业度。
                        请以一份结构清晰、有策略高度、数据驱动、兼具创新与落地性的市场策略报告形式输出，使用{output_language_mm}。
                        """
                        mm_report = call_gemini(
                            system_prompt=mm_prompt,
                            user_prompt=f"请为产品 {product_name_mm} 制定上市营销策略。",
                            model="gemini-2.5-flash"
                        )
                        st.session_state['mm_report'] = mm_report
                        st.session_state['mm_product_name'] = product_name_mm
                        st.session_state['mm_core_demand'] = core_demand_mm
                        st.session_state['mm_target_users'] = target_users_mm
                        status.update(label="策略生成完成！", state="complete", expanded=False)
                        st.subheader("✅ 市场经理报告：")
                        st.markdown(mm_report)
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.download_button(
                                label="📥 导出为Markdown",
                                data=f"# 市场经理报告\n\n**产品**: {product_name_mm}\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{mm_report}",
                                file_name=f"市场经理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                                mime="text/markdown"
                            ):
                                st.success("文件已准备下载！")
                        with col2:
                            pdf_data = generate_pdf_report(
                                title="市场经理报告",
                                content=mm_report,
                                metadata={"产品": product_name_mm, "生成时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                            )
                            if st.download_button(
                                label="📄 导出为PDF",
                                data=pdf_data,
                                file_name=f"市场经理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf",
                                key="mm_pdf_download"
                            ):
                                st.success("PDF已准备下载！")
                            
                    except Exception as e:
                        status.update(label="策略生成失败！", state="error", expanded=True)
                        st.error(f"生成策略失败: {e}")
            else:
                st.warning("请填写所有必填信息。")
        
        # 执行文档包生成功能（独立于按钮之外，持久显示）
        if 'mm_report' in st.session_state:
            st.markdown("---")
            with st.expander("📋 生成执行文档包（基于营销策略报告）"):
                st.write("选择您需要生成的执行文档：")
                doc_options = st.multiselect(
                    "选择文档类型：",
                    ["医师SOP与培训课件目录", "KOL分层与人选清单", "白皮书大纲与指标体系", "线下沙龙标准化执行手册"],
                    default=["医师SOP与培训课件目录"]
                )
                
                if st.button("生成选中的执行文档", key="generate_exec_docs"):
                    if doc_options:
                        with st.status("正在生成执行文档...", expanded=True) as doc_status:
                            st.write(f"正在生成 {len(doc_options)} 份执行文档...")
                            time.sleep(2)
                            try:
                                doc_prompt = f"""
                                你是一名资深、全面的AI市场经理，专注于医美、皮肤科学和生物技术领域。
                                
                                基于以下营销策略报告，为产品"{st.session_state.get('mm_product_name', '')}"生成具体的执行文档。
                                
                                营销策略报告摘要：
                                {st.session_state.get('mm_report', '')[:1000]}...
                                
                                请为以下文档类型生成详细、可执行的内容：
                                {', '.join(doc_options)}
                                
                                针对每个文档类型，请输出：
                                
                                {"1. **医师SOP与培训课件目录**：包括培训课程结构、每个模块的学习目标、课时安排、教学方法、评估标准、操作规范要点、并发症处置流程等。" if "医师SOP与培训课件目录" in doc_options else ""}
                                
                                {"2. **KOL分层与人选清单**：按照平台（小红书/抖音/微博/B站/Instagram等）、影响力层级（头部/腰部/尾部KOL、KOC）、粉丝数量、垂直领域、合作报价区间、预估ROI、合作形式建议等维度，提供20-30位具体的KOL/KOC人选清单（可以是虚拟但真实可信的人设）。" if "KOL分层与人选清单" in doc_options else ""}
                                
                                {"3. **白皮书大纲与指标体系**：包括白皮书章节结构、每章核心内容要点、数据采集指标（皮肤检测指标、用户满意度评分、不良事件监测）、研究方法、样本量设计、时间节点、伦理审查要点、发布与传播策略等。" if "白皮书大纲与指标体系" in doc_options else ""}
                                
                                {"4. **线下沙龙标准化执行手册**：包括活动流程时间表、场地布置方案、物料清单（展板、手册、体验装、礼品等）、人员配置（主持人、医生讲师、咨询顾问、接待人员）、预算明细模板、效果评估指标、应急预案等。" if "线下沙龙标准化执行手册" in doc_options else ""}
                                
                                请以清晰的Markdown格式输出，每个文档用二级标题分隔，内容详实、可直接用于执行。
                                """
                                
                                exec_docs = call_gemini(
                                    system_prompt=doc_prompt,
                                    user_prompt=f"请生成以下执行文档：{', '.join(doc_options)}",
                                    model="gemini-2.5-flash"
                                )
                                st.session_state['exec_docs'] = exec_docs
                                st.session_state['exec_doc_types'] = doc_options
                                doc_status.update(label="执行文档生成完成！", state="complete", expanded=False)
                                    
                            except Exception as e:
                                doc_status.update(label="文档生成失败！", state="error", expanded=True)
                                st.error(f"生成执行文档失败: {e}")
                    else:
                        st.warning("请至少选择一种文档类型。")
        
        # 显示生成的执行文档（持久显示）
        if 'exec_docs' in st.session_state:
            st.markdown("---")
            st.subheader("✅ 执行文档包：")
            st.markdown(st.session_state['exec_docs'])
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.download_button(
                    label="📥 导出执行文档为Markdown",
                    data=f"# 执行文档包\n\n**产品**: {st.session_state.get('mm_product_name', '')}\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n**文档类型**: {', '.join(st.session_state.get('exec_doc_types', []))}\n\n{st.session_state['exec_docs']}",
                    file_name=f"执行文档包_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="download_exec_docs"
                ):
                    st.success("执行文档已准备下载！")
            with col2:
                pdf_data = generate_pdf_report(
                    title="执行文档包",
                    content=st.session_state['exec_docs'],
                    metadata={
                        "产品": st.session_state.get('mm_product_name', ''),
                        "生成时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "文档类型": ', '.join(st.session_state.get('exec_doc_types', []))
                    }
                )
                if st.download_button(
                    label="📄 导出为PDF",
                    data=pdf_data,
                    file_name=f"执行文档包_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key="exec_docs_pdf_download"
                ):
                    st.success("PDF已准备下载！")

    elif manager_tool == "「医学经理Agent」":
        st.subheader("🔬 「医学经理Agent」")
        st.write("为您提供产品医学故事构建、科学依据和合规性审核。")
        
        # 检测上游报告状态
        has_pm_report = 'pm_report' in st.session_state
        has_mm_report = 'mm_report' in st.session_state
        
        if has_pm_report or has_mm_report:
            report_info = []
            if has_pm_report:
                report_info.append("「产品经理」报告")
            if has_mm_report:
                report_info.append("「市场经理」报告")
            
            st.info(f"💡 已检测到 {' 和 '.join(report_info)}！您可以直接使用这些分析结果作为医学审核的基础。")
            if st.button("📥 使用产品经理和市场经理的报告信息", key="use_reports_med"):
                st.session_state['auto_fill_med'] = True
                st.rerun()
        
        # 自动填充逻辑
        if st.session_state.get('auto_fill_med', False):
            # 从产品经理和市场经理报告中提取信息
            filled_product = "新型肽链技术抗衰精华"
            filled_description = "这是一款能够深入肌底，激活胶原再生，显著改善细纹和松弛的抗衰精华。"
            
            if has_pm_report:
                # 使用产品经理的产品概念
                pm_concept = st.session_state.get('pm_product_concept', '')
                if pm_concept:
                    filled_product = pm_concept
            
            if has_mm_report:
                # 如果有市场经理的报告，提取核心需求作为描述的一部分
                mm_core_demand = st.session_state.get('mm_core_demand', '')
                if mm_core_demand:
                    filled_description = f"基于市场需求（{mm_core_demand}）的医美产品，需要医学验证和合规审核。"
            
            st.session_state['med_filled_product'] = filled_product
            st.session_state['med_filled_description'] = filled_description
            st.session_state['auto_fill_med'] = False  # 重置标记
        
        # 确定默认值：优先使用已填充的值，否则使用默认值
        default_product = st.session_state.get('med_filled_product', "新型肽链技术抗衰精华")
        default_description = st.session_state.get('med_filled_description', "这是一款能够深入肌底，激活胶原再生，显著改善细纹和松弛的抗衰精华。")

        product_ingredient_med = st.text_input("【医美产品/成分】（例如：新型肽链技术抗衰精华）：", default_product)
        product_description_med = st.text_area("初步的【产品描述/功效宣称草稿】（可选）：", 
                                              default_description, height=100)
        output_language_med = st.radio("输出语言：", ("简体中文", "繁体中文", "English"), index=0, key="med_lang")

        if st.button("生成医学策略报告", key="run_med_agent"):
            if product_ingredient_med:
                with st.status("医学经理Agent正在分析并生成报告...", expanded=True) as status:
                    st.write("正在检索最新医学研究，构建科学故事...")
                    time.sleep(2)
                    try:
                        # 构建上下文信息
                        context_info = ""
                        if has_pm_report:
                            pm_summary = st.session_state.get('pm_report', '')[:500]
                            context_info += f"\n\n【产品经理的分析摘要】：\n{pm_summary}...\n"
                        
                        if has_mm_report:
                            mm_summary = st.session_state.get('mm_report', '')[:500]
                            context_info += f"\n【市场经理的策略摘要】：\n{mm_summary}...\n"
                        
                        med_prompt = f"""
                        你是一名资深、全面的AI医学经理，专注于医美、皮肤科学和生物技术领域。你不仅具备深厚的医学知识和法规合规意识，更擅长将复杂的医学原理转化为易懂的产品价值，构建科学严谨的产品故事，并支持内部团队的医学知识赋能。你的风格严谨而不失策略性，总能为产品和营销提供强大的科学依据和专业指导。核心能力：
                        • 医学知识库管理与洞察： 快速检索、分析和整合全球最新的医学研究、临床数据、成分原理，为产品研发和市场策略提供前瞻性洞察。
                        • 产品医学故事构建： 基于医学原理和科学证据，为产品提炼核心医学卖点，构建有说服力、可信赖的产品故事，并参与产品说明书和专业资料的撰写。
                        • 内容合规与风险管理： 严谨校验产品成分、功效宣称、治疗方案的医学准确性和法规合规性（包括国家卫健委、药监局等相关医美法规），识别并提示潜在的医疗风险、副作用和禁忌症。
                        • 医学培训与赋能支持： 为内部团队（如销售、市场、新媒体）提供医学知识培训支持，解答专业疑问，确保团队对产品医学原理有深度理解。
                        • 专家资源支持（虚拟）： 模拟外部专家视角，对产品或营销方案进行初步的医学评估和反馈，提出优化建议。
                        工作模式：
                        接收来自"总指挥"（用户）的产品概念、研发方向、营销文案或内部培训需求。输出结构化的医学洞察报告、产品医学故事大纲、内容审核意见、风险评估报告或培训素材草稿。能够与其他AI Agent（产品、市场、新媒体）紧密协作，确保所有输出的医学专业性和策略性。

                        你现在是一名专业的AI医学经理，请充分发挥你在医美领域的广义专业职责。
                        我们正在研发一款{product_ingredient_med}。
                        {context_info}
                        
                        基于以上产品经理和市场经理的分析，请你：
                        1. 从医学角度，分析该{product_ingredient_med}在抗衰领域的最新研究进展和作用机制，提供3-5个核心的科学依据点。
                        2. 基于这些医学依据，为这款产品构思一个具有科学说服力且易于传播的"产品医学故事"大纲，强调其独特价值。
                        3. 针对市场经理提出的营销策略，预判这款产品在未来市场宣称和用户教育中可能遇到的医学挑战或误区，并提出初步的应对策略。
                        4. 同时，请对初步的产品描述（{product_description_med}）进行合规性初审，指出潜在的风险点，并提供优化建议，确保符合医美行业法规。
                        5. 为产品经理的产品概念和市场经理的营销方向提供医学层面的支持和建议，确保产品定位和宣传的科学性与合规性。
                        请以一份结构化、兼具深度和实用性的医学策略报告形式输出，使用{output_language_med}。
                        """
                        med_report = call_gemini(
                            system_prompt=med_prompt,
                            user_prompt=f"请为 {product_ingredient_med} 生成医学策略报告。",
                            model="gemini-2.5-flash"
                        )
                        st.session_state['med_report'] = med_report
                        st.session_state['med_product'] = product_ingredient_med
                        status.update(label="报告生成完成！", state="complete", expanded=False)
                            
                    except Exception as e:
                        status.update(label="报告生成失败！", state="error", expanded=True)
                        st.error(f"生成报告失败: {e}")
            else:
                st.warning("请输入医美产品/成分信息。")
        
        # 显示生成的报告（持久显示）
        if 'med_report' in st.session_state:
            st.markdown("---")
            st.subheader("✅ 医学经理报告：")
            st.markdown(st.session_state['med_report'])
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.download_button(
                    label="📥 导出为Markdown",
                    data=f"# 医学经理报告\n\n**产品**: {st.session_state.get('med_product', '')}\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{st.session_state['med_report']}",
                    file_name=f"医学经理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="med_md_download_persistent"
                ):
                    st.success("文件已准备下载！")
            with col2:
                pdf_data = generate_pdf_report(
                    title="医学经理报告",
                    content=st.session_state['med_report'],
                    metadata={"产品": st.session_state.get('med_product', ''), "生成时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                )
                if st.download_button(
                    label="📄 导出为PDF",
                    data=pdf_data,
                    file_name=f"医学经理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key="med_pdf_download_persistent"
                ):
                    st.success("PDF已准备下载！")

    elif manager_tool == "「新媒体经理Agent」":
        st.subheader("📱 「新媒体经理Agent」")
        st.write("为您制定引爆社交媒体的内容策略。")
        
        # 新增功能选择
        sm_function = st.radio(
            "选择新媒体功能：",
            ("基础内容策略", "内容创意矩阵生成器（九宫格方法论）"),
            key="sm_function_select"
        )
        st.markdown("---")
        
        # 检测上游报告状态
        has_radar_report = 'radar_report' in st.session_state
        has_pm_report = 'pm_report' in st.session_state
        has_mm_report = 'mm_report' in st.session_state
        has_med_report = 'med_report' in st.session_state
        
        if has_pm_report or has_mm_report or has_med_report:
            report_info = []
            if has_pm_report:
                report_info.append("「产品经理」")
            if has_mm_report:
                report_info.append("「市场经理」")
            if has_med_report:
                report_info.append("「医学经理」")
            
            st.info(f"💡 已检测到 {' 和 '.join(report_info)} 报告！您可以直接使用这些分析结果。")
            if st.button("📥 使用上游报告的信息", key="use_reports_sm"):
                st.session_state['auto_fill_sm'] = True
                st.rerun()
        
        # 自动填充逻辑
        if st.session_state.get('auto_fill_sm', False):
            # 从产品经理报告填充基础信息
            if has_pm_report:
                st.session_state['sm_filled_product_name'] = st.session_state.get('pm_project_name', project_name)
                st.session_state['sm_filled_target_users'] = st.session_state.get('pm_target_users', target_users_global)
                st.session_state['sm_filled_core_info'] = st.session_state.get('pm_product_concept', "核心成分：新型肽链；功效：激活胶原、改善细纹、温和抗衰。")
            
            # 从市场经理报告补充营销目标
            if has_mm_report:
                st.session_state['sm_filled_marketing_goal'] = "基于市场经理策略：未上市，先种草，积累早期用户关注度"
            
            # 从医学经理报告获取审核后的产品信息
            if has_med_report:
                med_product = st.session_state.get('med_product', '')
                if med_product:
                    st.session_state['sm_filled_core_info'] = f"【医学经理已审核】{med_product}"
            
            st.session_state['auto_fill_sm'] = False  # 重置标记
        
        # 智能默认值：自动检测并使用上游报告
        if 'sm_filled_product_name' not in st.session_state and has_pm_report:
            default_product_name = st.session_state.get('pm_project_name', project_name)
        else:
            default_product_name = st.session_state.get('sm_filled_product_name', project_name)
        
        if 'sm_filled_target_users' not in st.session_state and has_pm_report:
            default_target_users = st.session_state.get('pm_target_users', target_users_global)
        else:
            default_target_users = st.session_state.get('sm_filled_target_users', target_users_global)
        
        if 'sm_filled_core_info' not in st.session_state:
            if has_med_report:
                med_product = st.session_state.get('med_product', '')
                default_core_info = f"【医学经理已审核】{med_product}" if med_product else "核心成分：新型肽链；功效：激活胶原、改善细纹、温和抗衰。"
            elif has_pm_report:
                default_core_info = st.session_state.get('pm_product_concept', "核心成分：新型肽链；功效：激活胶原、改善细纹、温和抗衰。")
            else:
                default_core_info = "核心成分：新型肽链；功效：激活胶原、改善细纹、温和抗衰。"
        else:
            default_core_info = st.session_state.get('sm_filled_core_info', "核心成分：新型肽链；功效：激活胶原、改善细纹、温和抗衰。")
        
        if 'sm_filled_marketing_goal' not in st.session_state and has_mm_report:
            default_marketing_goal = "基于市场经理策略：未上市，先种草，积累早期用户关注度"
        else:
            default_marketing_goal = st.session_state.get('sm_filled_marketing_goal', "未上市，先种草，积累早期用户关注度")

        if sm_function == "基础内容策略":
            product_name_sm = st.text_input("【医美新产品名称】：", value=default_product_name)
            target_users_sm = st.text_area("【目标用户画像】：", value=default_target_users, height=100)
            marketing_goal_sm = st.text_area("【上市前期营销目标】（如：未上市，先种草）：", 
                                            default_marketing_goal, height=80)
            core_info_sm = st.text_area("【产品核心成分和功效信息】（AI医学经理已审核）：", 
                                       default_core_info, height=100)
            social_platforms_sm = st.multiselect("选择【重点社交媒体平台】（可多选）：", 
                                                ["小红书", "Instagram", "抖音", "微博", "B站", "知乎", "微信公众号"],
                                                ["小红书", "Instagram"])
            output_language_sm = st.radio("输出语言：", ("简体中文", "繁体中文", "English"), index=0, key="basic_lang")

            if st.button("生成新媒体内容策略", key="run_sm_agent"):
                if product_name_sm and target_users_sm and marketing_goal_sm and core_info_sm and social_platforms_sm:
                    with st.status("新媒体经理Agent正在构思内容策略...", expanded=True) as status:
                        st.write("正在分析平台特性，生成爆款创意...")
                        time.sleep(2)
                        try:
                            sm_prompt = f"""
                            你是一名资深、全面的AI新媒体经理，专注于医美、皮肤科学和生物技术领域。你精通主流社交媒体平台（如小红书、抖音、微博、Facebook、Instagram、Line等）的传播规律和用户偏好，并具备卓越的内容策略规划、创意产出、社群运营及数据分析能力。你擅长将复杂的医美知识转化为吸引人的内容形式，能够快速捕捉热点、制造爆款，并通过精细化运营提升用户参与度和转化率，实现"未上市，先种草"或持续品牌声量的目标。核心能力：
                            • 新媒体策略规划： 根据产品特点、目标用户（来自AI产品经理）和市场目标（来自AI市场经理），制定适合不同平台的新媒体内容策略、发布频率和互动计划。
                            • 内容创意与产出： 不仅限于文案，还能构思短视频脚本、直播主题、图文策划等多样化内容形式。将AI医学经理审核后的专业内容，转化为生动、有趣、易于传播的语言。
                            • 社群运营与互动： 设计互动问答、话题挑战、用户活动等，提升用户参与度和粘性；管理用户评论和私信，进行初步的用户引导和反馈收集。
                            • 热点捕捉与借势营销： 实时监测社交媒体热点，结合品牌或产品特性，快速响应并创作相关内容，制造传播机会。
                            • 数据分析与效果评估： 监控新媒体平台的数据表现（如阅读量、互动量、转发量、粉丝增长、转化率等），分析内容效果，并据此优化策略和内容方向。
                            • KOL/KOC策略建议： 根据产品和市场目标，评估并推荐合适的KOL/KOC合作人选和合作模式。工作模式：
                            接收来自"总指挥"（用户）的产品信息、营销目标、目标用户画像或特定的内容主题。输出结构化的新媒体内容策略方案、具体的内容排期、多平台文案/脚本草稿、互动活动策划或效果分析报告。能够紧密协调和指导其他AI Agent（产品、医学、市场、设计）的输出，确保新媒体内容与整体营销战略协同。

                            你现在是一名专业的AI新媒体经理，请为我们的{product_name_sm}在{output_language_sm}社交媒体（重点关注{', '.join(social_platforms_sm)}）制定一份为期一个月的上市前期内容策略。
                            AI产品经理的调研显示，目标用户是{target_users_sm}。AI市场经理已制定"{marketing_goal_sm}"的初期目标。AI医学经理已审核通过产品的核心成分和功效信息：{core_info_sm}。

                            请你：
                            1. 针对{', '.join(social_platforms_sm)}这些平台，分别构思3个不同主题的内容系列（例如：成分科普系列、用户痛点解决系列、日常使用场景系列），并说明其内容形式（图文、短视频脚本、直播预热等）。
                            2. 为每个主题系列提出3-5个爆款标题建议，并附上吸引人的emoji。
                            3. 设计2-3个互动话题或社群活动，以提升用户参与度和讨论度，实现私域流量沉淀。
                            4. 建议3-5个适合该阶段的KOL/KOC合作方向。
                            请以一份结构清晰、创意丰富、兼具策略性和落地性的新媒体内容策略报告形式输出，使用{output_language_sm}。
                            """
                            sm_report = call_gemini(
                                system_prompt=sm_prompt,
                                user_prompt=f"请为 {product_name_sm} 生成新媒体内容策略。",
                                model="gemini-2.5-flash"
                            )
                            st.session_state['sm_report'] = sm_report
                            st.session_state['sm_product_name'] = product_name_sm
                            status.update(label="策略生成完成！", state="complete", expanded=False)
                                
                        except Exception as e:
                            status.update(label="策略生成失败！", state="error", expanded=True)
                            st.error(f"生成策略失败: {e}")
                else:
                    st.warning("请填写所有必填信息。")
        
        elif sm_function == "内容创意矩阵生成器（九宫格方法论）":
            st.subheader("📊 内容创意矩阵生成器")
            st.write("基于九宫格方法论，系统化生成30个Hero内容创意。")
            
            # Step 1: 背景信息智能填充
            st.markdown("### 第一步：创业者/品牌背景信息")
            
            # 智能提取背景信息
            background_info = ""
            if has_radar_report or has_pm_report or has_mm_report or has_med_report:
                st.info("💡 系统已自动从上游报告中提取背景信息。您可以直接使用或编辑。")
                
                # 从各个报告中提取关键信息构建背景
                profession = "创业者"
                if has_pm_report:
                    pm_concept = st.session_state.get('pm_product_concept', '')
                    if "医美" in pm_concept or "皮肤" in pm_concept:
                        profession = "医美行业创业者"
                
                product_service = st.session_state.get('pm_product_concept', default_product_name)
                target_audience = st.session_state.get('pm_target_users', default_target_users)[:200]
                core_value = st.session_state.get('mm_core_demand', '解决用户核心痛点')
                
                background_info = f"""我是一名{profession}，致力于医美与健康领域的创新和卓越。我的主业是提供{product_service}，旨在帮助用户在{core_value}方面创造价值。这项服务/产品适用于{target_audience}，能够帮助他们获得显著成果。
我在小红书、抖音等社交媒体平台上保持活跃，分享关于医美知识和护肤技巧的内容去触达到我的目标客户。我力求在医美专业领域提供最新趋势的洞察和行之有效的技巧，助力我的观众和客户脱颖而出。"""
            
            user_background = st.text_area(
                "请描述您的创业者/品牌背景：", 
                value=background_info if background_info else "我是一名...",
                height=200,
                help="参考模板：我是一名 [职业名称]，致力于 [目标领域]的创新和卓越。我的主业是提供 [产品/服务名称]，旨在 [主要目标]方面为个人和企业创造价值。"
            )
            
            # Step 2: 目标用户
            st.markdown("### 第二步：目标用户画像")
            
            target_audience_info = ""
            if has_pm_report or has_mm_report:
                target_users_detail = st.session_state.get('pm_target_users', default_target_users)
                target_audience_info = f"""我专注于为{target_users_detail[:150]}提供医美产品/服务。我的潜在客户可能是对医美、护肤有兴趣或需求的个人消费者。这些客户在社交媒体平台上寻找专业的医美知识和有效的护肤方案。
他们可能已经有了一定的护肤经验，或许在抗衰、美白、敏感肌护理等方面寻求改善。我提供的产品/服务旨在解决他们在护肤效果、安全性方面的问题，帮助他们在肌肤健康、外在形象方面取得进步。"""
            
            target_audience = st.text_area(
                "请描述您的目标用户：",
                value=target_audience_info if target_audience_info else "我专注于为...",
                height=180,
                help="参考模板：我专注于为（目标客户群体）提供（产品/服务类型）。我的潜在客户可能是对（领域/行业）有兴趣或需求的（用户类型）。"
            )
            
            # Step 3: 主要话题
            st.markdown("### 第三步：您的主要内容话题")
            st.info("💡 AI将基于这些话题生成九宫格内容支柱")
            
            topic1 = st.text_input("话题一：", "医美知识科普")
            topic2 = st.text_input("话题二：", "产品成分分析")
            topic3 = st.text_input("话题三：", "用户案例分享")
            
            # Step 4: 内容特殊要求
            st.markdown("### 第四步：内容创作要求")
            
            col1, col2 = st.columns(2)
            with col1:
                excluded_content = st.text_area(
                    "不包含的内容（可选）：",
                    "编程、技术代码等",
                    height=80,
                    help="列出您不希望在内容中出现的主题"
                )
            with col2:
                content_count = st.number_input(
                    "生成内容创意数量：",
                    min_value=10,
                    max_value=50,
                    value=30,
                    step=10,
                    help="建议30个（增长型、知识型、权威型各10个）"
                )
            
            output_language_matrix = st.radio("输出语言：", ("简体中文", "繁体中文", "English"), index=0, key="matrix_lang")
            
            if st.button("🚀 生成内容创意矩阵", key="run_content_matrix"):
                if user_background and target_audience and topic1:
                    with st.status("AI正在生成九宫格内容支柱和30个创意...", expanded=True) as status:
                        st.write("第1步：分析背景和目标用户...")
                        time.sleep(1.5)
                        
                        try:
                            # Step 1: 生成九宫格内容支柱
                            st.write("第2步：构建九宫格内容支柱...")
                            pillar_prompt = f"""
                            你是一位内容策略专家，精通九宫格内容支柱方法论。
                            
                            用户背景：
                            {user_background}
                            
                            目标用户：
                            {target_audience}
                            
                            主要话题：
                            1. {topic1}
                            2. {topic2}
                            3. {topic3}
                            
                            请基于以上信息，创建一个3x3的内容支柱矩阵（九宫格）。每个格子代表一个内容主题方向，这些主题应该：
                            1. 与用户背景和目标用户高度相关
                            2. 覆盖增长型内容（吸引眼球）、知识型内容（获取粉丝）、权威型内容（建立权威）三个维度
                            3. 每个主题简洁明了，适合作为社交媒体内容的核心主题
                            
                            请以清晰的Markdown表格格式输出九宫格：
                            
                            | 主题1 | 主题2 | 主题3 |
                            |------|------|------|
                            | 主题4 | 主题5 | 主题6 |
                            | 主题7 | 主题8 | 主题9 |
                            
                            然后为每个主题提供一句话说明其定位和价值。
                            
                            输出语言：{output_language_matrix}
                            """
                            
                            pillar_result = call_gemini(
                                system_prompt=pillar_prompt,
                                user_prompt="请生成九宫格内容支柱。",
                                model="gemini-2.5-flash"
                            )
                            
                            st.session_state['content_pillar'] = pillar_result
                            
                            # Step 2: 生成30个内容创意
                            st.write("第3步：生成30个Hero内容创意...")
                            time.sleep(1)
                            
                            ideas_prompt = f"""
                            你是一位专业的内容创意专家。基于以下九宫格内容支柱，为用户生成{content_count}个具体的内容创意（Content Ideas）。
                            
                            九宫格内容支柱：
                            {pillar_result}
                            
                            用户背景：
                            {user_background}
                            
                            目标用户：
                            {target_audience}
                            
                            要求：
                            1. **内容类型**：Hero content（英雄式内容，高曝光高传播）
                            2. **目标**：吸引粉丝，增加曝光
                            3. **不包含的内容**：{excluded_content}
                            4. **内容特点**：actionable（可执行）, inspirational（有启发性）, analytical（有分析深度）, informative（信息丰富）, sharable（易于分享）
                            5. **数量分配**：
                               - 增长型内容（吸引眼球）：{content_count // 3}篇
                               - 知识型内容（获取粉丝）：{content_count // 3}篇
                               - 权威型内容（建立权威）：{content_count // 3}篇
                            6. **避免重复**：确保每个创意都是独特的
                            
                            请以表格形式输出，包含以下列：
                            - 编号
                            - 内容标题/话题
                            - 类型（增长型/知识型/权威型）
                            - 一句话说明
                            
                            格式示例：
                            | 编号 | 内容标题 | 类型 | 说明 |
                            |-----|---------|------|------|
                            | 1   | 如何在30天内改善皮肤屏障 | 知识型 | 提供具体的护肤步骤和时间表 |
                            
                            输出语言：{output_language_matrix}
                            """
                            
                            ideas_result = call_gemini(
                                system_prompt=ideas_prompt,
                                user_prompt=f"请生成{content_count}个内容创意。",
                                model="gemini-2.5-flash"
                            )
                            
                            st.session_state['content_ideas'] = ideas_result
                            st.session_state['matrix_count'] = content_count
                            
                            status.update(label="内容创意矩阵生成完成！", state="complete", expanded=False)
                            st.success(f"✅ 已成功生成九宫格内容支柱和{content_count}个Hero内容创意！")
                            
                        except Exception as e:
                            status.update(label="生成失败！", state="error", expanded=True)
                            st.error(f"生成内容创意矩阵失败: {e}")
                else:
                    st.warning("请至少填写背景信息、目标用户和第一个话题。")
            
            # 显示生成的内容创意矩阵
            if 'content_pillar' in st.session_state and 'content_ideas' in st.session_state:
                st.markdown("---")
                st.subheader("✅ 九宫格内容支柱")
                st.markdown(st.session_state['content_pillar'])
                
                st.markdown("---")
                st.subheader(f"✅ {st.session_state.get('matrix_count', 30)}个Hero内容创意")
                st.markdown(st.session_state['content_ideas'])
                
                # 导出按钮
                col1, col2 = st.columns([1, 1])
                with col1:
                    combined_content = f"""# 内容创意矩阵报告

## 九宫格内容支柱

{st.session_state['content_pillar']}

## Hero内容创意

{st.session_state['content_ideas']}

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                    if st.download_button(
                        label="📥 导出完整报告（Markdown）",
                        data=combined_content,
                        file_name=f"内容创意矩阵_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown",
                        key="matrix_md_download"
                    ):
                        st.success("文件已准备下载！")
                
                with col2:
                    pdf_data = generate_pdf_report(
                        title="内容创意矩阵报告",
                        content=combined_content,
                        metadata={"生成时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    )
                    if st.download_button(
                        label="📄 导出为PDF",
                        data=pdf_data,
                        file_name=f"内容创意矩阵_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        key="matrix_pdf_download"
                    ):
                        st.success("PDF已准备下载！")
        
        # 显示生成的报告（持久显示）
        if 'sm_report' in st.session_state and sm_function == "基础内容策略":
            st.markdown("---")
            st.subheader("✅ 新媒体经理报告：")
            st.markdown(st.session_state['sm_report'])
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.download_button(
                    label="📥 导出为Markdown",
                    data=f"# 新媒体经理报告\n\n**产品**: {st.session_state.get('sm_product_name', '')}\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{st.session_state['sm_report']}",
                    file_name=f"新媒体经理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="sm_md_download_persistent"
                ):
                    st.success("文件已准备下载！")
            with col2:
                pdf_data = generate_pdf_report(
                    title="新媒体经理报告",
                    content=st.session_state['sm_report'],
                    metadata={"产品": st.session_state.get('sm_product_name', ''), "生成时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                )
                if st.download_button(
                    label="📄 导出为PDF",
                    data=pdf_data,
                    file_name=f"新媒体经理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key="sm_pdf_download_persistent"
                ):
                    st.success("PDF已准备下载！")

    elif manager_tool == "「设计经理Agent」":
        st.subheader("🎨 「设计经理Agent」")
        st.write("为您提供有品味、有策略的品牌视觉方案，降低沟通成本。")
        
        # 检测上游报告状态
        has_pm_report = 'pm_report' in st.session_state
        has_mm_report = 'mm_report' in st.session_state
        has_med_report = 'med_report' in st.session_state
        has_sm_report = 'sm_report' in st.session_state
        
        if has_pm_report or has_mm_report or has_med_report or has_sm_report:
            report_info = []
            if has_pm_report:
                report_info.append("「产品经理」")
            if has_mm_report:
                report_info.append("「市场经理」")
            if has_med_report:
                report_info.append("「医学经理」")
            if has_sm_report:
                report_info.append("「新媒体经理」")
            
            st.info(f"💡 已检测到 {' 和 '.join(report_info)} 报告！您可以直接使用这些分析结果。")
            if st.button("📥 使用上游报告的信息", key="use_reports_design"):
                st.session_state['auto_fill_design'] = True
                st.rerun()
        
        # 自动填充逻辑
        if st.session_state.get('auto_fill_design', False):
            # 从产品经理报告填充基础信息
            if has_pm_report:
                st.session_state['design_filled_product_name'] = st.session_state.get('pm_project_name', project_name)
                st.session_state['design_filled_selling_points'] = st.session_state.get('pm_product_concept', "温和焕肤不刺激、提亮肤色、改善肤质")
                # 从目标用户中提取简化版
                target_users_full = st.session_state.get('pm_target_users', '')
                if target_users_full and len(target_users_full) > 100:
                    st.session_state['design_filled_target_audience'] = target_users_full[:100] + "..."
                elif target_users_full:
                    st.session_state['design_filled_target_audience'] = target_users_full
                else:
                    st.session_state['design_filled_target_audience'] = "25-35岁、注重护肤成分和温和性"
            
            # 从市场经理报告补充品牌定位信息
            if has_mm_report:
                st.session_state['design_filled_brand_positioning'] = "基于市场经理策略的品牌定位"
            
            # 从新媒体经理报告获取内容摘要
            if has_sm_report:
                sm_report_excerpt = st.session_state.get('sm_report', '')[:200]
                if sm_report_excerpt:
                    st.session_state['design_filled_media_content'] = f"新媒体核心策略摘要：{sm_report_excerpt}..."
            
            st.session_state['auto_fill_design'] = False  # 重置标记
        
        # 智能默认值：自动检测并使用上游报告
        if 'design_filled_product_name' not in st.session_state and has_pm_report:
            default_product_name = st.session_state.get('pm_project_name', project_name)
        else:
            default_product_name = st.session_state.get('design_filled_product_name', project_name)
        
        if 'design_filled_selling_points' not in st.session_state and has_pm_report:
            default_selling_points = st.session_state.get('pm_product_concept', "温和焕肤不刺激、提亮肤色、改善肤质")
        else:
            default_selling_points = st.session_state.get('design_filled_selling_points', "温和焕肤不刺激、提亮肤色、改善肤质")
        
        if 'design_filled_target_audience' not in st.session_state and has_pm_report:
            target_users_full = st.session_state.get('pm_target_users', '')
            if target_users_full and len(target_users_full) > 100:
                default_target_audience = target_users_full[:100] + "..."
            elif target_users_full:
                default_target_audience = target_users_full
            else:
                default_target_audience = "25-35岁、注重护肤成分和温和性"
        else:
            default_target_audience = st.session_state.get('design_filled_target_audience', "25-35岁、注重护肤成分和温和性")
        
        if 'design_filled_media_content' not in st.session_state and has_sm_report:
            sm_report_excerpt = st.session_state.get('sm_report', '')[:200]
            default_media_content = f"新媒体核心策略摘要：{sm_report_excerpt}..." if sm_report_excerpt else "通过AI新媒体经理生成的文案摘要，供设计参考。"
        else:
            default_media_content = st.session_state.get('design_filled_media_content', "通过AI新媒体经理生成的文案摘要，供设计参考。")

        product_name_design = st.text_input("【医美新产品名称】：", value=default_product_name)
        core_selling_points_design = st.text_area("产品【核心卖点】：", default_selling_points, height=80)
        target_audiences_design = st.text_area("【目标受众】：", default_target_audience, height=100)
        media_content_design = st.text_area("【新媒体核心文案/内容摘要】（可选）：", 
                                           default_media_content, height=100)
        output_language_design = st.radio("输出语言：", ("简体中文", "繁体中文", "English"), index=0, key="design_lang")
        
        if st.button("生成设计方案报告", key="run_design_agent"):
            if product_name_design and core_selling_points_design and target_audiences_design:
                with st.status("设计经理Agent正在构思视觉方案...", expanded=True) as status:
                    st.write("正在转化营销信息为视觉语言，确保品牌一致性...")
                    time.sleep(2)
                    try:
                        design_prompt = f"""
                        你是一名资深、全面的AI设计经理，专注于医美、皮肤科学和生物技术领域的品牌视觉和用户体验。你具备卓越的审美能力、策略性思维和将抽象概念具象化的能力。你精通用户体验（UX）、用户界面（UI）、品牌视觉识别（VI）和营销物料设计的核心原则。你能够将来自其他AI Agent（产品、市场、新媒体）的信息转化为直观、有吸引力且符合品牌调性的视觉解决方案，并能指导设计方向，确保品牌视觉一致性和营销效果的最大化，致力于将设计沟通成本降到最低，实现"高效出图，精准沟通"。核心能力：
                        • 品牌视觉策略与管理： 维护和发展品牌视觉识别（VI）系统，确保所有设计产出都符合品牌规范和整体调性。能够将品牌理念转化为视觉语言。
                        • 营销物料设计与指导： 构思并指导各类营销物料（如海报、广告图、社交媒体配图、H5页面、视频动画元素等）的设计方向、风格和关键视觉元素，以最大化营销信息的传播效果。
                        • 用户体验（UX）与用户界面（UI）设计： 为产品或工具（如小程序、App界面）提供初步的UI/UX设计方案、线框图或用户流程草图，确保产品的易用性和美观性。
                        • 设计趋势洞察： 追踪医美行业和数字媒体最新的设计趋势和审美偏好，为设计创新提供灵感和方向。
                        • 跨Agent协作与沟通： 将其他Agent的输出（产品卖点、营销文案、医学信息）有效地转化为视觉需求，并能够解释设计决策背后的策略思考。
                        • 设计效果评估与优化： 能够初步评估设计方案在目标受众中的接受度和传播效果，并提出优化建议。
                        工作模式：
                        接收来自"总指挥"（用户）的品牌策略、产品信息、营销文案、用户体验需求或特定的设计任务。输出结构化的设计概念报告、多方案视觉草图、UI/UX线框图、品牌视觉指导原则、营销物料设计方向或设计元素建议。能够紧密协调和指导其他AI Agent（产品、市场、新媒体）的输出，确保视觉传达与整体营销战略和品牌形象高度一致。

                        你现在是一名专业的AI设计经理，请为我们的{product_name_design}设计一套完整的上市前期视觉方案。
                        产品核心卖点是【{core_selling_points_design}】，目标受众是【{target_audiences_design}】。AI新媒体已撰写了多个平台的核心文案，摘要如下（供参考）：{media_content_design}

                        请你：
                        1. 根据产品特点和目标受众，构思3个不同的核心视觉风格概念（例如：科技极简、自然纯粹、临床专业），并说明每个风格如何体现产品价值和品牌调性。
                        2. 针对每个风格，提出一套完整的视觉元素清单（如主色调、辅助色、字体风格、图像/插画风格、排版布局特点），并提供可用于AI绘图工具生成的关键词或具体描述。
                        3. 为小红书、Instagram等社交媒体平台设计3-5款概念海报（或系列图）的视觉草图或排版建议，确保它们能够最大化地吸引目标受众并突出产品优势。
                        4. 请简要说明如何确保这些视觉方案能够与整体品牌形象和营销策略保持高度一致。
                        5. 需要有非常好的品味和审美敏感度。
                        请以一份结构清晰、创意丰富、兼具策略性和落地性的设计方案报告形式输出，使用{output_language_design}。
                        """
                        design_report = call_gemini(
                            system_prompt=design_prompt,
                            user_prompt=f"请为 {product_name_design} 生成设计方案。",
                            model="gemini-2.5-flash"
                        )
                        st.session_state['design_report'] = design_report
                        st.session_state['design_product_name'] = product_name_design
                        status.update(label="方案生成完成！", state="complete", expanded=False)
                            
                    except Exception as e:
                        status.update(label="方案生成失败！", state="error", expanded=True)
                        st.error(f"生成方案失败: {e}")
            else:
                st.warning("请填写所有必填信息。")
        
        # 显示生成的报告（持久显示）
        if 'design_report' in st.session_state:
            st.markdown("---")
            st.subheader("✅ 设计经理报告：")
            st.markdown(st.session_state['design_report'])
            
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.download_button(
                    label="📥 导出为Markdown",
                    data=f"# 设计经理报告\n\n**产品**: {st.session_state.get('design_product_name', '')}\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n{st.session_state['design_report']}",
                    file_name=f"设计经理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    key="design_md_download_persistent"
                ):
                    st.success("文件已准备下载！")
            with col2:
                pdf_data = generate_pdf_report(
                    title="设计经理报告",
                    content=st.session_state['design_report'],
                    metadata={"产品": st.session_state.get('design_product_name', ''), "生成时间": datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                )
                if st.download_button(
                    label="📄 导出为PDF",
                    data=pdf_data,
                    file_name=f"设计经理报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key="design_pdf_download_persistent"
                ):
                    st.success("PDF已准备下载！")


# --- 底部信息 ---
st.sidebar.markdown("---")
st.sidebar.info("【智慧放大引擎】敬请期待！")

st.markdown("---")
st.caption("© 2024 【德美颜】AI增长架构师. Powered by Streamlit & OpenAI. 您专属的精益增长伙伴。")

import streamlit as st
import time
from datetime import datetime
from agents import AgentSystem
import json

# 页面配置
st.set_page_config(
    page_title="TalkSense 言感 - 多智能体社交助手",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS样式，模拟微信群聊界面
st.markdown("""
<style>
    /* 隐藏 Streamlit 默认元素 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 主容器样式 - 微信灰色背景 */
    .stApp {
        background: #ededed;
    }
    
    /* 聊天窗口容器 */
    .chat-window {
        max-width: 900px;
        margin: 0 auto;
        background: #ededed;
        min-height: 70vh;
        padding: 10px;
    }
    
    /* 消息容器 */
    .message-wrapper {
        display: flex;
        margin: 8px 0;
        animation: fadeIn 0.3s;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(5px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* 用户消息（右侧对齐） */
    .message-wrapper.user {
        flex-direction: row-reverse;
    }
    
    /* 头像样式 */
    .avatar {
        width: 40px;
        height: 40px;
        border-radius: 4px;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        font-weight: bold;
        margin: 0 8px;
    }
    
    /* 智能体头像颜色 */
    .avatar-trend { background: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 100%); }
    .avatar-diplomat { background: linear-gradient(135deg, #4ecdc4 0%, #6eddd6 100%); }
    .avatar-shooter { background: linear-gradient(135deg, #ffe66d 0%, #fff089 100%); }
    .avatar-romance { background: linear-gradient(135deg, #a8e6cf 0%, #c4f0dd 100%); }
    .avatar-user { background: linear-gradient(135deg, #95ec69 0%, #b0f08a 100%); }
    
    /* 消息内容区域 */
    .message-content {
        max-width: 60%;
        display: flex;
        flex-direction: column;
    }
    
    /* 消息发送者名字 */
    .sender-name {
        font-size: 12px;
        color: #888;
        margin-bottom: 4px;
        padding: 0 4px;
    }
    
    .message-wrapper.user .sender-name {
        text-align: right;
    }
    
    /* 消息气泡 */
    .message-bubble {
        padding: 10px 14px;
        border-radius: 4px;
        word-wrap: break-word;
        line-height: 1.5;
        position: relative;
    }
    
    /* 用户消息气泡（绿色，右侧） */
    .message-wrapper.user .message-bubble {
        background: #95ec69;
        color: #000;
        border-top-right-radius: 0;
    }
    
    /* 智能体消息气泡（白色，左侧） */
    .message-wrapper.agent .message-bubble {
        background: #ffffff;
        color: #000;
        border-top-left-radius: 0;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    /* 消息时间戳 */
    .message-time {
        font-size: 11px;
        color: #999;
        margin-top: 4px;
        padding: 0 4px;
    }
    
    .message-wrapper.user .message-time {
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'agent_system' not in st.session_state:
    st.session_state.agent_system = AgentSystem()
def render_message(message, is_user=False, agent_name=None, timestamp=None):
    """渲染单条消息，类似微信群聊样式"""
    # 智能体信息映射
    agent_info = {
        "爽爽": {
            "name": "爽爽",
            "emoji": "✨",
            "avatar_class": "avatar-trend"
        },
        "温荣": {
            "name": "温荣",
            "emoji": "💝",
            "avatar_class": "avatar-diplomat"
        },
        "张凉": {
            "name": "张凉",
            "emoji": "🧊",
            "avatar_class": "avatar-shooter"
        }
    }
    
    if is_user:
        # 用户消息
        wrapper_class = "user"
        sender_name = "我"
        avatar_emoji = "👤"
        avatar_class = "avatar-user"
    else:
        # 智能体消息
        wrapper_class = "agent"
        if agent_name and agent_name in agent_info:
            info = agent_info[agent_name]
            sender_name = f"{info['emoji']} {info['name']}"
            avatar_emoji = info['emoji']
            avatar_class = info['avatar_class']
        else:
            sender_name = "智能体"
            avatar_emoji = "🤖"
            avatar_class = "avatar-trend"
    
    # 格式化时间
    time_str = ""
    if timestamp:
        try:
            time_str = timestamp.strftime("%H:%M")
        except:
            pass
    
    html = f"""
    <div class="message-wrapper {wrapper_class}">
        <div class="avatar {avatar_class}">{avatar_emoji}</div>
        <div class="message-content">
            <div class="sender-name">{sender_name}</div>
            <div class="message-bubble">{message}</div>
            {f'<div class="message-time">{time_str}</div>' if time_str else ''}
        </div>
    </div>
    """
    return html

# 主界面
st.markdown("""
<div style="text-align: center; padding: 8px 15px 6px 15px; background: #ededed; border-bottom: 1px solid #d4d4d4; margin-bottom: 0;">
    <h3 style="margin: 0; color: #333; font-size: 18px;">💬 TalkSense 言感 智囊团</h3>
    <p style="margin: 2px 0 0 0; font-size: 11px; color: #888;">多智能体社交助手 - 3位好友为你出谋划策</p>
</div>
""", unsafe_allow_html=True)

# 聊天历史显示区域
st.markdown('<div class="chat-window" style="padding-top: 0;">', unsafe_allow_html=True)

if len(st.session_state.messages) == 0:
    st.markdown("""
    <div style="text-align: center; padding: 8px 20px 10px 20px; color: #999;">
        <div style="font-size: 32px; margin-bottom: 5px;">👋</div>
        <h3 style="color: #666; margin-bottom: 4px; font-size: 15px;">欢迎使用 TalkSense 言感！</h3>
        <p style="color: #888; font-size: 12px; margin: 0;">输入你的社交场景，3位智能体好友会为你提供多角度的回复建议～</p>
    </div>
    """, unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        if msg['type'] == 'user':
            st.markdown(render_message(
                msg['content'], 
                is_user=True, 
                timestamp=msg.get('timestamp')
            ), unsafe_allow_html=True)
        elif msg['type'] == 'agent':
            st.markdown(render_message(
                msg['content'], 
                is_user=False, 
                agent_name=msg.get('agent'),
                timestamp=msg.get('timestamp')
            ), unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# 输入区域 - 微信风格
st.markdown("""
<div style="background: #f7f7f7; padding: 15px; border-top: 1px solid #d4d4d4;">
</div>
""", unsafe_allow_html=True)

# 使用 form 来包装输入框，提交后可以自动清空
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "💭 输入你的社交场景或对话内容",
            placeholder="例如：同事在群里@我，说我工作有问题，但我觉得他在针对我...",
            label_visibility="collapsed"
        )
    with col2:
        send_button = st.form_submit_button("发送", type="primary", use_container_width=True)

# 处理用户输入
if send_button and user_input:
    # 保存用户输入
    input_text = user_input
    
    # 添加用户消息
    st.session_state.messages.append({
        'type': 'user',
        'content': input_text,
        'timestamp': datetime.now()
    })
    
    # 显示智能体回复（每个智能体会自己分析意图）
    with st.spinner("🤔 智囊团正在思考中..."):
        agent_responses = st.session_state.agent_system.get_responses(input_text)
        
        for agent_name, response in agent_responses.items():
            st.session_state.messages.append({
                'type': 'agent',
                'content': response,
                'agent': agent_name,
                'timestamp': datetime.now()
            })
    
    # 重新运行以更新界面
    st.rerun()

# 侧边栏说明
with st.sidebar:
    st.header("📖 使用说明")
    st.markdown("""
    ### 功能特点
    
    **🔍 深层意图解析**
    - 分析输入文本的真实意图
    - 识别情绪状态
    - 解读文字背后的潜台词
    
    **👥 智囊团回复体系**
    
    - **✨ 爽爽**：以自我为主的体验玩家，高能量Alpha
    - **💝 温荣**：无条件站队的情绪嘴替，温柔托底
    - **🧊 张凉**：犀利直球手，事实大于情绪，帮你止损
    
    ### 使用场景
    
    - 职场沟通难题
    - 社交尴尬时刻
    - 暧昧关系处理
    - 边界设立与回怼
    - 日常聊天建议
    """)
    
    st.markdown("---")
    if st.button("🗑️ 清空对话历史"):
        st.session_state.messages = []
        st.rerun()


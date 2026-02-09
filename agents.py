"""
多智能体系统：包含4个不同风格的AI智能体
每个问题都会让4个智能体都回答，提供不同视角的建议
"""
import os
import time
from typing import Dict, List, Any
from prompts import AGENT_PROMPTS

# 尝试加载 dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class AgentSystem:
    """多智能体系统"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        # 智能体名称列表，所有prompt都在prompts.py中定义
        self.agent_names = list(AGENT_PROMPTS.keys())
    
    def get_responses(self, user_input: str) -> Dict[str, str]:
        """
        获取所有智能体的回复
        每个问题都会让4个智能体都回答，提供不同视角的建议
        每个智能体会自己分析意图并给出回复
        
        Args:
            user_input: 用户输入的原始文本
            
        Returns:
            包含各智能体回复的字典，键为智能体名称，值为回复内容
        """
        responses = {}
        
        # 遍历所有智能体，每个都回答同一个问题
        for i, agent_name in enumerate(self.agent_names):
            if self.api_key:
                # 在请求之间添加延迟，避免API过载
                if i > 0:
                    time.sleep(0.5)  # 每个请求间隔0.5秒
                response = self._get_gemini_response(agent_name, user_input)
            else:
                response = self._get_demo_response(agent_name, user_input)
            
            responses[agent_name] = response
        
        return responses
    
    def _get_gemini_response(self, agent_name: str, user_input: str, max_retries: int = 3) -> str:
        """使用Gemini API生成智能体回复，每个角色使用对应的prompt，自己分析意图
        
        Args:
            agent_name: 智能体名称
            user_input: 用户输入
            max_retries: 最大重试次数（默认3次）
        """
        from google import genai
        
        # 创建Gemini客户端
        client = genai.Client(api_key=self.api_key)
        
        # 从prompts.py获取对应角色的prompt模板
        prompt_template = AGENT_PROMPTS.get(agent_name, "")
        if not prompt_template:
            raise ValueError(f"未找到智能体 {agent_name} 的prompt模板")
        
        # 填充prompt模板（只传入用户输入，让LLM自己分析意图）
        prompt = prompt_template.format(user_input=user_input)
        
        # 重试机制：对于503等临时错误进行重试
        for attempt in range(max_retries):
            try:
                # 调用Gemini API生成回复
                response = client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt,
                )
                
                # 处理响应，只提取文本部分，忽略thought_signature等非文本部分
                if hasattr(response, 'candidates') and response.candidates:
                    # 从candidates中提取文本部分
                    text_parts = []
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(part.text)
                    if text_parts:
                        return ''.join(text_parts).strip()
                
                # 如果上述方法失败，尝试使用text属性
                if hasattr(response, 'text'):
                    return response.text.strip()
                
                # 如果都失败，返回错误信息
                return "抱歉，无法获取回复内容。"
                
            except Exception as e:
                error_str = str(e)
                
                # 检查是否是配额限制错误
                is_quota_error = (
                    'quota' in error_str.lower() or
                    'QuotaFailure' in error_str or
                    '429' in error_str or
                    'RESOURCE_EXHAUSTED' in error_str
                )
                
                # 检查是否是503错误（模型过载）或其他可重试的错误
                is_retryable = (
                    '503' in error_str or 
                    'UNAVAILABLE' in error_str or
                    'overloaded' in error_str.lower() or
                    'rate limit' in error_str.lower()
                )
                
                if is_quota_error:
                    # 配额限制错误，不重试，直接返回友好提示
                    return f"⚠️ API配额已用完（每日免费额度20次）。请明天再试，或升级到付费计划。\n\n💡 提示：你可以暂时使用演示模式，虽然回复是预设的，但也能提供参考。"
                
                if is_retryable and attempt < max_retries - 1:
                    # 指数退避：等待时间逐渐增加
                    wait_time = (2 ** attempt) * 0.5  # 0.5秒, 1秒, 2秒
                    print(f"Gemini API调用失败 ({agent_name})，{wait_time}秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    # 最后一次尝试失败，或者不是可重试的错误
                    print(f"Gemini API调用失败 ({agent_name}): {e}")
                    # 如果API调用失败，回退到演示模式
                    return self._get_demo_response(agent_name, user_input)
        
        # 所有重试都失败了
        print(f"Gemini API调用失败 ({agent_name})，已重试{max_retries}次，使用演示模式")
        return self._get_demo_response(agent_name, user_input)
    
    def _get_demo_response(self, agent_name: str, user_input: str) -> str:
        """生成演示回复（当没有API时使用）"""
    
        return "根据你的情况，我建议你保持冷静，理性分析，然后做出最适合你的决定。"


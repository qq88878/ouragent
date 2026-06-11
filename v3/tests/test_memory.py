"""
Redis 记忆系统测试
测试会话管理、对话历史、画像缓存功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.memory.redis_client import get_redis, RedisClient, close_redis
from src.core.memory.session_manager import SessionManager
from src.core.memory.conversation_memory import ConversationMemory
from src.core.memory.profile_cache import ProfileCache


async def test_memory_system():
    """测试记忆系统"""
    print("=" * 50)
    print("Redis 记忆系统测试")
    print("=" * 50)

    # 初始化
    print("\n1. 初始化 Redis 连接...")
    try:
        redis_conn = await get_redis()
        client = RedisClient(redis_conn)
        health = await client.health_check()
        print(f"   Redis 连接状态: {'✓ 正常' if health else '✗ 失败'}")
        if not health:
            print("   Redis 未启动，跳过测试")
            return
    except Exception as e:
        print(f"   Redis 连接失败: {e}")
        print("   请确保 Redis 服务已启动")
        return

    # 测试会话管理
    print("\n2. 测试会话管理...")
    session_mgr = SessionManager(client)

    # 创建会话
    session_id = await session_mgr.create_session(
        user_id="test_user_001",
        course_id=1,
    )
    print(f"   创建会话: {session_id}")

    # 获取会话
    session = await session_mgr.get_session(session_id)
    print(f"   获取会话: user_id={session['user_id']}, course_id={session['course_id']}")

    # 更新会话
    await session_mgr.touch_session(session_id)
    session = await session_mgr.get_session(session_id)
    print(f"   消息计数: {session['message_count']}")

    # 列出用户会话
    sessions = await session_mgr.list_user_sessions("test_user_001")
    print(f"   用户会话数: {len(sessions)}")

    # 测试对话历史
    print("\n3. 测试对话历史...")
    conv = ConversationMemory(client, session_id)

    # 添加消息
    await conv.add_message("user", "什么是Python列表？")
    await conv.add_message("assistant", "Python列表是一种有序、可变的数据结构...")
    await conv.add_message("user", "它和元组有什么区别？")
    await conv.add_message("assistant", "主要区别在于可变性...")

    count = await conv.get_message_count()
    print(f"   消息总数: {count}")

    # 获取历史
    history = await conv.get_history(limit=10)
    print(f"   获取历史: {len(history)} 条")
    for msg in history:
        print(f"     [{msg['role']}] {msg['content'][:20]}...")

    # 获取 LLM 上下文
    llm_context = await conv.get_recent_context_for_llm(max_messages=5)
    print(f"   LLM 上下文: {len(llm_context)} 条")

    # 测试画像缓存
    print("\n4. 测试画像缓存...")
    profile_cache = ProfileCache(client)

    # 设置画像
    profile_data = {
        "learning_style": "visual",
        "weaknesses": ["递归", "数据结构"],
        "strengths": ["循环", "条件语句"],
        "grade_level": "beginner",
    }
    await profile_cache.set_profile("test_user_001", profile_data, course_id=1)
    print(f"   缓存画像: learning_style={profile_data['learning_style']}")

    # 获取画像
    cached_profile = await profile_cache.get_profile("test_user_001", course_id=1)
    print(f"   获取画像: {cached_profile is not None}")
    if cached_profile:
        print(f"     learning_style: {cached_profile.get('learning_style')}")
        print(f"     weaknesses: {cached_profile.get('weaknesses')}")

    # 清理
    print("\n5. 清理测试数据...")
    await session_mgr.delete_session(session_id)
    await profile_cache.invalidate_profile("test_user_001", course_id=1)
    print("   清理完成")

    # 关闭连接
    await close_redis()

    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_memory_system())

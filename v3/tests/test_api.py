"""
API 端点集成测试
使用 pytest 和 httpx.AsyncClient
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from src.api import app


@pytest.fixture
def mock_orchestrator():
    """模拟 Orchestrator"""
    mock = AsyncMock()
    mock.chat.return_value = "这是一个测试回复"
    mock.create_session.return_value = "test-session-id"
    mock.get_session.return_value = {
        "session_id": "test-session-id",
        "user_id": "test-user",
        "course_id": 1,
        "created_at": "2026-06-11T10:00:00",
        "last_active": "2026-06-11T10:00:00",
        "message_count": 0,
    }
    mock.get_conversation_history.return_value = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
    ]
    mock.list_user_sessions.return_value = []
    mock.get_status.return_value = {
        "agents": ["profile_agent", "planner_agent", "resource_agent", "evaluator_agent"],
        "tools": ["knowledge_retrieval", "web_search"],
        "rag": {"total_chunks": 0, "embedding_provider": "LocalEmbeddingProvider", "chunk_size": 500},
        "llm": "OpenAIProvider",
        "memory": {"redis_connected": True},
    }
    return mock


@pytest.fixture
def mock_auth():
    """模拟认证"""
    return {"user_id": "test-user", "role": "student"}


@pytest.mark.asyncio
async def test_health_check():
    """测试健康检查端点"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_agent_status(mock_orchestrator, mock_auth):
    """测试 Agent 状态端点"""
    import src.api as api_module
    api_module.orchestrator = mock_orchestrator

    with patch("src.api.get_current_user", return_value=mock_auth):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/agent/status")
            assert response.status_code == 200
            data = response.json()
            assert "agents" in data
            assert "tools" in data
            assert len(data["agents"]) == 4


@pytest.mark.asyncio
async def test_chat_endpoint(mock_orchestrator, mock_auth):
    """测试对话端点"""
    import src.api as api_module
    api_module.orchestrator = mock_orchestrator

    with patch("src.api.get_current_user", return_value=mock_auth):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/agent/chat",
                json={"message": "你好", "session_id": "550e8400-e29b-41d4-a716-446655440000"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["response"] == "这是一个测试回复"
            assert data["status"] == "success"
            mock_orchestrator.chat.assert_called_once()


@pytest.mark.asyncio
async def test_chat_validation_error(mock_orchestrator, mock_auth):
    """测试对话参数验证"""
    import src.api as api_module
    api_module.orchestrator = mock_orchestrator

    with patch("src.api.get_current_user", return_value=mock_auth):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 空消息
            response = await client.post("/agent/chat", json={"message": ""})
            assert response.status_code == 422

            # 无效 session_id 格式
            response = await client.post(
                "/agent/chat",
                json={"message": "你好", "session_id": "invalid"},
            )
            assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_session(mock_orchestrator, mock_auth):
    """测试创建会话"""
    import src.api as api_module
    api_module.orchestrator = mock_orchestrator

    with patch("src.api.get_current_user", return_value=mock_auth):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/agent/sessions",
                json={"user_id": "test-user", "course_id": 1},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "test-session-id"
            assert data["status"] == "created"


@pytest.mark.asyncio
async def test_get_session_history(mock_orchestrator, mock_auth):
    """测试获取会话历史"""
    import src.api as api_module
    api_module.orchestrator = mock_orchestrator

    with patch("src.api.get_current_user", return_value=mock_auth):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/agent/sessions/test-session-id/history",
                params={"limit": 10},
            )
            assert response.status_code == 200
            data = response.json()
            assert "messages" in data
            assert len(data["messages"]) == 2


@pytest.mark.asyncio
async def test_generate_resource_validation(mock_orchestrator, mock_auth):
    """测试资源生成参数验证"""
    import src.api as api_module
    api_module.orchestrator = mock_orchestrator

    with patch("src.api.get_current_user", return_value=mock_auth):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 无效类型
            response = await client.post(
                "/agent/generate",
                json={"type": "invalid", "topic": "Python"},
            )
            assert response.status_code == 422

            # 无效难度
            response = await client.post(
                "/agent/generate",
                json={"type": "question", "topic": "Python", "difficulty": "invalid"},
            )
            assert response.status_code == 422

            # 超出数量限制
            response = await client.post(
                "/agent/generate",
                json={"type": "question", "topic": "Python", "count": 100},
            )
            assert response.status_code == 422


@pytest.mark.asyncio
async def test_service_unavailable():
    """测试服务未初始化"""
    import src.api as api_module
    api_module.orchestrator = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/agent/chat",
            json={"message": "你好"},
        )
        assert response.status_code == 503

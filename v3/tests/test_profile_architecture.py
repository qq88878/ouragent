"""User Profile Architecture Tests - Two-Tier Profile System

Tests:
  1. Basic profile is shared across courses (same user -> same basic profile)
  2. Course profiles are independent per course
  3. ProfileCache key structure (basic=global, course=not cached)
  4. Edge cases: empty data, fallback, invalid JSON
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.agents.profile_agent import ProfileAgent
from src.core.memory.profile_cache import ProfileCache, PROFILE_TTL
from src.core.utils import parse_llm_json


# ==================== 1. Basic Profile: Shared Across Courses ====================


class TestBasicProfileShared:
    """Test that basic profile is shared across courses (one per user, not per course)"""

    BASIC_LLM_RESPONSE_FOR_CS_STUDENT = json.dumps({
        "learning_style": "VISUAL",
        "grade_level": "INTERMEDIATE",
        "interests": ["Python", "Java"],
        "strengths": ["logic", "debugging"],
        "weaknesses": ["algorithm design"],
        "recommended_methods": ["VIDEO", "READING"],
        "recommended_strategy": "Focus on algorithm practice",
        "study_pace": "MODERATE",
        "education_level": "BACHELOR",
        "major": "CS",
        "confidence": 0.85
    })

    @pytest.fixture
    def agent(self, mock_llm):
        mock_llm.chat.return_value = self.BASIC_LLM_RESPONSE_FOR_CS_STUDENT
        return ProfileAgent(llm=mock_llm)

    @pytest.mark.asyncio
    async def test_basic_profile_same_user_same_result(self, agent):
        """Same user with same questionnaire -> same basic profile"""
        q_data = {
            "education_level": "BACHELOR",
            "major_direction": "CS",
            "learning_goals": ["EMPLOYMENT"],
            "learning_methods": ["VIDEO", "READING"],
            "self_strengths": ["COMPREHENSION"],
            "self_weaknesses": ["MEMORY"],
        }
        r1 = await agent.analyze_basic_profile(questionnaire_data=q_data)
        r2 = await agent.analyze_basic_profile(questionnaire_data=q_data)
        assert r1["learning_style"] == r2["learning_style"]
        assert r1["grade_level"] == r2["grade_level"]
        assert r1["interests"] == r2["interests"]

    @pytest.mark.asyncio
    async def test_basic_profile_from_different_courses_same_result(self, agent):
        """Basic profile does NOT depend on course_id - same user, any course"""
        q_data = {
            "education_level": "BACHELOR",
            "major_direction": "CS",
        }
        # Simulating call from course_id=1 (Python course)
        r_course1 = await agent.analyze_basic_profile(questionnaire_data=q_data)
        # Simulating call from course_id=2 (Java course) - same questionnaire
        r_course2 = await agent.analyze_basic_profile(questionnaire_data=q_data)
        # Basic profile should be identical regardless of which course triggered it
        assert r_course1["learning_style"] == r_course2["learning_style"]
        assert r_course1["interests"] == r_course2["interests"]
        assert r_course1["strengths"] == r_course2["strengths"]

    @pytest.mark.asyncio
    async def test_basic_profile_contains_all_required_fields(self, agent):
        """Basic profile returns all expected fields"""
        q_data = {
            "education_level": "MASTER",
            "major_direction": "AI",
            "learning_goals": ["POSTGRADUATE"],
            "learning_methods": ["DISCUSSION"],
            "self_strengths": ["FOCUS"],
            "self_weaknesses": ["EXPRESSION"],
        }
        result = await agent.analyze_basic_profile(questionnaire_data=q_data)
        required_fields = [
            "learning_style", "grade_level", "interests",
            "strengths", "weaknesses", "recommended_methods",
            "recommended_strategy", "study_pace", "confidence"
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"

    @pytest.mark.asyncio
    async def test_basic_profile_with_minimal_questionnaire(self, agent, mock_llm):
        """Basic profile works with only required fields (empty optional fields)"""
        mock_llm.chat.return_value = json.dumps({
            "learning_style": "READING",
            "grade_level": "BEGINNER",
            "interests": [],
            "strengths": [],
            "weaknesses": [],
            "recommended_methods": [],
            "recommended_strategy": "Start with basics",
            "study_pace": "SLOW",
            "confidence": 0.5
        })
        result = await agent.analyze_basic_profile(questionnaire_data={})
        assert result["learning_style"] == "READING"
        assert result["grade_level"] == "BEGINNER"

    @pytest.mark.asyncio
    async def test_basic_profile_llm_failure_fallback(self, agent, mock_llm):
        """When LLM returns invalid JSON, fallback is used"""
        mock_llm.chat.return_value = "not valid json at all!!!"
        result = await agent.analyze_basic_profile(questionnaire_data={
            "education_level": "BACHELOR",
        })
        # Should get fallback values
        assert result["learning_style"] == "VISUAL"
        assert result["grade_level"] == "BEGINNER"
        assert "raw_response" in result


# ==================== 2. Course Profile: Independent Per Course ====================


class TestCourseProfileIndependent:
    """Test that each course gets its own independent course profile"""

    BASIC_PROFILE = {
        "learning_style": "VISUAL",
        "grade_level": "INTERMEDIATE",
        "interests": ["Python", "AI"],
        "strengths": ["comprehension", "debugging"],
        "weaknesses": ["recursion", "algorithm"],
        "recommended_methods": ["VIDEO"],
        "recommended_strategy": "Practice coding daily",
        "study_pace": "MODERATE",
    }

    @pytest.fixture
    def agent(self, mock_llm):
        return ProfileAgent(llm=mock_llm)

    @pytest.mark.asyncio
    async def test_course_profiles_different_for_different_courses(self, agent, mock_llm):
        """Course profile differs based on chat history content"""
        # Course A (Python) - student struggles with recursion
        mock_llm.chat.return_value = json.dumps({
            "course_strengths": ["list", "dictionary"],
            "course_weaknesses": ["recursion"],
            "topics_discussed": ["Python lists", "Python dicts", "recursion"],
            "engagement_level": "HIGH",
            "questions_frequency": "FREQUENT",
            "summary": "Good at basics but struggles with recursion"
        })
        r_python = await agent.analyze_course_profile(
            basic_profile=self.BASIC_PROFILE,
            chat_history=[
                {"role": "user", "content": "How to use Python lists?"},
                {"role": "assistant", "content": "Python lists are..."},
                {"role": "user", "content": "I don't understand recursion"},
            ],
        )

        # Course B (Java) - student excels at OOP
        mock_llm.chat.return_value = json.dumps({
            "course_strengths": ["OOP", "inheritance"],
            "course_weaknesses": ["generics"],
            "topics_discussed": ["Java classes", "inheritance", "generics"],
            "engagement_level": "MEDIUM",
            "questions_frequency": "MODERATE",
            "summary": "Strong OOP understanding, needs work on generics"
        })
        r_java = await agent.analyze_course_profile(
            basic_profile=self.BASIC_PROFILE,
            chat_history=[
                {"role": "user", "content": "What is inheritance in Java?"},
                {"role": "assistant", "content": "Inheritance allows..."},
            ],
        )

        # Course profiles should differ
        assert r_python["course_strengths"] != r_java["course_strengths"]
        assert r_python["course_weaknesses"] != r_java["course_weaknesses"]
        assert r_python["topics_discussed"] != r_java["topics_discussed"]

    @pytest.mark.asyncio
    async def test_course_profile_empty_chat_history(self, agent):
        """Course profile with empty chat history returns default"""
        result = await agent.analyze_course_profile(
            basic_profile=self.BASIC_PROFILE,
            chat_history=[],
        )
        assert result["engagement_level"] == "UNKNOWN"
        assert result["course_strengths"] == []
        assert result["course_weaknesses"] == []
        assert result["topics_discussed"] == []
        assert "note" in result

    @pytest.mark.asyncio
    async def test_course_profile_with_study_records(self, agent, mock_llm):
        """Course profile incorporates study records"""
        mock_llm.chat.return_value = json.dumps({
            "course_strengths": ["variables"],
            "course_weaknesses": ["loops"],
            "topics_discussed": ["variables", "loops"],
            "engagement_level": "HIGH",
            "questions_frequency": "FREQUENT",
            "summary": "Improving"
        })
        result = await agent.analyze_course_profile(
            basic_profile=self.BASIC_PROFILE,
            chat_history=[
                {"role": "user", "content": "How do for loops work?"},
            ],
            study_records=[
                {"topic": "variables", "score": 90, "time_spent": 30},
                {"topic": "loops", "score": 55, "time_spent": 60},
            ],
        )
        assert "course_strengths" in result
        assert "course_weaknesses" in result

    @pytest.mark.asyncio
    async def test_course_profile_does_not_persist_between_calls(self, agent, mock_llm):
        """Each call to analyze_course_profile is independent - no caching"""
        # Call 1
        mock_llm.chat.return_value = json.dumps({
            "course_strengths": ["topic_a"],
            "course_weaknesses": [],
            "topics_discussed": ["topic_a"],
            "engagement_level": "HIGH",
        })
        r1 = await agent.analyze_course_profile(
            basic_profile=self.BASIC_PROFILE,
            chat_history=[{"role": "user", "content": "About topic A"}],
        )

        # Call 2 - different chat_history, different result (no caching)
        mock_llm.chat.return_value = json.dumps({
            "course_strengths": ["topic_b"],
            "course_weaknesses": ["topic_c"],
            "topics_discussed": ["topic_b", "topic_c"],
            "engagement_level": "MEDIUM",
        })
        r2 = await agent.analyze_course_profile(
            basic_profile=self.BASIC_PROFILE,
            chat_history=[{"role": "user", "content": "About topic B"}],
        )

        # Results should differ (no caching interference)
        assert r1["course_strengths"] != r2["course_strengths"]
        assert r1["topics_discussed"] != r2["topics_discussed"]


# ==================== 3. ProfileCache: Key Structure ====================


class TestProfileCacheKeys:
    """Test ProfileCache key naming and isolation"""

    @pytest.fixture
    def mock_redis_client(self):
        rc = AsyncMock()
        rc.get_json = AsyncMock(return_value=None)
        rc.set_json = AsyncMock(return_value=True)
        rc.delete = AsyncMock(return_value=True)
        rc.exists = AsyncMock(return_value=False)
        rc.scan_keys = AsyncMock(return_value=[])
        return rc

    @pytest.fixture
    def cache(self, mock_redis_client):
        return ProfileCache(redis=mock_redis_client)

    def test_basic_profile_key_uses_global(self, cache):
        """Basic profile cache key: profile:{user_id}:global"""
        key = cache._profile_key("user123", course_id=None)
        assert key == "profile:user123:global"
        assert "course" not in key.lower()

    def test_course_profile_key_includes_course_id(self, cache):
        """Course-specific key: profile:{user_id}:{course_id}"""
        key = cache._profile_key("user123", course_id=1)
        assert key == "profile:user123:1"

    def test_different_courses_have_different_keys(self, cache):
        """Different course IDs produce different cache keys"""
        key1 = cache._profile_key("user123", course_id=1)
        key2 = cache._profile_key("user123", course_id=2)
        key3 = cache._profile_key("user123", course_id=999)
        assert key1 != key2
        assert key1 != key3
        assert key2 != key3

    def test_different_users_have_different_keys(self, cache):
        """Different user IDs produce different cache keys"""
        key_a = cache._profile_key("userA", course_id=1)
        key_b = cache._profile_key("userB", course_id=1)
        assert key_a != key_b

    @pytest.mark.asyncio
    async def test_set_basic_profile_uses_global_key(self, cache, mock_redis_client):
        """Setting basic profile (no course_id) uses global key"""
        profile_data = {"learning_style": "VISUAL", "grade_level": "BEGINNER"}
        await cache.set_profile("user123", profile_data, course_id=None)

        call_args = mock_redis_client.set_json.call_args
        used_key = call_args[0][0]
        assert used_key == "profile:user123:global"

    @pytest.mark.asyncio
    async def test_set_course_profile_uses_course_key(self, cache, mock_redis_client):
        """Setting profile with course_id uses course-specific key"""
        profile_data = {"course_strengths": ["loops"]}
        await cache.set_profile("user123", profile_data, course_id=5)

        call_args = mock_redis_client.set_json.call_args
        used_key = call_args[0][0]
        assert used_key == "profile:user123:5"

    @pytest.mark.asyncio
    async def test_get_profile_cache_hit(self, cache, mock_redis_client):
        """Getting a cached profile returns it"""
        cached_data = {"learning_style": "AUDITORY", "_cached": True}
        mock_redis_client.get_json.return_value = cached_data

        result = await cache.get_profile("user123", course_id=None)
        assert result == cached_data
        mock_redis_client.get_json.assert_called_once_with("profile:user123:global")

    @pytest.mark.asyncio
    async def test_get_profile_cache_miss(self, cache, mock_redis_client):
        """Getting an uncached profile returns None"""
        mock_redis_client.get_json.return_value = None
        result = await cache.get_profile("user123", course_id=None)
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_profile_deletes_correct_key(self, cache, mock_redis_client):
        """Invalidating a profile deletes the correct key"""
        await cache.invalidate_profile("user123", course_id=3)
        mock_redis_client.delete.assert_called_once_with("profile:user123:3")

    @pytest.mark.asyncio
    async def test_invalidate_user_all_scans_correct_pattern(self, cache, mock_redis_client):
        """Invalidating all profiles for a user scans user:* pattern"""
        mock_redis_client.scan_keys.return_value = [
            "profile:user123:global",
            "profile:user123:1",
            "profile:user123:2",
        ]
        count = await cache.invalidate_user_all("user123")
        assert count == 3
        assert mock_redis_client.delete.call_count == 3

    @pytest.mark.asyncio
    async def test_set_profile_adds_meta_fields(self, cache, mock_redis_client):
        """Setting a profile automatically adds _cached, _user_id, _course_id"""
        profile_data = {"learning_style": "KINESTHETIC"}
        await cache.set_profile("user456", profile_data, course_id=10)

        call_args = mock_redis_client.set_json.call_args
        stored_value = call_args[0][1]
        assert stored_value["_cached"] == True
        assert stored_value["_user_id"] == "user456"
        assert stored_value["_course_id"] == 10
        assert stored_value["learning_style"] == "KINESTHETIC"

    @pytest.mark.asyncio
    async def test_set_profile_with_default_ttl(self, cache, mock_redis_client):
        """Profile cache uses 24-hour TTL by default"""
        await cache.set_profile("user123", {"test": True}, course_id=None)
        call_args = mock_redis_client.set_json.call_args
        ttl = call_args[1]["ttl"]
        assert ttl == PROFILE_TTL
        assert ttl == 24 * 3600


# ==================== 4. Edge Cases & Boundary Tests ====================


class TestProfileEdgeCases:
    """Edge cases for profile system"""

    @pytest.fixture
    def agent(self, mock_llm):
        return ProfileAgent(llm=mock_llm)

    @pytest.mark.asyncio
    async def test_execute_invalid_task_type(self, agent):
        """ProfileAgent raises ValueError for unknown task type"""
        with pytest.raises(ValueError, match="ProfileAgent"):
            await agent.execute("unknown_task")

    @pytest.mark.asyncio
    async def test_execute_analyze_basic(self, agent, mock_llm):
        """execute('analyze_basic') delegates correctly"""
        mock_llm.chat.return_value = json.dumps({
            "learning_style": "VISUAL",
            "grade_level": "BEGINNER",
            "interests": [],
            "strengths": [],
            "weaknesses": [],
            "recommended_methods": [],
            "recommended_strategy": "test",
            "study_pace": "MODERATE",
            "confidence": 0.5
        })
        result = await agent.execute(
            "analyze_basic",
            questionnaire_data={"education_level": "BACHELOR"},
        )
        assert "learning_style" in result

    @pytest.mark.asyncio
    async def test_execute_analyze_course(self, agent, mock_llm):
        """execute('analyze_course') delegates correctly"""
        mock_llm.chat.return_value = json.dumps({
            "course_strengths": ["loops"],
            "course_weaknesses": [],
            "topics_discussed": ["loops"],
            "engagement_level": "HIGH",
        })
        result = await agent.execute(
            "analyze_course",
            basic_profile={"learning_style": "VISUAL"},
            chat_history=[{"role": "user", "content": "test"}],
        )
        assert "course_strengths" in result

    @pytest.mark.asyncio
    async def test_basic_profile_with_partial_questionnaire(self, agent, mock_llm):
        """Basic profile with only some questionnaire fields filled"""
        mock_llm.chat.return_value = json.dumps({
            "learning_style": "READING",
            "grade_level": "BEGINNER",
            "interests": [],
            "strengths": [],
            "weaknesses": [],
            "recommended_methods": ["VIDEO"],
            "recommended_strategy": "Start with video tutorials",
            "study_pace": "SLOW",
            "confidence": 0.4
        })
        q_data = {
            "education_level": "BACHELOR",
            "learning_methods": ["VIDEO"],
        }
        result = await agent.analyze_basic_profile(questionnaire_data=q_data)
        assert "learning_style" in result
        assert result["learning_style"] == "READING"
        assert result["recommended_methods"] == ["VIDEO"]

    @pytest.mark.asyncio
    async def test_course_profile_with_long_chat_history(self, agent, mock_llm):
        """Course profile handles chat history truncation (last 30 messages)"""
        mock_llm.chat.return_value = json.dumps({
            "course_strengths": [],
            "course_weaknesses": [],
            "topics_discussed": [],
            "engagement_level": "MEDIUM",
        })
        # 50 messages - only last 30 should be used
        long_history = [
            {"role": "user" if i % 2 == 0 else "assistant",
             "content": f"Message {i}"}
            for i in range(50)
        ]
        result = await agent.analyze_course_profile(
            basic_profile={"learning_style": "VISUAL"},
            chat_history=long_history,
        )
        # Should not crash
        assert "course_strengths" in result

    @pytest.mark.asyncio
    async def test_course_profile_llm_failure_fallback(self, agent, mock_llm):
        """Course profile with invalid LLM JSON response uses fallback"""
        mock_llm.chat.return_value = "garbage response{{{{"
        result = await agent.analyze_course_profile(
            basic_profile={"learning_style": "VISUAL"},
            chat_history=[{"role": "user", "content": "test"}],
        )
        assert result["course_strengths"] == []
        assert result["course_weaknesses"] == []
        assert "raw_response" in result

    @pytest.mark.asyncio
    async def test_full_pipeline_basic_then_course(self, agent, mock_llm):
        """Full pipeline: basic profile -> course profile"""
        # Step 1: Generate basic profile
        mock_llm.chat.return_value = json.dumps({
            "learning_style": "READING",
            "grade_level": "BEGINNER",
            "interests": ["web dev"],
            "strengths": ["HTML"],
            "weaknesses": ["JS"],
            "recommended_methods": ["READING"],
            "recommended_strategy": "Read docs first",
            "study_pace": "SLOW",
            "confidence": 0.6
        })
        basic = await agent.analyze_basic_profile(questionnaire_data={
            "education_level": "BACHELOR",
            "major_direction": "CS",
        })

        # Step 2: Use basic profile to build course profile
        mock_llm.chat.return_value = json.dumps({
            "course_strengths": ["HTML tags"],
            "course_weaknesses": ["JS closures"],
            "topics_discussed": ["HTML", "CSS", "JS"],
            "engagement_level": "HIGH",
        })
        course = await agent.analyze_course_profile(
            basic_profile=basic,
            chat_history=[
                {"role": "user", "content": "What are JS closures?"},
            ],
        )

        assert course["course_weaknesses"] == ["JS closures"]


# ==================== 5. parse_llm_json Utility ====================


class TestParseLLMJson:
    """Test JSON parsing from LLM responses"""

    def test_parse_plain_json(self):
        result = parse_llm_json('{"key": "value"}', fallback={"default": True})
        assert result == {"key": "value"}

    def test_parse_json_with_code_fence(self):
        response = '```json\n{"key": "value"}\n```'
        result = parse_llm_json(response)
        assert result == {"key": "value"}

    def test_parse_json_with_generic_fence(self):
        response = '```\n{"key": "value"}\n```'
        result = parse_llm_json(response)
        assert result == {"key": "value"}

    def test_parse_invalid_json_uses_fallback(self):
        result = parse_llm_json('not json', fallback={"default": True})
        assert result["default"] == True
        assert result["raw_response"] == 'not json'

    def test_parse_empty_string(self):
        result = parse_llm_json('', fallback={"empty": True})
        assert result["empty"] == True
        assert "raw_response" in result

    def test_parse_json_with_whitespace(self):
        result = parse_llm_json('  \n  {"key": 123}  \n  ')
        assert result == {"key": 123}


# ==================== 6. Integration: Two-Tier Architecture Contract ====================


class TestTwoTierContract:
    """
    Integration tests verifying the two-tier architecture contract:

    Tier 1 (Basic Profile):
      - One per USER (not per course)
      - Generated once from questionnaire
      - Persisted to MySQL + cached in Redis (profile:{user_id}:global)
      - Shared across all courses the user is enrolled in

    Tier 2 (Course Profile):
      - One per COURSE per USER
      - Generated on-demand from: basic_profile + chat_history + study_records
      - NOT persisted (dynamic, regenerated each time)
      - Independent between courses (Python profile != Java profile)
    """

    @pytest.fixture
    def agent(self, mock_llm):
        return ProfileAgent(llm=mock_llm)

    @pytest.fixture
    def mock_redis_client(self):
        rc = AsyncMock()
        rc.get_json = AsyncMock(return_value=None)
        rc.set_json = AsyncMock(return_value=True)
        rc.delete = AsyncMock(return_value=True)
        rc.exists = AsyncMock(return_value=False)
        rc.scan_keys = AsyncMock(return_value=[])
        return rc

    @pytest.mark.asyncio
    async def test_full_scenario_multi_course(self, agent, mock_llm):
        """
        Full scenario:
        1. User fills questionnaire -> basic profile generated (once)
        2. User chats in Python course -> course profile A generated
        3. User chats in Java course -> course profile B generated
        4. A and B are different, but share same basic_profile
        """
        # Step 1: Generate basic profile
        mock_llm.chat.return_value = json.dumps({
            "learning_style": "VISUAL",
            "grade_level": "INTERMEDIATE",
            "interests": ["Python", "Java", "AI"],
            "strengths": ["comprehension", "logic"],
            "weaknesses": ["algorithm", "memory"],
            "recommended_methods": ["VIDEO", "QUIZ"],
            "recommended_strategy": "Visual learning with practice quizzes",
            "study_pace": "MODERATE",
            "confidence": 0.75
        })
        basic_profile = await agent.analyze_basic_profile(questionnaire_data={
            "education_level": "BACHELOR",
            "major_direction": "CS",
            "learning_goals": ["EMPLOYMENT"],
            "learning_methods": ["VIDEO"],
            "self_strengths": ["COMPREHENSION"],
            "self_weaknesses": ["MEMORY"],
        })
        assert basic_profile["learning_style"] == "VISUAL"

        # Step 2: Python course chat -> course profile
        mock_llm.chat.return_value = json.dumps({
            "course_strengths": ["list comprehensions"],
            "course_weaknesses": ["recursion", "decorators"],
            "topics_discussed": ["lists", "dicts", "recursion", "decorators"],
            "engagement_level": "HIGH",
            "questions_frequency": "FREQUENT",
            "summary": "Good at basics, needs work on advanced Python features"
        })
        python_profile = await agent.analyze_course_profile(
            basic_profile=basic_profile,
            chat_history=[
                {"role": "user", "content": "How do list comprehensions work?"},
                {"role": "assistant", "content": "List comprehensions are..."},
                {"role": "user", "content": "Why is recursion so hard?"},
                {"role": "assistant", "content": "Recursion is..."},
                {"role": "user", "content": "What are decorators?"},
            ],
        )

        # Step 3: Java course chat -> different course profile
        mock_llm.chat.return_value = json.dumps({
            "course_strengths": ["OOP basics", "interfaces"],
            "course_weaknesses": ["generics", "streams"],
            "topics_discussed": ["classes", "interfaces", "generics"],
            "engagement_level": "MEDIUM",
            "questions_frequency": "MODERATE",
            "summary": "Understands OOP well, working on advanced Java features"
        })
        java_profile = await agent.analyze_course_profile(
            basic_profile=basic_profile,
            chat_history=[
                {"role": "user", "content": "What is an interface?"},
                {"role": "assistant", "content": "An interface defines..."},
                {"role": "user", "content": "How do generics work?"},
            ],
        )

        # Step 4: Verify independence
        # Same basic_profile used for both
        # But course profiles are different
        assert python_profile["course_strengths"] != java_profile["course_strengths"]
        assert python_profile["course_weaknesses"] != java_profile["course_weaknesses"]
        assert python_profile["topics_discussed"] != java_profile["topics_discussed"]
        assert python_profile["engagement_level"] != java_profile["engagement_level"]

        # Verify LLM was called 3 times (basic + 2 course profiles)
        assert mock_llm.chat.call_count == 3

    @pytest.mark.asyncio
    async def test_cache_isolation(self, mock_redis_client):
        """
        Verify the caching strategy:
        - Basic profile: cached at profile:{user_id}:global
        - Course profiles: NOT cached by ProfileAgent.analyze_course_profile
          (orchestrator does NOT call cache.set for course profiles)
        """
        cache = ProfileCache(redis=mock_redis_client)

        # Basic profile: stored at global key
        basic_data = {"learning_style": "VISUAL"}
        await cache.set_profile("user123", basic_data, course_id=None)
        basic_key = mock_redis_client.set_json.call_args[0][0]
        assert basic_key == "profile:user123:global"

        # Course profiles stored at course-specific keys
        mock_redis_client.set_json.reset_mock()
        course_data = {"course_strengths": ["OOP"]}
        await cache.set_profile("user123", course_data, course_id=1)
        course_key = mock_redis_client.set_json.call_args[0][0]
        assert course_key == "profile:user123:1"

        # Different course -> different key
        mock_redis_client.set_json.reset_mock()
        await cache.set_profile("user123", course_data, course_id=2)
        course_key_2 = mock_redis_client.set_json.call_args[0][0]
        assert course_key_2 == "profile:user123:2"
        assert course_key != course_key_2

    @pytest.mark.asyncio
    async def test_profile_agent_name_and_description(self, agent):
        """Verify agent identity"""
        assert agent.name == "profile_agent"
        info = agent.get_info()
        assert info["name"] == "profile_agent"


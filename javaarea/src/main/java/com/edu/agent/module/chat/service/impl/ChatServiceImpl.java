package com.edu.agent.module.chat.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.chat.dto.ChatRequest;
import com.edu.agent.module.chat.dto.ChatResponse;
import com.edu.agent.module.chat.dto.ChatSessionDTO;
import com.edu.agent.module.chat.entity.ChatMessage;
import com.edu.agent.module.chat.entity.ChatSession;
import com.edu.agent.module.chat.mapper.ChatMessageMapper;
import com.edu.agent.module.chat.mapper.ChatSessionMapper;
import com.edu.agent.module.chat.service.ChatService;
import com.edu.agent.module.chat.service.client.AgentServiceClient;
import com.edu.agent.module.course.entity.Course;
import com.edu.agent.module.course.mapper.CourseMapper;
import com.edu.agent.module.knowledge.entity.KnowledgeBase;
import com.edu.agent.module.knowledge.mapper.KnowledgeMapper;
import com.edu.agent.module.learning.entity.StudentProfile;
import com.edu.agent.module.learning.dto.QuestionnaireDTO;
import com.edu.agent.module.learning.service.StudentProfileService;
import com.edu.agent.module.learning.service.StudentProfileQuestionnaireService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class ChatServiceImpl extends ServiceImpl<ChatSessionMapper, ChatSession> implements ChatService {

    private final AgentServiceClient agentServiceClient;
    private final ChatMessageMapper messageMapper;
    private final KnowledgeMapper knowledgeMapper;
    private final CourseMapper courseMapper;
    private final StudentProfileService studentProfileService;
    private final StudentProfileQuestionnaireService questionnaireService;
    private final ExecutorService streamExecutor = Executors.newCachedThreadPool();

    @Override
    @Transactional
    public ChatSessionDTO createSession(Long userId, Long courseId) {
        ChatSession session = new ChatSession();
        session.setUserId(userId);
        session.setCourseId(courseId);
        session.setTitle("新对话");
        save(session);

        log.info("会话创建成功: id={}, userId={}", session.getId(), userId);
        return toSessionDTO(session, null, Collections.emptyMap());
    }

    @Override
    public List<ChatSessionDTO> listSessions(Long userId) {
        LambdaQueryWrapper<ChatSession> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(ChatSession::getUserId, userId)
                .orderByDesc(ChatSession::getUpdateTime);
        List<ChatSession> sessions = list(wrapper);

        if (sessions.isEmpty()) {
            return Collections.emptyList();
        }

        // Batch fetch last messages
        List<Long> sessionIds = sessions.stream()
                .map(ChatSession::getId)
                .collect(Collectors.toList());
        LambdaQueryWrapper<ChatMessage> msgWrapper = new LambdaQueryWrapper<>();
        msgWrapper.in(ChatMessage::getSessionId, sessionIds)
                .orderByDesc(ChatMessage::getCreateTime);
        List<ChatMessage> allMessages = messageMapper.selectList(msgWrapper);

        Map<Long, ChatMessage> lastMessageMap = new HashMap<>();
        for (ChatMessage msg : allMessages) {
            lastMessageMap.putIfAbsent(msg.getSessionId(), msg);
        }

        // Batch fetch courses to avoid N+1 queries
        Set<Long> courseIds = sessions.stream()
                .map(ChatSession::getCourseId)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());
        Map<Long, Course> courseMap = new HashMap<>();
        if (!courseIds.isEmpty()) {
            courseMapper.selectBatchIds(courseIds).forEach(c -> courseMap.put(c.getId(), c));
        }

        return sessions.stream()
                .map(session -> toSessionDTO(session, lastMessageMap.get(session.getId()), courseMap))
                .collect(Collectors.toList());
    }

    @Override
    public IPage<ChatMessage> getSessionMessages(Long sessionId, int page, int size) {
        ChatSession session = getById(sessionId);
        if (session == null) {
            throw new BizException(ResultCode.NOT_FOUND, "会话不存在");
        }

        LambdaQueryWrapper<ChatMessage> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(ChatMessage::getSessionId, sessionId)
                .orderByAsc(ChatMessage::getCreateTime);

        Page<ChatMessage> pageParam = new Page<>(page, size);
        return messageMapper.selectPage(pageParam, wrapper);
    }

    @Override
    @Transactional
    public ChatResponse sendMessage(Long sessionId, Long userId, ChatRequest request) {
        ChatSession session = getById(sessionId);
        if (session == null) {
            throw new BizException(ResultCode.NOT_FOUND, "会话不存在");
        }
        if (!session.getUserId().equals(userId)) {
            throw new BizException(ResultCode.FORBIDDEN, "无权访问此会话");
        }

        // Save user message
        ChatMessage userMessage = new ChatMessage();
        userMessage.setSessionId(sessionId);
        userMessage.setRole("USER");
        userMessage.setContent(request.getMessage());
        messageMapper.insert(userMessage);

        // Build context
        Map<String, Object> context = buildContext(session);

        // Call agent service
        String agentResponse;
        try {
            agentResponse = agentServiceClient.chatWithContext(request.getMessage(), context);
        } catch (Exception e) {
            log.error("调用 Agent 服务失败", e);
            agentResponse = "抱歉，AI 服务暂时不可用，请稍后再试。";
        }

        // Save assistant message
        ChatMessage assistantMessage = new ChatMessage();
        assistantMessage.setSessionId(sessionId);
        assistantMessage.setRole("ASSISTANT");
        assistantMessage.setContent(agentResponse);
        messageMapper.insert(assistantMessage);

        // Update session title if first message
        if ("新对话".equals(session.getTitle())) {
            String title = request.getMessage().length() > 50
                    ? request.getMessage().substring(0, 50) + "..."
                    : request.getMessage();
            session.setTitle(title);
            updateById(session);
        }

        ChatResponse response = new ChatResponse();
        response.setResponse(agentResponse);
        response.setSessionId(sessionId);
        response.setMessageId(assistantMessage.getId());
        response.setAgentId("orchestrator");
        return response;
    }

    @Override
    public SseEmitter sendMessageStream(Long sessionId, Long userId, ChatRequest request) {
        ChatSession session = getById(sessionId);
        if (session == null) {
            throw new BizException(ResultCode.NOT_FOUND, "会话不存在");
        }
        if (!session.getUserId().equals(userId)) {
            throw new BizException(ResultCode.FORBIDDEN, "无权访问此会话");
        }

        // Save user message synchronously
        ChatMessage userMessage = new ChatMessage();
        userMessage.setSessionId(sessionId);
        userMessage.setRole("USER");
        userMessage.setContent(request.getMessage());
        messageMapper.insert(userMessage);

        // Build context
        Map<String, Object> context = buildContext(session);

        // Update session title if first message
        if ("新对话".equals(session.getTitle())) {
            String title = request.getMessage().length() > 50
                    ? request.getMessage().substring(0, 50) + "..."
                    : request.getMessage();
            session.setTitle(title);
            updateById(session);
        }

        SseEmitter emitter = new SseEmitter(120_000L); // 2 min timeout
        StringBuilder accumulator = new StringBuilder();
        AtomicBoolean responseSaved = new AtomicBoolean(false);

        // Capture SecurityContext on request thread for async propagation
        SecurityContext secCtx = SecurityContextHolder.getContext();

        streamExecutor.submit(() -> {
            // Restore SecurityContext on worker thread
            SecurityContextHolder.setContext(secCtx);
            try {
                agentServiceClient.streamChatWithContext(request.getMessage(), context, emitter, accumulator);
            } catch (Exception e) {
                log.error("流式对话失败", e);
                try {
                    emitter.send(SseEmitter.event().data("{\"error\":\"AI 服务暂时不可用\"}"));
                    emitter.complete();
                } catch (Exception ignored) {}
            } finally {
                // Persist response to DB (full or partial)
                saveAssistantMessage(sessionId, accumulator, responseSaved);
                SecurityContextHolder.clearContext();
            }
        });

        emitter.onTimeout(() -> {
            log.warn("SSE 超时: sessionId={}", sessionId);
            saveAssistantMessage(sessionId, accumulator, responseSaved);
        });
        emitter.onError(e -> {
            log.warn("SSE 错误/客户端断开: sessionId={}", sessionId, e);
            saveAssistantMessage(sessionId, accumulator, responseSaved);
        });

        return emitter;
    }

    private Map<String, Object> buildContext(ChatSession session) {
        Map<String, Object> context = new HashMap<>();

        // Knowledge context
        if (session.getCourseId() != null) {
            LambdaQueryWrapper<KnowledgeBase> kbWrapper = new LambdaQueryWrapper<>();
            kbWrapper.eq(KnowledgeBase::getCourseId, session.getCourseId())
                    .eq(KnowledgeBase::getStatus, 1);
            List<KnowledgeBase> knowledgeList = knowledgeMapper.selectList(kbWrapper);
            List<Long> knowledgeIds = knowledgeList.stream()
                    .map(KnowledgeBase::getId)
                    .collect(Collectors.toList());
            if (!knowledgeIds.isEmpty()) {
                context.put("knowledge_ids", knowledgeIds);
            }
        }

        // Student profile context
        Long userId = session.getUserId();
        if (userId != null) {
            Map<String, Object> profileData = new HashMap<>();

            // Basic student profile (learning style, strengths, weaknesses, interests)
            try {
                StudentProfile profile = studentProfileService.getProfile(userId);
                if (profile != null) {
                    if (profile.getLearningStyle() != null) {
                        profileData.put("learning_style", profile.getLearningStyle());
                    }
                    if (profile.getStrengths() != null) {
                        profileData.put("strengths", profile.getStrengths());
                    }
                    if (profile.getWeaknesses() != null) {
                        profileData.put("weaknesses", profile.getWeaknesses());
                    }
                    if (profile.getInterests() != null) {
                        profileData.put("interests", profile.getInterests());
                    }
                }
            } catch (Exception e) {
                log.debug("获取学生画像失败: userId={}", userId, e);
            }

            // Questionnaire data (7 dimensions)
            try {
                QuestionnaireDTO questionnaire = questionnaireService.getQuestionnaire(userId);
                if (questionnaire != null && Boolean.TRUE.equals(questionnaire.getIsCompleted())) {
                    Map<String, Object> qData = new HashMap<>();
                    if (questionnaire.getEducationLevel() != null) qData.put("education_level", questionnaire.getEducationLevel());
                    if (questionnaire.getMajorDirection() != null) qData.put("major_direction", questionnaire.getMajorDirection());
                    if (questionnaire.getAgeRange() != null) qData.put("age_range", questionnaire.getAgeRange());
                    if (questionnaire.getLearningGoals() != null) qData.put("learning_goals", questionnaire.getLearningGoals());
                    if (questionnaire.getGoalClarity() != null) qData.put("goal_clarity", questionnaire.getGoalClarity());
                    if (questionnaire.getMotivationLevel() != null) qData.put("motivation_level", questionnaire.getMotivationLevel());
                    if (questionnaire.getSubjectLevel() != null) qData.put("subject_level", questionnaire.getSubjectLevel());
                    if (questionnaire.getSelfStrengths() != null) qData.put("self_strengths", questionnaire.getSelfStrengths());
                    if (questionnaire.getSelfWeaknesses() != null) qData.put("self_weaknesses", questionnaire.getSelfWeaknesses());
                    if (questionnaire.getLearningMethods() != null) qData.put("learning_methods", questionnaire.getLearningMethods());
                    if (questionnaire.getStudyTimeSlots() != null) qData.put("study_time_slots", questionnaire.getStudyTimeSlots());
                    if (questionnaire.getSessionDuration() != null) qData.put("session_duration", questionnaire.getSessionDuration());
                    if (questionnaire.getPlanningHabit() != null) qData.put("planning_habit", questionnaire.getPlanningHabit());
                    if (questionnaire.getFocusLevel() != null) qData.put("focus_level", questionnaire.getFocusLevel());
                    if (questionnaire.getReviewHabit() != null) qData.put("review_habit", questionnaire.getReviewHabit());
                    if (questionnaire.getDailyStudyHours() != null) qData.put("daily_study_hours", questionnaire.getDailyStudyHours());
                    if (questionnaire.getDevices() != null) qData.put("devices", questionnaire.getDevices());
                    if (questionnaire.getHasMentor() != null) qData.put("has_mentor", questionnaire.getHasMentor());
                    if (questionnaire.getHasPastFailures() != null) qData.put("has_past_failures", questionnaire.getHasPastFailures());
                    if (questionnaire.getMainBarriers() != null) qData.put("main_barriers", questionnaire.getMainBarriers());
                    if (questionnaire.getConfidenceLevel() != null) qData.put("confidence_level", questionnaire.getConfidenceLevel());
                    profileData.put("questionnaire", qData);
                    log.debug("问卷画像已注入: userId={}", userId);
                }
            } catch (Exception e) {
                log.debug("获取问卷数据失败: userId={}", userId, e);
            }

            if (!profileData.isEmpty()) {
                context.put("student_profile", profileData);
                log.info("学生画像已注入对话上下文: userId={}, fields={}", userId, profileData.size());
            }
        }

        return context;
    }

    @Override
    @Transactional
    public void deleteSession(Long sessionId, Long userId) {
        ChatSession session = getById(sessionId);
        if (session == null) {
            throw new BizException(ResultCode.NOT_FOUND, "会话不存在");
        }
        if (!session.getUserId().equals(userId)) {
            throw new BizException(ResultCode.FORBIDDEN, "无权删除此会话");
        }

        // Delete messages
        LambdaQueryWrapper<ChatMessage> msgWrapper = new LambdaQueryWrapper<>();
        msgWrapper.eq(ChatMessage::getSessionId, sessionId);
        messageMapper.delete(msgWrapper);

        // Delete session
        removeById(sessionId);
        log.info("会话删除成功: id={}", sessionId);
    }

    private void saveAssistantMessage(Long sessionId, StringBuilder accumulator, AtomicBoolean saved) {
        String content = accumulator.toString().trim();
        if (content.isEmpty() || !saved.compareAndSet(false, true)) {
            return; // empty or already saved
        }
        try {
            ChatMessage msg = new ChatMessage();
            msg.setSessionId(sessionId);
            msg.setRole("ASSISTANT");
            msg.setContent(content);
            messageMapper.insert(msg);
            log.info("流式回复已保存: sessionId={}, length={}", sessionId, content.length());
        } catch (Exception e) {
            log.error("保存流式回复失败: sessionId={}", sessionId, e);
        }
    }

    private ChatSessionDTO toSessionDTO(ChatSession session, ChatMessage lastMessage,
                                         Map<Long, Course> courseMap) {
        ChatSessionDTO dto = new ChatSessionDTO();
        dto.setId(session.getId());
        dto.setCourseId(session.getCourseId());
        dto.setTitle(session.getTitle());
        dto.setCreateTime(session.getCreateTime());
        if (session.getCourseId() != null && courseMap != null) {
            Course course = courseMap.get(session.getCourseId());
            if (course != null) {
                dto.setCourseName(course.getTitle());
            }
        }
        if (lastMessage != null) {
            dto.setLastMessage(lastMessage.getContent());
            dto.setLastMessageTime(lastMessage.getCreateTime());
        }
        return dto;
    }
}
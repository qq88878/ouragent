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
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.*;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.stream.Collectors;

@Service
public class ChatServiceImpl extends ServiceImpl<ChatSessionMapper, ChatSession> implements ChatService {
    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(ChatServiceImpl.class);

    private final AgentServiceClient agentServiceClient;
    private final ChatMessageMapper messageMapper;
    private final KnowledgeMapper knowledgeMapper;
    private final CourseMapper courseMapper;
    private final StudentProfileService studentProfileService;
    private final StudentProfileQuestionnaireService questionnaireService;
    private final TransactionTemplate transactionTemplate;
    private final ExecutorService streamExecutor = Executors.newCachedThreadPool();
    public ChatServiceImpl(AgentServiceClient agentServiceClient, ChatMessageMapper messageMapper, KnowledgeMapper knowledgeMapper, CourseMapper courseMapper, StudentProfileService studentProfileService, StudentProfileQuestionnaireService questionnaireService, TransactionTemplate transactionTemplate) {
        this.agentServiceClient = agentServiceClient;
        this.messageMapper = messageMapper;
        this.knowledgeMapper = knowledgeMapper;
        this.courseMapper = courseMapper;
        this.studentProfileService = studentProfileService;
        this.questionnaireService = questionnaireService;
        this.transactionTemplate = transactionTemplate;
    }

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
        context.put("user_id", String.valueOf(userId));

        // Call agent service
        String agentResponse;
        try {
            agentResponse = agentServiceClient.chatWithContext(request.getMessage(), context, sessionId);
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

        // 对话中自动检测问答，记录错题
        tryAutoRecordMistake(sessionId, String.valueOf(userId), request.getMessage());

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
        context.put("user_id", String.valueOf(userId));

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

        // Capture SecurityContext on request thread for async propagation
        SecurityContext secCtx = SecurityContextHolder.getContext();

        streamExecutor.submit(() -> {
            // Restore SecurityContext on worker thread
            SecurityContextHolder.setContext(secCtx);
            try {
                agentServiceClient.streamChatWithContext(request.getMessage(), context, sessionId, emitter, accumulator);
            } catch (Exception e) {
                log.error("流式对话失败", e);
                try {
                    emitter.send(SseEmitter.event().data("{\"error\":\"AI 服务暂时不可用\"}"));
                    emitter.complete();
                } catch (Exception ignored) {}
            } finally {
                // Persist full response to DB within a transaction
                final String fullResponse = accumulator.toString();
                final Long sid = sessionId;
                if (!fullResponse.isEmpty()) {
                    ChatMessage assistantMessage = new ChatMessage();
                    assistantMessage.setSessionId(sessionId);
                    assistantMessage.setRole("ASSISTANT");
                    assistantMessage.setContent(fullResponse);
                    messageMapper.insert(assistantMessage);
                    // 对话中自动记录错题
                    tryAutoRecordMistake(sessionId, String.valueOf(userId), request.getMessage());
                }
                SecurityContextHolder.clearContext();
            }
        });

        emitter.onTimeout(() -> log.warn("SSE 超时: sessionId={}", sessionId));
        emitter.onError(e -> log.warn("SSE 错误: sessionId={}", sessionId, e));

        return emitter;
    }

    @Override
    public SseEmitter sendQAStream(Long sessionId, Long userId, ChatRequest request) {
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

        // Build context (same as normal chat)
        Map<String, Object> context = buildContext(session);
        context.put("user_id", String.valueOf(userId));

        // Update session title if first message
        if ("新对话".equals(session.getTitle())) {
            String title = request.getMessage().length() > 50
                    ? request.getMessage().substring(0, 50) + "..."
                    : request.getMessage();
            session.setTitle(title);
            updateById(session);
        }

        SseEmitter emitter = new SseEmitter(120_000L);
        StringBuilder accumulator = new StringBuilder();
        SecurityContext secCtx = SecurityContextHolder.getContext();

        streamExecutor.submit(() -> {
            SecurityContextHolder.setContext(secCtx);
            try {
                agentServiceClient.streamQAWithCheck(request.getMessage(), context, sessionId, emitter, accumulator);
            } catch (Exception e) {
                log.error("深度答疑流式对话失败", e);
                try {
                    emitter.send(SseEmitter.event().data("{\"type\":\"error\",\"error\":\"AI 服务暂时不可用\"}"));
                    emitter.complete();
                } catch (Exception ignored) {}
            } finally {
                String fullResponse = accumulator.toString();
                if (!fullResponse.isEmpty()) {
                    ChatMessage assistantMessage = new ChatMessage();
                    assistantMessage.setSessionId(sessionId);
                    assistantMessage.setRole("ASSISTANT");
                    assistantMessage.setContent(fullResponse);
                    messageMapper.insert(assistantMessage);
                }
                SecurityContextHolder.clearContext();
            }
        });

        emitter.onTimeout(() -> log.warn("QA SSE 超时: sessionId={}", sessionId));
        emitter.onError(e -> log.warn("QA SSE 错误: sessionId={}", sessionId, e));

        return emitter;
    }

    private Map<String, Object> buildContext(ChatSession session) {
        Map<String, Object> context = new HashMap<>();

        // User ID for mistake book auto-recording
        if (session.getUserId() != null) {
            context.put("user_id", String.valueOf(session.getUserId()));
        }

        // Knowledge context
        if (session.getCourseId() != null) {
            // 固定课程模式：只检索该课程的知识库
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

            // Tell the agent which course this chat is about
            Course course = courseMapper.selectById(session.getCourseId());
            if (course != null) {
                context.put("course_id", session.getCourseId());
                context.put("course_title", course.getTitle());
            }
        } else {
            // 动态课程模式：传所有课程及知识库，让 AI 自主选择
            List<Course> allCourses = courseMapper.selectList(null);
            if (allCourses != null && !allCourses.isEmpty()) {
                Map<Long, List<Long>> courseKnowledgeMap = new HashMap<>();
                List<Long> allKnowledgeIds = new ArrayList<>();
                for (Course c : allCourses) {
                    LambdaQueryWrapper<KnowledgeBase> kbWrapper = new LambdaQueryWrapper<>();
                    kbWrapper.eq(KnowledgeBase::getCourseId, c.getId())
                            .eq(KnowledgeBase::getStatus, 1);
                    List<Long> kbIds = knowledgeMapper.selectList(kbWrapper)
                            .stream().map(KnowledgeBase::getId).collect(Collectors.toList());
                    if (!kbIds.isEmpty()) {
                        courseKnowledgeMap.put(c.getId(), kbIds);
                        allKnowledgeIds.addAll(kbIds);
                    }
                }
                if (!allKnowledgeIds.isEmpty()) {
                    context.put("knowledge_ids", allKnowledgeIds);
                }
                // 课程目录：让 AI 知道有哪些课程可选
                List<Map<String, Object>> courseCatalog = new ArrayList<>();
                for (Course c : allCourses) {
                    Map<String, Object> item = new HashMap<>();
                    item.put("id", c.getId());
                    item.put("title", c.getTitle());
                    if (courseKnowledgeMap.containsKey(c.getId())) {
                        item.put("knowledge_ids", courseKnowledgeMap.get(c.getId()));
                    }
                    courseCatalog.add(item);
                }
                context.put("course_catalog", courseCatalog);
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

            // Questionnaire data (6 core fields)
            try {
                QuestionnaireDTO questionnaire = questionnaireService.getQuestionnaire(userId);
                if (questionnaire != null && Boolean.TRUE.equals(questionnaire.getIsCompleted())) {
                    Map<String, Object> qData = new HashMap<>();
                    if (questionnaire.getEducationLevel() != null) qData.put("education_level", questionnaire.getEducationLevel());
                    if (questionnaire.getMajorDirection() != null) qData.put("major_direction", questionnaire.getMajorDirection());
                    if (questionnaire.getLearningGoals() != null) qData.put("learning_goals", questionnaire.getLearningGoals());
                    if (questionnaire.getLearningMethods() != null) qData.put("learning_methods", questionnaire.getLearningMethods());
                    if (questionnaire.getSelfStrengths() != null) qData.put("self_strengths", questionnaire.getSelfStrengths());
                    if (questionnaire.getSelfWeaknesses() != null) qData.put("self_weaknesses", questionnaire.getSelfWeaknesses());
                    profileData.put("questionnaire", qData);
                    log.debug("问卷数据已注入: userId={}", userId);
                }
            } catch (Exception e) {
                log.debug("获取问卷数据失败: userId={}", userId, e);
            }
            if (!profileData.isEmpty()) {
                context.put("basic_profile", profileData);
                log.info("基础画像已注入对话上下文: userId={}, fields={}", userId, profileData.size());
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

    @Override
    public Map<String, Object> getChatSignals(Long sessionId) {
        return agentServiceClient.getChatSignals(String.valueOf(sessionId));
    }

    /**
     * Format period indexes into readable string, e.g., [0,1] -> "?1-2?"
     */

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

    /**
     * 对话中自动检测问答并记录错题
     * 如果上一条 AI 消息是提问（以?或？结尾），
     * 则将当前用户回答自动记录到错题本
     */
        private void tryAutoRecordMistake(Long sessionId, String userId, String userMessage) {
        try {
            LambdaQueryWrapper<ChatMessage> wrapper = new LambdaQueryWrapper<>();
            wrapper.eq(ChatMessage::getSessionId, sessionId)
                   .orderByDesc(ChatMessage::getCreateTime)
                   .last("LIMIT 4");
            List<ChatMessage> recentMessages = messageMapper.selectList(wrapper);

            if (recentMessages.size() < 2) return;

            // recentMessages[0] = ?? assistant (????)
            // recentMessages[1] = ?????
            // recentMessages[2] = ??? AI (?????)
            ChatMessage lastAiMsg = null;
            ChatMessage prevAiMsg = null;
            int aiCount = 0;
            for (ChatMessage msg : recentMessages) {
                if ("ASSISTANT".equals(msg.getRole())) {
                    aiCount++;
                    if (aiCount == 1) lastAiMsg = msg;
                    else if (aiCount == 2) { prevAiMsg = msg; break; }
                }
            }

            if (lastAiMsg == null) return;

            String lastContent = lastAiMsg.getContent();
            if (lastContent == null) return;
            lastContent = lastContent.trim();

            // ??1??? AI ??????300?? ? / ?
            boolean isQuestion = lastContent.endsWith("?") || lastContent.endsWith("？");
            if (!isQuestion) {
                String tail = lastContent.length() > 300 
                    ? lastContent.substring(lastContent.length() - 300) 
                    : lastContent;
                isQuestion = tail.contains("?") || tail.contains("？");
            }
            // 收紧提问判断：AI消息必须包含教育场景关键词（计算、题目、练习等）
            if (isQuestion) {
                String lowLast = lastContent.toLowerCase();
                boolean isEdu = lowLast.contains("计算") || lowLast.contains("题目") 
                    || lowLast.contains("练习") || lowLast.contains("答案")
                    || lowLast.contains("等于") || lowLast.contains("calculate")
                    || lowLast.contains("question") || lowLast.contains("problem")
                    || lowLast.contains("solve") || lowLast.contains("exercise")
                    || lowLast.contains("判断") || lowLast.contains("填空")
                    || lowLast.contains("选择") || lowLast.contains("简答")
                    || lowLast.contains("求解") || lowLast.contains("解答")
                    || lowLast.contains("证明");
                if (!isEdu) isQuestion = false;
            }

            // ??2??? AI ?????????
            // 先检查 AI 是否在表扬学生（答对了 → 不记录错题）
            boolean isPraise = false;
            String[] praiseKeywords = {
                "你答对了", "回答正确", "完全正确", "正确无误",
                "做得很好", "非常好", "很好！", "没错",
                "答案正确", "you are correct", "that's right",
                "well done", "good job", "exactly right"
            };
            for (String kw : praiseKeywords) {
                if (lastContent.contains(kw)) {
                    isPraise = true;
                    break;
                }
            }
            if (isPraise) return;

            boolean isCorrection = false;
            if (!isQuestion) {
                String[] correctionKeywords = {
                    "不对", "不正确", "错了", "错误", "不等于", "不是", "错的",
                    "正确答案", "应该是", "解答", "答案是", "实际上",
                    "incorrect", "wrong", "not correct", "mistake",
                    "correct answer", "should be", "actually"
                };
                for (String kw : correctionKeywords) {
                    if (lastContent.contains(kw)) {
                        isCorrection = true;
                        break;
                    }
                }
            }

            if (!isQuestion && !isCorrection) return;

            // 过滤用户消息：跳过问候语、闲聊、纯表情等
            String trimmedUser = userMessage.trim().toLowerCase();
            String[] skipPatterns = {
                "你好", "hi", "hello", "hey", "在吗", "在不",
                "谢谢", "thanks", "thank you", "好的", "ok",
                "晚上好", "早上好", "下午好",
                "晚安", "再见", "bye", "goodbye",
                "哈哈", "嘻嘻", "啊", "哦",
                "没事", "无聊"
            };
            boolean isGreeting = false;
            for (String p : skipPatterns) {
                if (trimmedUser.equals(p) || trimmedUser.startsWith(p)) {
                    isGreeting = true;
                    break;
                }
            }
            if (isGreeting || trimmedUser.length() < 2) return;

            // 过滤：如果用户消息是提问（问问题），不是回答 → 跳过
            if (trimmedUser.endsWith("?") || trimmedUser.endsWith("？")
                || trimmedUser.contains("什么") || trimmedUser.contains("怎么")
                || trimmedUser.contains("多少") || trimmedUser.contains("如何")
                || trimmedUser.contains("哪个") || trimmedUser.contains("为什么")
                || trimmedUser.contains("what") || trimmedUser.contains("how")
                || trimmedUser.contains("which") || trimmedUser.contains("why")) {
                return;
            }

            // ?????????
            if (userMessage.length() > 500) return;

            // 简洁传参：用户说的原话 + AI的纠正回复，让LLM自行提取题目和答案
            final String studentSaid = userMessage;
            final String aiCorrection = lastContent;
            streamExecutor.submit(() -> {
                try {
                    agentServiceClient.diagnoseMistake(userId, studentSaid, studentSaid, aiCorrection);
                    log.info("自动记录错题成功: userId={}", userId);
                } catch (Exception e) {
                    log.debug("自动记录错题跳过: {}", e.getMessage());
                }
            });
        } catch (Exception e) {
            log.debug("自动记录错题跳过: {}", e.getMessage());
        }
    }

}

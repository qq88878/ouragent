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
import com.edu.agent.module.knowledge.entity.KnowledgeBase;
import com.edu.agent.module.knowledge.mapper.KnowledgeMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class ChatServiceImpl extends ServiceImpl<ChatSessionMapper, ChatSession> implements ChatService {

    private final AgentServiceClient agentServiceClient;
    private final ChatMessageMapper messageMapper;
    private final KnowledgeMapper knowledgeMapper;

    @Override
    @Transactional
    public ChatSessionDTO createSession(Long userId, Long courseId) {
        ChatSession session = new ChatSession();
        session.setUserId(userId);
        session.setCourseId(courseId);
        session.setTitle("新对话");
        save(session);

        log.info("会话创建成功: id={}, userId={}", session.getId(), userId);
        return toSessionDTO(session, null);
    }

    @Override
    public List<ChatSessionDTO> listSessions(Long userId) {
        LambdaQueryWrapper<ChatSession> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(ChatSession::getUserId, userId)
                .orderByDesc(ChatSession::getUpdateTime);
        List<ChatSession> sessions = list(wrapper);

        return sessions.stream()
                .map(session -> {
                    LambdaQueryWrapper<ChatMessage> msgWrapper = new LambdaQueryWrapper<>();
                    msgWrapper.eq(ChatMessage::getSessionId, session.getId())
                            .orderByDesc(ChatMessage::getCreateTime)
                            .last("LIMIT 1");
                    ChatMessage lastMessage = messageMapper.selectOne(msgWrapper);
                    return toSessionDTO(session, lastMessage);
                })
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
        Map<String, Object> context = new HashMap<>();
        if (session.getCourseId() != null) {
            LambdaQueryWrapper<KnowledgeBase> kbWrapper = new LambdaQueryWrapper<>();
            kbWrapper.eq(KnowledgeBase::getCourseId, session.getCourseId())
                    .eq(KnowledgeBase::getStatus, 1); // indexed only
            List<KnowledgeBase> knowledgeList = knowledgeMapper.selectList(kbWrapper);
            List<Long> knowledgeIds = knowledgeList.stream()
                    .map(KnowledgeBase::getId)
                    .collect(Collectors.toList());
            if (!knowledgeIds.isEmpty()) {
                context.put("knowledge_ids", knowledgeIds);
            }
        }

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

    private ChatSessionDTO toSessionDTO(ChatSession session, ChatMessage lastMessage) {
        ChatSessionDTO dto = new ChatSessionDTO();
        dto.setId(session.getId());
        dto.setCourseId(session.getCourseId());
        dto.setTitle(session.getTitle());
        dto.setCreateTime(session.getCreateTime());
        if (lastMessage != null) {
            dto.setLastMessage(lastMessage.getContent());
            dto.setLastMessageTime(lastMessage.getCreateTime());
        }
        return dto;
    }
}

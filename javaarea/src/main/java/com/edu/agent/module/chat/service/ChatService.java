package com.edu.agent.module.chat.service;

import com.edu.agent.module.chat.dto.ChatRequest;
import com.edu.agent.module.chat.dto.ChatResponse;
import com.edu.agent.module.chat.dto.ChatSessionDTO;
import com.edu.agent.module.chat.entity.ChatMessage;
import com.baomidou.mybatisplus.core.metadata.IPage;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;
import java.util.Map;

public interface ChatService {

    ChatSessionDTO createSession(Long userId, Long courseId);

    List<ChatSessionDTO> listSessions(Long userId);

    IPage<ChatMessage> getSessionMessages(Long sessionId, int page, int size);

    ChatResponse sendMessage(Long sessionId, Long userId, ChatRequest request);

    SseEmitter sendMessageStream(Long sessionId, Long userId, ChatRequest request);

    void deleteSession(Long sessionId, Long userId);

    Map<String, Object> getChatSignals(Long sessionId);
}

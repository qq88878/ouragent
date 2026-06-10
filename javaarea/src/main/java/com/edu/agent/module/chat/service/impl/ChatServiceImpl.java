package com.edu.agent.module.chat.service.impl;

import com.edu.agent.module.chat.dto.ChatRequest;
import com.edu.agent.module.chat.dto.ChatResponse;
import com.edu.agent.module.chat.dto.ChatSessionDTO;
import com.edu.agent.module.chat.entity.ChatMessage;
import com.edu.agent.module.chat.entity.ChatSession;
import com.edu.agent.module.chat.mapper.ChatSessionMapper;
import com.edu.agent.module.chat.service.ChatService;
import com.edu.agent.module.chat.service.client.AgentServiceClient;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Slf4j
@Service
public class ChatServiceImpl extends ServiceImpl<ChatSessionMapper, ChatSession> implements ChatService {

    @Autowired
    private AgentServiceClient agentServiceClient;

    @Override
    public ChatSessionDTO createSession(Long userId, Long courseId) {
        // TODO phase 3: create session record
        //  1. build ChatSession entity with userId, courseId
        //  2. set default title
        //  3. save to DB
        //  4. convert to ChatSessionDTO and return
        throw new UnsupportedOperationException("Not implemented yet - phase 3");
    }

    @Override
    public List<ChatSessionDTO> listSessions(Long userId) {
        // TODO phase 3: list sessions for user
        //  1. query sessions by userId
        //  2. for each session, fetch last message as preview
        //  3. convert to ChatSessionDTO list
        throw new UnsupportedOperationException("Not implemented yet - phase 3");
    }

    @Override
    public IPage<ChatMessage> getSessionMessages(Long sessionId, int page, int size) {
        // TODO phase 3: get paginated messages for session
        //  1. validate session exists
        //  2. query messages by sessionId with pagination
        throw new UnsupportedOperationException("Not implemented yet - phase 3");
    }

    @Override
    public ChatResponse sendMessage(Long sessionId, Long userId, ChatRequest request) {
        // TODO phase 3: core chat logic
        //  1. validate session ownership
        //  2. store user message (role=USER)
        //  3. load course knowledge IDs as context
        //  4. call agentServiceClient.chatWithContext(message, context)
        //  5. store assistant message (role=ASSISTANT)
        //  6. update session message_count
        //  7. async update study_record
        throw new UnsupportedOperationException("Not implemented yet - phase 3");
    }

    @Override
    public void deleteSession(Long sessionId, Long userId) {
        // TODO phase 3: soft-delete session
        //  1. validate session ownership
        //  2. logically delete session and its messages
        throw new UnsupportedOperationException("Not implemented yet - phase 3");
    }
}

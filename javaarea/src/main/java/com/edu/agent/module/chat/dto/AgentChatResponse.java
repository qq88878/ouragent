package com.edu.agent.module.chat.dto;

import lombok.Data;

/**
 * Typed response from Python Agent /agent/chat and /agent/chat/context endpoints.
 */
@Data
public class AgentChatResponse {

    private String response;

    private String sessionId;

    private String status;
}

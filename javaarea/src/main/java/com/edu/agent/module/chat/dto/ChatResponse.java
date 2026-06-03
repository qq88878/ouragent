package com.edu.agent.module.chat.dto;

import lombok.Data;

@Data
public class ChatResponse {

    private String response;

    private Long sessionId;

    private Long messageId;

    private String agentId;
}

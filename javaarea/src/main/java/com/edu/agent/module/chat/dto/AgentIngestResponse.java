package com.edu.agent.module.chat.dto;

import lombok.Data;

/**
 * Typed response from Python Agent /agent/knowledge/ingest endpoint.
 */
@Data
public class AgentIngestResponse {

    private Long knowledgeId;

    private Integer chunks;

    private String status;
}

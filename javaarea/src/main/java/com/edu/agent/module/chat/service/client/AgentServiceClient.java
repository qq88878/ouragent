package com.edu.agent.module.chat.service.client;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Slf4j
@Service
public class AgentServiceClient {

    private final RestTemplate restTemplate;
    private final String agentServiceUrl;
    private final String serviceKey;

    public AgentServiceClient(
            RestTemplate restTemplate,
            @Value("${agent.service.url:http://localhost:8000}") String agentServiceUrl,
            @Value("${agent.service.key:default-dev-key}") String serviceKey) {
        this.restTemplate = restTemplate;
        this.agentServiceUrl = agentServiceUrl;
        this.serviceKey = serviceKey;
    }

    /**
     * 构建带服务间密钥的请求头
     */
    private HttpHeaders createHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("X-Service-Key", serviceKey);
        return headers;
    }

    // ===== Phase 1: Basic =====

    public String chat(String message) {
        // TODO phase 1: POST /agent/chat
        throw new UnsupportedOperationException("Not implemented yet - phase 1");
    }

    public boolean isHealthy() {
        // TODO phase 1: GET /health (no auth needed)
        throw new UnsupportedOperationException("Not implemented yet - phase 1");
    }

    public Map<String, Object> getStatus() {
        // TODO phase 1: GET /agent/status (no auth needed)
        throw new UnsupportedOperationException("Not implemented yet - phase 1");
    }

    // ===== Phase 2: Knowledge =====

    public String ingestKnowledge(Long knowledgeId, Long courseId, String content, String fileType) {
        // TODO phase 2: POST /agent/knowledge/ingest
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    public Map<String, Object> getKnowledgeStatus(Long knowledgeId) {
        // TODO phase 2: GET /agent/knowledge/status/{id}
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    // ===== Phase 3: Enhanced AI =====

    public String chatWithContext(String message, Map<String, Object> context) {
        // TODO phase 3: POST /agent/chat with context (knowledge_ids, student_profile, session history)
        throw new UnsupportedOperationException("Not implemented yet - phase 3");
    }

    // ===== Phase 4: Learning =====

    public Map<String, Object> generateLearningPath(Map<String, Object> studentProfile, Long courseId, String goal) {
        // TODO phase 4: POST /agent/learning-path/generate
        throw new UnsupportedOperationException("Not implemented yet - phase 4");
    }

    public Map<String, Object> evaluateAnswer(String question, String answer) {
        // TODO phase 4: POST /agent/evaluate
        throw new UnsupportedOperationException("Not implemented yet - phase 4");
    }
}

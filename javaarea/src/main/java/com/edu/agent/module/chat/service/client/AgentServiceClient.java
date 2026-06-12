package com.edu.agent.module.chat.service.client;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
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

    private HttpHeaders createHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("X-Service-Key", serviceKey);
        return headers;
    }

    // ===== Phase 1: Basic =====

    public String chat(String message) {
        Map<String, Object> body = new HashMap<>();
        body.put("message", message);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, createHeaders());
        ResponseEntity<Map> response = restTemplate.postForEntity(
                agentServiceUrl + "/agent/chat", request, Map.class);

        if (response.getBody() != null) {
            return (String) response.getBody().get("response");
        }
        return "No response from agent";
    }

    public boolean isHealthy() {
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(
                    agentServiceUrl + "/health", Map.class);
            return response.getStatusCode().is2xxSuccessful();
        } catch (Exception e) {
            log.warn("Agent health check failed: {}", e.getMessage());
            return false;
        }
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getStatus() {
        ResponseEntity<Map> response = restTemplate.getForEntity(
                agentServiceUrl + "/agent/status", Map.class);
        return response.getBody() != null ? response.getBody() : new HashMap<>();
    }

    // ===== Phase 2: Knowledge =====

    public String ingestKnowledge(Long knowledgeId, Long courseId, String content, String fileType) {
        Map<String, Object> body = new HashMap<>();
        body.put("knowledge_id", knowledgeId);
        body.put("course_id", courseId);
        body.put("content", content);
        body.put("file_type", fileType);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, createHeaders());
        ResponseEntity<Map> response = restTemplate.postForEntity(
                agentServiceUrl + "/agent/knowledge/ingest-text", request, Map.class);

        if (response.getBody() != null) {
            return (String) response.getBody().get("status");
        }
        return "failed";
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getKnowledgeStatus(Long knowledgeId) {
        HttpEntity<Void> request = new HttpEntity<>(createHeaders());
        ResponseEntity<Map> response = restTemplate.exchange(
                agentServiceUrl + "/agent/knowledge/status",
                org.springframework.http.HttpMethod.GET,
                request, Map.class);
        return response.getBody() != null ? response.getBody() : new HashMap<>();
    }

    // ===== Phase 3: Enhanced AI =====

    @SuppressWarnings("unchecked")
    public String chatWithContext(String message, Map<String, Object> context) {
        Map<String, Object> body = new HashMap<>();
        body.put("message", message);
        body.put("context", context);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, createHeaders());
        ResponseEntity<Map> response = restTemplate.postForEntity(
                agentServiceUrl + "/agent/chat/context", request, Map.class);

        if (response.getBody() != null) {
            return (String) response.getBody().get("response");
        }
        return "No response from agent";
    }

    // ===== Phase 4: Learning =====

    @SuppressWarnings("unchecked")
    public Map<String, Object> generateLearningPath(Map<String, Object> studentProfile, Long courseId, String goal) {
        Map<String, Object> body = new HashMap<>();
        body.put("student_profile", studentProfile);
        body.put("course_id", courseId);
        body.put("goal", goal);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, createHeaders());
        ResponseEntity<Map> response = restTemplate.postForEntity(
                agentServiceUrl + "/agent/plan", request, Map.class);

        return response.getBody() != null ? response.getBody() : new HashMap<>();
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> evaluateAnswer(String question, String answer) {
        Map<String, Object> body = new HashMap<>();
        body.put("question", question);
        body.put("student_answer", answer);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, createHeaders());
        ResponseEntity<Map> response = restTemplate.postForEntity(
                agentServiceUrl + "/agent/evaluate", request, Map.class);

        return response.getBody() != null ? response.getBody() : new HashMap<>();
    }
}

package com.edu.agent.module.chat.service.client;

import com.edu.agent.module.chat.dto.AgentChatResponse;
import com.edu.agent.module.chat.dto.AgentIngestResponse;
import com.edu.agent.module.learning.dto.AgentLearningPathResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

@Service
public class AgentServiceClient {
    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(AgentServiceClient.class);

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

    private HttpHeaders createMultipartHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.MULTIPART_FORM_DATA);
        headers.set("X-Service-Key", serviceKey);
        return headers;
    }

    // ===== Phase 1: Basic =====

    public String chat(String message) {
        AgentChatResponse response = chatTyped(message);
        return response.getResponse();
    }

    public AgentChatResponse chatTyped(String message) {
        Map<String, Object> body = new HashMap<>();
        body.put("message", message);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, createHeaders());
        ResponseEntity<AgentChatResponse> response = restTemplate.exchange(
                agentServiceUrl + "/agent/chat",
                HttpMethod.POST,
                request,
                new ParameterizedTypeReference<>() {});

        return response.getBody() != null ? response.getBody() : new AgentChatResponse();
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

    public String ingestKnowledge(Long knowledgeId, Long courseId, String filePath, String fileType) {
        try {
            HttpHeaders headers = createHeaders();
            headers.setContentType(new MediaType(MediaType.MULTIPART_FORM_DATA, StandardCharsets.UTF_8));

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", new FileSystemResource(filePath));
            body.add("knowledge_id", knowledgeId.toString());
            body.add("course_id", courseId != null ? courseId.toString() : "");

            HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);
            ResponseEntity<Map> response = restTemplate.postForEntity(
                    agentServiceUrl + "/agent/knowledge/ingest", request, Map.class);

            if (response.getBody() != null) {
                Object status = response.getBody().get("status");
                return status != null ? status.toString() : "failed";
            }
            return "failed";
        } catch (Exception e) {
            log.error("调用 Agent 知识入库失败: knowledgeId={}", knowledgeId, e);
            return "failed";
        }
    }

    /**
     * Send a file to the agent service for knowledge ingestion via multipart upload.
     * Calls POST /agent/knowledge/ingest
     */
    @SuppressWarnings("unchecked")

    public AgentIngestResponse ingestKnowledgeFile(Long knowledgeId, Long courseId, File file) {
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", new FileSystemResource(file));
        body.add("knowledge_id", knowledgeId);
        body.add("course_id", courseId);

        HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, createMultipartHeaders());
        ResponseEntity<AgentIngestResponse> response = restTemplate.exchange(
                agentServiceUrl + "/agent/knowledge/ingest",
                HttpMethod.POST,
                request,
                new ParameterizedTypeReference<>() {});

        return response.getBody() != null ? response.getBody() : new AgentIngestResponse();
    }

    // Keep legacy method for backward compatibility

    // ===== Phase 3: Enhanced AI =====

    public String chatWithContext(String message, Map<String, Object> context) {
        AgentChatResponse response = chatWithContextTyped(message, context);
        return response.getResponse();
    }

    public AgentChatResponse chatWithContextTyped(String message, Map<String, Object> context) {
        Map<String, Object> body = new HashMap<>();
        body.put("message", message);
        body.put("context", context);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, createHeaders());
        ResponseEntity<AgentChatResponse> response = restTemplate.exchange(
                agentServiceUrl + "/agent/chat",
                HttpMethod.POST,
                request,
                new ParameterizedTypeReference<>() {});

        return response.getBody() != null ? response.getBody() : new AgentChatResponse();
    }

    // ===== Phase 4: Learning =====

    public AgentLearningPathResponse generateLearningPath(
            Map<String, Object> studentProfile, Long courseId, String goal) {
        Map<String, Object> body = new HashMap<>();
        body.put("student_profile", studentProfile);
        body.put("course_id", courseId);
        body.put("goal", goal);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, createHeaders());
        ResponseEntity<AgentLearningPathResponse> response = restTemplate.exchange(
                agentServiceUrl + "/agent/plan",
                HttpMethod.POST,
                request,
                new ParameterizedTypeReference<>() {});

        return response.getBody() != null ? response.getBody() : new AgentLearningPathResponse();
    }

    public Map<String, Object> evaluateAnswer(String question, String answer) {
        Map<String, Object> body = new HashMap<>();
        body.put("question", question);
        body.put("student_answer", answer);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, createHeaders());
        ResponseEntity<Map> response = restTemplate.postForEntity(
                agentServiceUrl + "/agent/evaluate", request, Map.class);

        return response.getBody() != null ? response.getBody() : new HashMap<>();
    }

    // ===== Streaming =====

    /**
     * 流式对话 — 读取 Python SSE 流，逐行转发给 SseEmitter
     * 注意：此方法会阻塞调用线程，应在独立线程中调用
     */
    public void streamChatWithContext(String message, Map<String, Object> context,
                                      org.springframework.web.servlet.mvc.method.annotation.SseEmitter emitter,
                                      StringBuilder accumulator) {
        Map<String, Object> body = new HashMap<>();
        body.put("message", message);
        body.put("context", context);

        HttpHeaders headers = createHeaders();
        HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, headers);

        restTemplate.execute(
                agentServiceUrl + "/agent/chat/stream",
                org.springframework.http.HttpMethod.POST,
                restTemplate.httpEntityCallback(request),
                (org.springframework.web.client.ResponseExtractor<Void>) response -> {
                    try (BufferedReader reader = new BufferedReader(
                            new InputStreamReader(response.getBody(), StandardCharsets.UTF_8))) {
                        String line;
                        java.util.Map<String, Object> wrapped;
                        com.fasterxml.jackson.databind.ObjectMapper localMapper = new com.fasterxml.jackson.databind.ObjectMapper();
                        while ((line = reader.readLine()) != null) {
                            if (line.startsWith("data: ")) {
                                String data = line.substring(6);
                                try {
                                    java.util.Map<String, Object> parsed = localMapper.readValue(data, java.util.Map.class);
                                    Object content = parsed.get("content");
                                    if (content != null) {
                                        accumulator.append(content.toString());
                                    }
                                    wrapped = new java.util.HashMap<>();
                                    wrapped.put("type", "text");
                                    wrapped.put("content", content != null ? content.toString() : "");
                                    emitter.send(org.springframework.web.servlet.mvc.method.annotation.SseEmitter
                                            .event().data(localMapper.writeValueAsString(wrapped)));
                                } catch (Exception ignored) {
                                }
                            }
                        }
                        try {
                            emitter.send(org.springframework.web.servlet.mvc.method.annotation.SseEmitter
                                    .event().data("{\"type\":\"end\"}"));
                        } catch (Exception ignored) {}
                        emitter.complete();
                    } catch (Exception e) {
                        log.error("SSE stream read error", e);
                        try {
                            emitter.completeWithError(e);
                        } catch (Exception ignored) {
                        }
                    }
                    return null;
                }
        );
    }

    // ===== Phase 5: Mistake Book =====

    /**
     * 诊断错题，自动记录到错题本
     */
    public Map<String, Object> diagnoseMistake(String userId, String question, 
                                                String studentAnswer, String correctAnswer) {
        Map<String, Object> body = new HashMap<>();
        body.put("user_id", userId);
        body.put("question", question);
        body.put("student_answer", studentAnswer);
        if (correctAnswer != null && !correctAnswer.isEmpty()) {
            body.put("correct_answer", correctAnswer);
        }

        try {
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(body, createHeaders());
            ResponseEntity<Map> response = restTemplate.postForEntity(
                    agentServiceUrl + "/agent/mistake-book/diagnose", request, Map.class);
            return response.getBody() != null ? response.getBody() : new HashMap<>();
        } catch (Exception e) {
            log.error("调用错题诊断失败: userId={}", userId, e);
            return new HashMap<>();
        }
    }

    // ===== Phase 6: Chat Signals =====

    /**
     * 获取会话的实时学习画像信号
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getChatSignals(String sessionId) {
        try {
            HttpEntity<Void> request = new HttpEntity<>(createHeaders());
            ResponseEntity<Map> response = restTemplate.exchange(
                    agentServiceUrl + "/agent/signals/" + sessionId,
                    HttpMethod.GET,
                    request,
                    new ParameterizedTypeReference<>() {});
            return response.getBody() != null ? response.getBody() : new HashMap<>();
        } catch (Exception e) {
            log.error("获取会话画像信号失败: sessionId={}", sessionId, e);
            return new HashMap<>();
        }
    }

}

// Java调用Python Agent服务的客户端
// 在Spring Boot项目中注入使用

package com.yourcompany.agent.client;

import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.stereotype.Service;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;

/**
 * Python Agent服务客户端
 *
 * TODO: 阶段一 - 实现基础HTTP调用
 *   - chat(): 对话接口
 *   - isHealthy(): 健康检查
 *
 * TODO: 阶段四 - 增强功能
 *   - 超时配置 (从application.yml读取)
 *   - 重试机制 (指数退避)
 *   - 熔断器 (Resilience4j)
 *   - 异步调用 (WebClient替代RestTemplate)
 *   - 连接池管理
 */
@Service
public class AgentServiceClient {

    private final RestTemplate restTemplate;
    private final String agentServiceUrl;

    public AgentServiceClient() {
        this.restTemplate = new RestTemplate();
        // TODO: 从配置注入，不要硬编码
        this.agentServiceUrl = "http://agent-service:8000";
    }

    public AgentServiceClient(String serviceUrl) {
        this.restTemplate = new RestTemplate();
        this.agentServiceUrl = serviceUrl;
    }

    // ==================== 数据模型 ====================

    /**
     * 对话请求
     */
    public static class ChatRequest {
        @JsonProperty("message")
        private String message;

        @JsonProperty("context")
        private Map<String, Object> context;

        public ChatRequest(String message) {
            this.message = message;
        }

        public String getMessage() { return message; }
        public void setMessage(String message) { this.message = message; }
        public Map<String, Object> getContext() { return context; }
        public void setContext(Map<String, Object> context) { this.context = context; }
    }

    /**
     * 对话响应
     */
    public static class ChatResponse {
        @JsonProperty("response")
        private String response;

        @JsonProperty("agent_id")
        private String agentId;

        @JsonProperty("status")
        private String status;

        public String getResponse() { return response; }
        public String getAgentId() { return agentId; }
        public String getStatus() { return status; }
    }

    /**
     * Agent状态
     */
    public static class AgentStatus {
        @JsonProperty("id")
        private String id;

        @JsonProperty("name")
        private String name;

        @JsonProperty("description")
        private String description;

        @JsonProperty("available_tools")
        private List<String> availableTools;

        @JsonProperty("memory_size")
        private Integer memorySize;

        public String getId() { return id; }
        public String getName() { return name; }
        public String getDescription() { return description; }
        public List<String> getAvailableTools() { return availableTools; }
        public Integer getMemorySize() { return memorySize; }
    }

    // ==================== API方法 ====================

    /**
     * 与Agent对话
     *
     * TODO: 阶段一 - 实现
     *   1. 构造ChatRequest
     *   2. POST /agent/chat
     *   3. 解析ChatResponse
     *   4. 异常处理 (超时、服务不可用)
     */
    public String chat(String message) {
        // TODO: 实现
        throw new UnsupportedOperationException("Not implemented yet");
    }

    /**
     * 与Agent对话 (带上下文)
     *
     * TODO: 阶段一 - 实现
     */
    public String chat(String message, Map<String, Object> context) {
        // TODO: 实现
        throw new UnsupportedOperationException("Not implemented yet");
    }

    /**
     * 调用Agent工具
     *
     * TODO: 阶段三 - 实现
     */
    public Object callTool(String toolName, Map<String, Object> parameters) {
        // TODO: 实现
        throw new UnsupportedOperationException("Not implemented yet");
    }

    /**
     * 获取Agent状态
     *
     * TODO: 阶段一 - 实现
     */
    public AgentStatus getStatus() {
        // TODO: 实现
        throw new UnsupportedOperationException("Not implemented yet");
    }

    /**
     * 健康检查
     *
     * TODO: 阶段一 - 实现
     */
    public boolean isHealthy() {
        // TODO: 实现
        throw new UnsupportedOperationException("Not implemented yet");
    }
}

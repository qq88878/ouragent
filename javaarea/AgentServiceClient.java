// Java调用Python Agent服务的示例代码
// 可以直接复制到Java项目中使用

package com.yourcompany.agent.client;

import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.stereotype.Service;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.*;

/**
 * Python Agent服务客户端
 * 用于Java后端调用Python Agent服务
 */
@Service
public class AgentServiceClient {

    private final RestTemplate restTemplate;
    private final String agentServiceUrl;

    public AgentServiceClient() {
        this.restTemplate = new RestTemplate();
        // Agent服务地址，可以通过配置文件或环境变量设置
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

        @JsonProperty("user_id")
        private String userId;

        public ChatRequest(String message) {
            this.message = message;
        }

        public ChatRequest(String message, String userId) {
            this.message = message;
            this.userId = userId;
        }

        // Getters and Setters
        public String getMessage() { return message; }
        public void setMessage(String message) { this.message = message; }
        public Map<String, Object> getContext() { return context; }
        public void setContext(Map<String, Object> context) { this.context = context; }
        public String getUserId() { return userId; }
        public void setUserId(String userId) { this.userId = userId; }
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

        // Getters
        public String getResponse() { return response; }
        public String getAgentId() { return agentId; }
        public String getStatus() { return status; }
    }

    /**
     * 工具调用请求
     */
    public static class ToolRequest {
        @JsonProperty("tool_name")
        private String toolName;

        @JsonProperty("parameters")
        private Map<String, Object> parameters;

        public ToolRequest(String toolName, Map<String, Object> parameters) {
            this.toolName = toolName;
            this.parameters = parameters;
        }

        // Getters and Setters
        public String getToolName() { return toolName; }
        public void setToolName(String toolName) { this.toolName = toolName; }
        public Map<String, Object> getParameters() { return parameters; }
        public void setParameters(Map<String, Object> parameters) { this.parameters = parameters; }
    }

    /**
     * 工具调用响应
     */
    public static class ToolResponse {
        @JsonProperty("result")
        private Object result;

        @JsonProperty("tool_name")
        private String toolName;

        @JsonProperty("status")
        private String status;

        // Getters
        public Object getResult() { return result; }
        public String getToolName() { return toolName; }
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

        // Getters
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
     * @param message 用户消息
     * @return Agent回复
     */
    public String chat(String message) {
        ChatRequest request = new ChatRequest(message);
        ChatResponse response = restTemplate.postForObject(
            agentServiceUrl + "/agent/chat",
            request,
            ChatResponse.class
        );
        return response != null ? response.getResponse() : null;
    }

    /**
     * 与Agent对话（带用户ID）
     *
     * @param message 用户消息
     * @param userId 用户ID
     * @return Agent回复
     */
    public String chat(String message, String userId) {
        ChatRequest request = new ChatRequest(message, userId);
        ChatResponse response = restTemplate.postForObject(
            agentServiceUrl + "/agent/chat",
            request,
            ChatResponse.class
        );
        return response != null ? response.getResponse() : null;
    }

    /**
     * 与Agent对话（带上下文）
     *
     * @param message 用户消息
     * @param context 上下文信息
     * @return Agent回复
     */
    public String chat(String message, Map<String, Object> context) {
        ChatRequest request = new ChatRequest(message);
        request.setContext(context);
        ChatResponse response = restTemplate.postForObject(
            agentServiceUrl + "/agent/chat",
            request,
            ChatResponse.class
        );
        return response != null ? response.getResponse() : null;
    }

    /**
     * 调用Agent工具
     *
     * @param toolName 工具名称
     * @param parameters 工具参数
     * @return 工具执行结果
     */
    public Object callTool(String toolName, Map<String, Object> parameters) {
        ToolRequest request = new ToolRequest(toolName, parameters);
        ToolResponse response = restTemplate.postForObject(
            agentServiceUrl + "/agent/tool",
            request,
            ToolResponse.class
        );
        return response != null ? response.getResult() : null;
    }

    /**
     * 获取Agent状态
     *
     * @return Agent状态
     */
    public AgentStatus getStatus() {
        return restTemplate.getForObject(
            agentServiceUrl + "/agent/status",
            AgentStatus.class
        );
    }

    /**
     * 获取可用工具列表
     *
     * @return 工具列表
     */
    public List<String> listTools() {
        Map response = restTemplate.getForObject(
            agentServiceUrl + "/agent/tools",
            Map.class
        );
        return response != null ? (List<String>) response.get("tools") : Collections.emptyList();
    }

    /**
     * 健康检查
     *
     * @return 是否健康
     */
    public boolean isHealthy() {
        try {
            Map response = restTemplate.getForObject(
                agentServiceUrl + "/health",
                Map.class
            );
            return response != null && "healthy".equals(response.get("status"));
        } catch (Exception e) {
            return false;
        }
    }

    // ==================== 使用示例 ====================

    /**
     * 使用示例
     */
    public static void main(String[] args) {
        // 创建客户端
        AgentServiceClient client = new AgentServiceClient("http://localhost:8000");

        // 检查服务是否可用
        if (client.isHealthy()) {
            System.out.println("Agent服务可用");
        }

        // 对话示例
        String response = client.chat("你好！");
        System.out.println("Agent回复: " + response);

        // 带用户ID的对话
        response = client.chat("计算2+2", "user123");
        System.out.println("Agent回复: " + response);

        // 调用工具示例
        Map<String, Object> params = new HashMap<>();
        params.put("expression", "10 * 20");
        Object result = client.callTool("calculator", params);
        System.out.println("计算结果: " + result);

        // 获取状态
        AgentStatus status = client.getStatus();
        System.out.println("Agent名称: " + status.getName());
        System.out.println("可用工具: " + status.getAvailableTools());
    }
}

// Java Controller示例
// 展示如何在Java后端调用Python Agent服务

package com.yourcompany.agent.controller;

import com.yourcompany.agent.client.AgentServiceClient;
import com.yourcompany.agent.client.AgentServiceClient.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

/**
 * Agent控制器
 * 处理前端请求，调用Python Agent服务
 */
@RestController
@RequestMapping("/api/agent")
@CrossOrigin(origins = "*")
public class AgentController {

    @Autowired
    private AgentServiceClient agentClient;

    /**
     * 对话接口
     *
     * 前端调用示例:
     * POST /api/agent/chat
     * {
     *   "message": "你好",
     *   "userId": "user123"
     * }
     */
    @PostMapping("/chat")
    public ResponseEntity<Map<String, Object>> chat(@RequestBody ChatRequest request) {
        try {
            // 调用Python Agent服务
            String response = agentClient.chat(
                request.getMessage(),
                request.getUserId()
            );

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("response", response);
            result.put("timestamp", System.currentTimeMillis());

            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("error", e.getMessage());

            return ResponseEntity.internalServerError().body(error);
        }
    }

    /**
     * 工具调用接口
     *
     * 前端调用示例:
     * POST /api/agent/tool
     * {
     *   "toolName": "calculator",
     *   "parameters": {"expression": "2+2"}
     * }
     */
    @PostMapping("/tool")
    public ResponseEntity<Map<String, Object>> callTool(@RequestBody ToolCallRequest request) {
        try {
            Object result = agentClient.callTool(
                request.getToolName(),
                request.getParameters()
            );

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("result", result);
            response.put("toolName", request.getToolName());

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("error", e.getMessage());

            return ResponseEntity.internalServerError().body(error);
        }
    }

    /**
     * 获取Agent状态
     *
     * GET /api/agent/status
     */
    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getStatus() {
        try {
            AgentStatus status = agentClient.getStatus();

            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("status", status);

            return ResponseEntity.ok(result);
        } catch (Exception e) {
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("error", e.getMessage());

            return ResponseEntity.internalServerError().body(error);
        }
    }

    /**
     * 健康检查
     *
     * GET /api/agent/health
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        boolean isHealthy = agentClient.isHealthy();

        Map<String, Object> result = new HashMap<>();
        result.put("healthy", isHealthy);
        result.put("timestamp", System.currentTimeMillis());

        return ResponseEntity.ok(result);
    }

    // ==================== 请求模型 ====================

    /**
     * 对话请求
     */
    public static class ChatRequest {
        private String message;
        private String userId;
        private Map<String, Object> context;

        public String getMessage() { return message; }
        public void setMessage(String message) { this.message = message; }
        public String getUserId() { return userId; }
        public void setUserId(String userId) { this.userId = userId; }
        public Map<String, Object> getContext() { return context; }
        public void setContext(Map<String, Object> context) { this.context = context; }
    }

    /**
     * 工具调用请求
     */
    public static class ToolCallRequest {
        private String toolName;
        private Map<String, Object> parameters;

        public String getToolName() { return toolName; }
        public void setToolName(String toolName) { this.toolName = toolName; }
        public Map<String, Object> getParameters() { return parameters; }
        public void setParameters(Map<String, Object> parameters) { this.parameters = parameters; }
    }
}

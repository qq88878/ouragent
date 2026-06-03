// Spring Boot Controller
// 处理前端请求，转发给Python Agent服务

package com.yourcompany.agent.controller;

import com.yourcompany.agent.client.AgentServiceClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

/**
 * Agent控制器
 *
 * TODO: 阶段一 - 实现基础接口
 *   - POST /api/agent/chat  -> 转发给Python /agent/chat
 *   - GET  /api/agent/health -> 转发给Python /health
 *
 * TODO: 阶段四 - 增强功能
 *   - 请求参数校验 (@Valid)
 *   - 统一异常处理 (@ControllerAdvice)
 *   - 请求限流 (RateLimiter)
 *   - 调用链追踪 (Sleuth/Micrometer)
 *   - SSE流式响应 (支持打字机效果)
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
     * TODO: 阶段一 - 实现
     *   1. 接收前端请求
     *   2. 调用 agentClient.chat()
     *   3. 封装统一响应格式返回
     *
     * 请求示例:
     *   POST /api/agent/chat
     *   {"message": "你好", "userId": "user123"}
     */
    @PostMapping("/chat")
    public ResponseEntity<Map<String, Object>> chat(@RequestBody Map<String, Object> request) {
        // TODO: 实现
        return ResponseEntity.status(501).body(Map.of("error", "Not implemented yet"));
    }

    /**
     * 工具调用接口
     *
     * TODO: 阶段三 - 实现
     */
    @PostMapping("/tool")
    public ResponseEntity<Map<String, Object>> callTool(@RequestBody Map<String, Object> request) {
        // TODO: 实现
        return ResponseEntity.status(501).body(Map.of("error", "Not implemented yet"));
    }

    /**
     * 获取Agent状态
     *
     * TODO: 阶段一 - 实现
     */
    @GetMapping("/status")
    public ResponseEntity<Map<String, Object>> getStatus() {
        // TODO: 实现
        return ResponseEntity.status(501).body(Map.of("error", "Not implemented yet"));
    }

    /**
     * 健康检查
     *
     * TODO: 阶段一 - 实现
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> healthCheck() {
        // TODO: 实现
        return ResponseEntity.status(501).body(Map.of("error", "Not implemented yet"));
    }

    // ==================== 请求/响应模型 ====================

    // TODO: 阶段一 - 抽取为独立DTO类 (ChatRequest, ChatResponse, ErrorResponse等)
    // TODO: 阶段四 - 添加@Valid校验注解
}

package com.edu.agent.module.chat.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edu.agent.common.result.Result;
import com.edu.agent.module.chat.dto.ChatRequest;
import com.edu.agent.module.chat.dto.ChatResponse;
import com.edu.agent.module.chat.dto.ChatSessionDTO;
import com.edu.agent.module.chat.entity.ChatMessage;
import com.edu.agent.module.chat.service.ChatService;
import com.edu.agent.security.LoginUser;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/chat")
public class ChatController {

    private final ChatService chatService;
    public ChatController(ChatService chatService) {
        this.chatService = chatService;
    }

    @PostMapping("/sessions")
    public Result<ChatSessionDTO> createSession(@RequestParam(required = false) Long courseId) {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return Result.success(chatService.createSession(loginUser.getUser().getId(), courseId));
    }

    @GetMapping("/sessions")
    public Result<List<ChatSessionDTO>> listSessions() {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return Result.success(chatService.listSessions(loginUser.getUser().getId()));
    }

    @GetMapping("/sessions/{id}/messages")
    public Result<IPage<ChatMessage>> getMessages(@PathVariable Long id,
                                                  @RequestParam(defaultValue = "1") int page,
                                                  @RequestParam(defaultValue = "20") int size) {
        return Result.success(chatService.getSessionMessages(id, page, size));
    }

    @PostMapping("/sessions/{id}/messages")
    public Result<ChatResponse> sendMessage(@PathVariable Long id,
                                            @Valid @RequestBody ChatRequest request) {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return Result.success(chatService.sendMessage(id, loginUser.getUser().getId(), request));
    }

    @DeleteMapping("/sessions/{id}")
    public Result<Void> deleteSession(@PathVariable Long id) {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        chatService.deleteSession(id, loginUser.getUser().getId());
        return Result.success();
    }

    @PostMapping(value = "/sessions/{id}/messages/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter sendMessageStream(@PathVariable Long id,
                                        @Valid @RequestBody ChatRequest request) {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return chatService.sendMessageStream(id, loginUser.getUser().getId(), request);
    }

    @GetMapping("/sessions/{id}/signals")
    public Result<Map<String, Object>> getChatSignals(@PathVariable Long id) {
        return Result.success(chatService.getChatSignals(id));
    }
}

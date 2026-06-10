package com.edu.agent.module.chat.controller;

import com.edu.agent.common.result.Result;
import com.edu.agent.module.chat.dto.ChatRequest;
import com.edu.agent.module.chat.dto.ChatResponse;
import com.edu.agent.module.chat.dto.ChatSessionDTO;
import com.edu.agent.module.chat.entity.ChatMessage;
import com.edu.agent.module.chat.service.ChatService;
import com.baomidou.mybatisplus.core.metadata.IPage;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/chat")
@RequiredArgsConstructor
public class ChatController {

    private final ChatService chatService;

    // TODO phase 3: get current user id from SecurityContext

    @PostMapping("/sessions")
    public Result<ChatSessionDTO> createSession(@RequestParam(required = false) Long courseId) {
        // TODO phase 3: extract userId from auth context, call chatService.createSession
        throw new UnsupportedOperationException("Not implemented yet - phase 3");
    }

    @GetMapping("/sessions")
    public Result<List<ChatSessionDTO>> listSessions() {
        // TODO phase 3: extract userId from auth context, call chatService.listSessions
        throw new UnsupportedOperationException("Not implemented yet - phase 3");
    }

    @GetMapping("/sessions/{id}/messages")
    public Result<IPage<ChatMessage>> getMessages(@PathVariable Long id,
                                                  @RequestParam(defaultValue = "1") int page,
                                                  @RequestParam(defaultValue = "20") int size) {
        // TODO phase 3: call chatService.getSessionMessages
        throw new UnsupportedOperationException("Not implemented yet - phase 3");
    }

    @PostMapping("/sessions/{id}/messages")
    public Result<ChatResponse> sendMessage(@PathVariable Long id,
                                            @Valid @RequestBody ChatRequest request) {
        // TODO phase 3: extract userId from auth context, call chatService.sendMessage (core interface)
        throw new UnsupportedOperationException("Not implemented yet - phase 3");
    }

    @DeleteMapping("/sessions/{id}")
    public Result<Void> deleteSession(@PathVariable Long id) {
        // TODO phase 3: extract userId from auth context, call chatService.deleteSession
        throw new UnsupportedOperationException("Not implemented yet - phase 3");
    }
}
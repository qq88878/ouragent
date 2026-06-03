package com.edu.agent.module.chat.dto;

import lombok.Data;

import jakarta.validation.constraints.NotBlank;

@Data
public class ChatRequest {

    @NotBlank(message = "message must not be blank")
    private String message;

    /** Nullable. null means create a new session */
    private Long sessionId;

    /** Nullable. Used to load course-specific context */
    private Long courseId;
}

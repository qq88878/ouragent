package com.edu.agent.module.chat.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class ChatSessionDTO {
    private Long id;
    private Long courseId;
    private String title;
    private String lastMessage;
    private LocalDateTime lastMessageTime;
    private LocalDateTime createTime;
}

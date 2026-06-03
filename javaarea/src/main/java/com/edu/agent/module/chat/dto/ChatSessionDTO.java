package com.edu.agent.module.chat.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class ChatSessionDTO {

    private Long id;

    private String title;

    private String sessionType;

    private Long courseId;

    private Integer status;

    private Integer messageCount;

    private String lastMessage;

    private LocalDateTime lastMessageTime;

    private LocalDateTime createTime;
}

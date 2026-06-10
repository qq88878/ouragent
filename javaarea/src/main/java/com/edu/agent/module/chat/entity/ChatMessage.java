package com.edu.agent.module.chat.entity;

import com.edu.agent.common.base.BaseEntity;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
@TableName("chat_message")
public class ChatMessage extends BaseEntity {
    private Long sessionId;
    private String role;      // USER / ASSISTANT / SYSTEM
    private String content;
    private Integer tokenCount;
}
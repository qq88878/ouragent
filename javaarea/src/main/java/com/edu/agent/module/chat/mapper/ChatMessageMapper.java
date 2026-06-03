package com.edu.agent.module.chat.mapper;

import com.edu.agent.module.chat.entity.ChatMessage;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface ChatMessageMapper extends BaseMapper<ChatMessage> {

    // TODO phase 3: select messages by session id, ordered by create_time desc, with pagination
    IPage<ChatMessage> selectBySessionId(@Param("page") Page<ChatMessage> page,
                                         @Param("sessionId") Long sessionId);
}

package com.edu.agent.module.chat.mapper;

import com.edu.agent.module.chat.entity.ChatSession;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface ChatSessionMapper extends BaseMapper<ChatSession> {

    // TODO phase 3: select sessions by user id, ordered by update_time desc
    List<ChatSession> selectByUserId(@Param("userId") Long userId);
}

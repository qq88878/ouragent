package com.edu.agent.module.learning.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.edu.agent.module.learning.entity.LearningPath;

import java.util.List;

public interface LearningPathMapper extends BaseMapper<LearningPath> {

    /**
     * Select learning paths by user ID.
     */
    List<LearningPath> selectByUserId(Long userId);
}

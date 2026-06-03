package com.edu.agent.module.learning.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.edu.agent.module.learning.entity.LearningPathStep;

import java.util.List;

public interface LearningPathStepMapper extends BaseMapper<LearningPathStep> {

    /**
     * Select steps by learning path ID.
     */
    List<LearningPathStep> selectByPathId(Long pathId);
}

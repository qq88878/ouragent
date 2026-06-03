package com.edu.agent.module.learning.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edu.agent.module.learning.entity.StudyRecord;

public interface StudyRecordMapper extends BaseMapper<StudyRecord> {

    /**
     * Select study records by user ID with pagination.
     */
    IPage<StudyRecord> selectByUserId(Long userId, int page, int size);
}

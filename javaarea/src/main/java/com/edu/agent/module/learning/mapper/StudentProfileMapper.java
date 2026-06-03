package com.edu.agent.module.learning.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.edu.agent.module.learning.entity.StudentProfile;

public interface StudentProfileMapper extends BaseMapper<StudentProfile> {

    /**
     * Select student profile by user ID.
     */
    StudentProfile selectByUserId(Long userId);
}

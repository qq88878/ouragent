package com.edu.agent.module.learning.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.module.learning.entity.StudentProfile;
import com.edu.agent.module.learning.mapper.StudentProfileMapper;
import com.edu.agent.module.learning.service.StudentProfileService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;

@Slf4j
@Service
public class StudentProfileServiceImpl
        extends ServiceImpl<StudentProfileMapper, StudentProfile>
        implements StudentProfileService {

    @Override
    public StudentProfile getProfile(Long userId) {
        // TODO phase 4 - query profile by userId via mapper
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @Override
    public void updateProfile(Long userId, StudentProfile profile) {
        // TODO phase 4 - find existing profile, merge fields, update in DB
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @Override
    public Map<String, Object> getRadarData(Long userId) {
        // TODO phase 4 - build radar chart data from strongPoints/weakPoints
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }
}

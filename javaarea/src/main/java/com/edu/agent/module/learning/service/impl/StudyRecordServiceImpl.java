package com.edu.agent.module.learning.service.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.module.learning.dto.StudyRecordDTO;
import com.edu.agent.module.learning.entity.StudyRecord;
import com.edu.agent.module.learning.mapper.StudyRecordMapper;
import com.edu.agent.module.learning.service.StudyRecordService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Map;

@Slf4j
@Service
public class StudyRecordServiceImpl
        extends ServiceImpl<StudyRecordMapper, StudyRecord>
        implements StudyRecordService {

    @Override
    public void recordStudy(Long userId, StudyRecordDTO dto) {
        // TODO phase 4 - map DTO to entity, set userId, insert into DB
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @Override
    public IPage<StudyRecordDTO> listRecords(Long userId, int page, int size) {
        // TODO phase 4 - build Page, query by userId, map to DTO page
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @Override
    public Map<String, Object> getStudyStats(Long userId) {
        // TODO phase 4 - aggregate study stats: total duration, avg score, record count, etc.
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }
}

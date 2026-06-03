package com.edu.agent.module.learning.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edu.agent.module.learning.dto.StudyRecordDTO;

import java.util.Map;

public interface StudyRecordService {

    /**
     * Record a study session.
     */
    void recordStudy(Long userId, StudyRecordDTO dto);

    /**
     * List study records with pagination.
     */
    IPage<StudyRecordDTO> listRecords(Long userId, int page, int size);

    /**
     * Get aggregated study statistics for a user.
     */
    Map<String, Object> getStudyStats(Long userId);
}

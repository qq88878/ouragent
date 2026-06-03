package com.edu.agent.module.learning.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edu.agent.common.result.Result;
import com.edu.agent.module.learning.dto.StudyRecordDTO;
import com.edu.agent.module.learning.service.StudyRecordService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/study/records")
@RequiredArgsConstructor
public class StudyRecordController {

    private final StudyRecordService studyRecordService;

    @PostMapping("/")
    public Result<Void> recordStudy(@RequestBody StudyRecordDTO dto) {
        // TODO phase 4 - get current userId from SecurityContext, call studyRecordService.recordStudy()
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @GetMapping("/")
    public Result<IPage<StudyRecordDTO>> listRecords(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        // TODO phase 4 - get current userId from SecurityContext, call studyRecordService.listRecords()
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @GetMapping("/stats")
    public Result<Map<String, Object>> getStudyStats() {
        // TODO phase 4 - get current userId from SecurityContext, call studyRecordService.getStudyStats()
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }
}

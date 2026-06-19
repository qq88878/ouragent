package com.edu.agent.module.learning.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edu.agent.common.result.Result;
import com.edu.agent.module.learning.dto.StudyRecordDTO;
import com.edu.agent.module.learning.service.StudyRecordService;
import com.edu.agent.security.LoginUser;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/study/records")
@PreAuthorize("hasRole('STUDENT')")
public class StudyRecordController {

    private final StudyRecordService studyRecordService;
    public StudyRecordController(StudyRecordService studyRecordService) {
        this.studyRecordService = studyRecordService;
    }

    @PostMapping("/")
    public Result<Void> recordStudy(@RequestBody StudyRecordDTO dto) {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        studyRecordService.recordStudy(loginUser.getUser().getId(), dto);
        return Result.success();
    }

    @GetMapping("/")
    public Result<IPage<StudyRecordDTO>> listRecords(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int size) {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return Result.success(studyRecordService.listRecords(loginUser.getUser().getId(), page, size));
    }

    @GetMapping("/stats")
    public Result<Map<String, Object>> getStudyStats() {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return Result.success(studyRecordService.getStudyStats(loginUser.getUser().getId()));
    }
}

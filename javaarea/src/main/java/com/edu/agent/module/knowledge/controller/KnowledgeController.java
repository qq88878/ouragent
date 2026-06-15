package com.edu.agent.module.knowledge.controller;

import com.edu.agent.common.result.Result;
import com.edu.agent.module.knowledge.dto.BatchApproveDTO;
import com.edu.agent.module.knowledge.dto.KnowledgeDTO;
import com.edu.agent.module.knowledge.dto.KnowledgeUploadDTO;
import com.edu.agent.module.knowledge.service.KnowledgeService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("/knowledge")
@RequiredArgsConstructor
public class KnowledgeController {

    private final KnowledgeService knowledgeService;

    @PostMapping(value = "/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public Result<KnowledgeDTO> upload(@RequestPart("file") MultipartFile file,
                                       @RequestParam(required = false) Long courseId,
                                       @RequestParam(required = false) String name,
                                       @RequestParam(required = false) String description) {
        if (file == null || file.isEmpty()) {
            return Result.fail(400, "No file selected or file is empty");
        }
        KnowledgeUploadDTO dto = new KnowledgeUploadDTO();
        dto.setCourseId(courseId);
        dto.setName(name);
        dto.setDescription(description);
        return Result.success(knowledgeService.uploadKnowledge(file, dto));
    }

    @GetMapping("/all")
    public Result<List<KnowledgeDTO>> listAll() {
        return Result.success(knowledgeService.listAll());
    }

    @GetMapping
    public Result<List<KnowledgeDTO>> list(@RequestParam(required = false) Long courseId) {
        return Result.success(knowledgeService.listByCourse(courseId));
    }

    @GetMapping("/{id}")
    public Result<KnowledgeDTO> getById(@PathVariable Long id) {
        return Result.success(knowledgeService.getKnowledgeById(id));
    }

    @PutMapping("/{id}/assign")
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public Result<Void> assignToCourse(@PathVariable Long id, @RequestParam(required = false) Long courseId) {
        knowledgeService.assignToCourse(id, courseId);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public Result<Void> delete(@PathVariable Long id) {
        knowledgeService.deleteKnowledge(id);
        return Result.success();
    }

    @PostMapping("/{id}/reprocess")
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public Result<Void> reprocess(@PathVariable Long id) {
        knowledgeService.reprocessKnowledge(id);
        return Result.success();
    }

    @GetMapping("/pending")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<List<KnowledgeDTO>> listPending() {
        return Result.success(knowledgeService.listByApprovalStatus("PENDING"));
    }

    @PostMapping("/{id}/approve")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<Void> approve(@PathVariable Long id,
                                @RequestParam boolean approved,
                                @RequestParam(required = false) String remark) {
        knowledgeService.approveKnowledge(id, approved, remark);
        return Result.success();
    }

    @PostMapping("/batch-approve")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<Void> batchApprove(@RequestBody BatchApproveDTO dto) {
        knowledgeService.batchApprove(dto);
        return Result.success();
    }
}
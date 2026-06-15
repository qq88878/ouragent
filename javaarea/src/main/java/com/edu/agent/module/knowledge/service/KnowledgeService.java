package com.edu.agent.module.knowledge.service;

import com.edu.agent.module.knowledge.dto.BatchApproveDTO;
import com.edu.agent.module.knowledge.dto.KnowledgeDTO;
import com.edu.agent.module.knowledge.dto.KnowledgeUploadDTO;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

public interface KnowledgeService {

    KnowledgeDTO uploadKnowledge(MultipartFile file, KnowledgeUploadDTO dto);

    KnowledgeDTO getKnowledgeById(Long id);

    List<KnowledgeDTO> listByCourse(Long courseId);

    List<KnowledgeDTO> listAll();

    List<KnowledgeDTO> listByApprovalStatus(String approvalStatus);

    void approveKnowledge(Long id, boolean approved, String remark);

    void batchApprove(BatchApproveDTO dto);

    void assignToCourse(Long knowledgeId, Long courseId);

    void deleteKnowledge(Long id);

    void reprocessKnowledge(Long id);
}
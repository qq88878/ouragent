package com.edu.agent.module.knowledge.service.impl;

import com.edu.agent.module.knowledge.dto.KnowledgeDTO;
import com.edu.agent.module.knowledge.dto.KnowledgeUploadDTO;
import com.edu.agent.module.knowledge.entity.KnowledgeBase;
import com.edu.agent.module.knowledge.mapper.KnowledgeMapper;
import com.edu.agent.module.knowledge.service.KnowledgeService;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@Slf4j
@Service
public class KnowledgeServiceImpl extends ServiceImpl<KnowledgeMapper, KnowledgeBase> implements KnowledgeService {

    @Override
    public KnowledgeDTO uploadKnowledge(MultipartFile file, KnowledgeUploadDTO dto) {
        // TODO phase 2: save file to storage, extract text content, create knowledge record with PENDING status,
        //  async call Agent service for vectorization, return DTO
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @Override
    public KnowledgeDTO getKnowledgeById(Long id) {
        // TODO phase 2: query by id, join uploader name, convert to DTO
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @Override
    public List<KnowledgeDTO> listByCourse(Long courseId) {
        // TODO phase 2: query by courseId, join uploader names, convert to DTO list
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @Override
    public void deleteKnowledge(Long id) {
        // TODO phase 2: verify permission, delete file from storage, delete record from DB
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @Override
    public void reprocessKnowledge(Long id) {
        // TODO phase 2: reset status to PENDING, call Agent service to re-vectorize the document
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }
}

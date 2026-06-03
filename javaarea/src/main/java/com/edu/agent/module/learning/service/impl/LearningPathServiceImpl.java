package com.edu.agent.module.learning.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.module.learning.dto.LearningPathDTO;
import com.edu.agent.module.learning.dto.LearningPathGenerateRequest;
import com.edu.agent.module.learning.entity.LearningPath;
import com.edu.agent.module.learning.mapper.LearningPathMapper;
import com.edu.agent.module.learning.service.LearningPathService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import com.edu.agent.module.chat.service.client.AgentServiceClient;

import java.util.List;

@Slf4j
@Service
public class LearningPathServiceImpl
        extends ServiceImpl<LearningPathMapper, LearningPath>
        implements LearningPathService {

    // TODO phase 4 - inject LearningPathStepMapper

    @Autowired
    private AgentServiceClient agentServiceClient;

    // TODO phase 4 - inject StudentProfileService

    @Override
    public LearningPathDTO generatePath(Long userId, LearningPathGenerateRequest request) {
        // TODO phase 4:
        //  1. Load student profile
        //  2. Load course knowledge
        //  3. Call AgentServiceClient.generateLearningPath()
        //  4. Parse response into LearningPath + Steps
        //  5. Persist path and steps to database
        //  6. Return LearningPathDTO
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @Override
    public List<LearningPathDTO> listPaths(Long userId) {
        // TODO phase 4 - query paths + steps, map to DTO list
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @Override
    public LearningPathDTO getPathById(Long pathId) {
        // TODO phase 4 - query path + steps by pathId, map to DTO
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @Override
    public void updateStepStatus(Long pathId, Long stepId, String status) {
        // TODO phase 4 - find step, update status, optionally update path completedSteps
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }

    @Override
    public void deletePath(Long pathId) {
        // TODO phase 4 - soft-delete path and its steps
        throw new UnsupportedOperationException("Not implemented yet - TODO phase 4");
    }
}

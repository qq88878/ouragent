package com.edu.agent.module.learning.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.module.learning.entity.StudentProfileHistory;
import com.edu.agent.module.learning.mapper.StudentProfileHistoryMapper;
import com.edu.agent.module.learning.service.ProfileHistoryService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ProfileHistoryServiceImpl
        extends ServiceImpl<StudentProfileHistoryMapper, StudentProfileHistory>
        implements ProfileHistoryService {
    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(ProfileHistoryServiceImpl.class);

    @Override
    public void saveHistory(Long userId, String profileJson, String changeSummary, String triggerSource) {
        // Get current version
        LambdaQueryWrapper<StudentProfileHistory> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StudentProfileHistory::getUserId, userId)
                .orderByDesc(StudentProfileHistory::getVersion)
                .last("limit 1");
        StudentProfileHistory latest = getOne(wrapper);
        int nextVersion = (latest != null) ? latest.getVersion() + 1 : 1;

        StudentProfileHistory history = new StudentProfileHistory();
        history.setUserId(userId);
        history.setProfileSnapshot(profileJson);
        history.setChangeSummary(changeSummary);
        history.setTriggerSource(triggerSource);
        history.setVersion(nextVersion);
        save(history);

        log.info("Profile history saved: userId={}, version={}, trigger={}", userId, nextVersion, triggerSource);
    }

    @Override
    public List<StudentProfileHistory> getHistory(Long userId, int limit) {
        LambdaQueryWrapper<StudentProfileHistory> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StudentProfileHistory::getUserId, userId)
                .orderByDesc(StudentProfileHistory::getVersion)
                .last("LIMIT " + limit);
        return list(wrapper);
    }
}

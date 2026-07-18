package com.edu.agent.module.learning.service;

import com.edu.agent.module.learning.entity.StudentProfileHistory;
import java.util.List;

public interface ProfileHistoryService {
    /** Save a profile history snapshot */
    void saveHistory(Long userId, String profileJson, String changeSummary, String triggerSource);

    /** Get history versions for a user */
    List<StudentProfileHistory> getHistory(Long userId, int limit);
}

package com.edu.agent.module.learning.service;

import com.edu.agent.module.learning.entity.StudentProfile;

import java.util.Map;

public interface StudentProfileService {

    /**
     * Get student profile by user ID.
     */
    StudentProfile getProfile(Long userId);

    /**
     * Update student profile.
     */
    void updateProfile(Long userId, StudentProfile profile);

    /**
     * Get radar chart data for student profile visualization.
     */
    Map<String, Object> getRadarData(Long userId);
}

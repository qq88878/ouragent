package com.edu.agent.module.learning.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.learning.entity.StudentProfile;
import com.edu.agent.module.learning.mapper.StudentProfileMapper;
import com.edu.agent.module.learning.service.StudentProfileService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.HashMap;
import java.util.Map;

@Slf4j
@Service
public class StudentProfileServiceImpl
        extends ServiceImpl<StudentProfileMapper, StudentProfile>
        implements StudentProfileService {

    @Override
    public StudentProfile getProfile(Long userId) {
        LambdaQueryWrapper<StudentProfile> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StudentProfile::getUserId, userId);
        StudentProfile profile = getOne(wrapper);
        if (profile == null) {
            profile = new StudentProfile();
            profile.setUserId(userId);
            profile.setLearningStyle("VISUAL");
            profile.setStrengths("");
            profile.setWeaknesses("");
            profile.setInterests("");
            profile.setGradeLevel("BEGINNER");
            save(profile);
        }
        return profile;
    }

    @Override
    @Transactional
    public void updateProfile(Long userId, StudentProfile profile) {
        LambdaQueryWrapper<StudentProfile> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StudentProfile::getUserId, userId);
        StudentProfile existing = getOne(wrapper);

        if (existing == null) {
            profile.setUserId(userId);
            save(profile);
        } else {
            if (profile.getLearningStyle() != null) {
                existing.setLearningStyle(profile.getLearningStyle());
            }
            if (profile.getStrengths() != null) {
                existing.setStrengths(profile.getStrengths());
            }
            if (profile.getWeaknesses() != null) {
                existing.setWeaknesses(profile.getWeaknesses());
            }
            if (profile.getInterests() != null) {
                existing.setInterests(profile.getInterests());
            }
            if (profile.getGradeLevel() != null) {
                existing.setGradeLevel(profile.getGradeLevel());
            }
            if (profile.getPreferences() != null) {
                existing.setPreferences(profile.getPreferences());
            }
            updateById(existing);
        }

        log.info("学生画像更新成功: userId={}", userId);
    }

    @Override
    public Map<String, Object> getRadarData(Long userId) {
        StudentProfile profile = getProfile(userId);

        Map<String, Object> radarData = new HashMap<>();
        radarData.put("learningStyle", profile.getLearningStyle());
        radarData.put("strengths", profile.getStrengths());
        radarData.put("weaknesses", profile.getWeaknesses());
        radarData.put("interests", profile.getInterests());
        radarData.put("gradeLevel", profile.getGradeLevel());

        // Build radar chart dimensions
        Map<String, Integer> dimensions = new HashMap<>();
        String strengths = profile.getStrengths() != null ? profile.getStrengths() : "";
        String weaknesses = profile.getWeaknesses() != null ? profile.getWeaknesses() : "";

        dimensions.put("理论知识", calculateDimension(strengths, weaknesses, "理论"));
        dimensions.put("实践能力", calculateDimension(strengths, weaknesses, "实践"));
        dimensions.put("问题解决", calculateDimension(strengths, weaknesses, "问题"));
        dimensions.put("创新思维", calculateDimension(strengths, weaknesses, "创新"));
        dimensions.put("协作能力", calculateDimension(strengths, weaknesses, "协作"));

        radarData.put("dimensions", dimensions);
        return radarData;
    }

    private int calculateDimension(String strengths, String weaknesses, String keyword) {
        int base = 60;
        if (strengths.contains(keyword)) {
            base += 20;
        }
        if (weaknesses.contains(keyword)) {
            base -= 20;
        }
        return Math.max(0, Math.min(100, base));
    }
}

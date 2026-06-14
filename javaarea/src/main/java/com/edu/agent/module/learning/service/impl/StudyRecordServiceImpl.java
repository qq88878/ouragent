package com.edu.agent.module.learning.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.module.course.entity.Course;
import com.edu.agent.module.course.entity.CourseEnrollment;
import com.edu.agent.module.course.mapper.CourseMapper;
import com.edu.agent.module.course.mapper.CourseEnrollmentMapper;
import com.edu.agent.module.learning.dto.StudyRecordDTO;
import com.edu.agent.module.learning.entity.StudyRecord;
import com.edu.agent.module.learning.mapper.StudyRecordMapper;
import com.edu.agent.module.learning.service.StudyRecordService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class StudyRecordServiceImpl
        extends ServiceImpl<StudyRecordMapper, StudyRecord>
        implements StudyRecordService {

    private final CourseMapper courseMapper;
    private final CourseEnrollmentMapper enrollmentMapper;

    @Override
    @Transactional
    public void recordStudy(Long userId, StudyRecordDTO dto) {
        StudyRecord record = new StudyRecord();
        record.setUserId(userId);
        record.setCourseId(dto.getCourseId());
        record.setSessionId(dto.getSessionId());
        record.setDuration(dto.getDuration());
        record.setInteractionCount(dto.getInteractionCount());
        record.setSummary(dto.getSummary());
        save(record);

        log.info("学习记录保存成功: userId={}, courseId={}", userId, dto.getCourseId());
    }

    @Override
    public IPage<StudyRecordDTO> listRecords(Long userId, int page, int size) {
        LambdaQueryWrapper<StudyRecord> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StudyRecord::getUserId, userId)
                .orderByDesc(StudyRecord::getCreateTime);

        Page<StudyRecord> pageParam = new Page<>(page, size);
        Page<StudyRecord> result = page(pageParam, wrapper);

        // Batch fetch courses to avoid N+1 queries
        Set<Long> courseIds = result.getRecords().stream()
                .map(StudyRecord::getCourseId)
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());
        Map<Long, String> courseNameMap = new HashMap<>();
        if (!courseIds.isEmpty()) {
            courseMapper.selectBatchIds(courseIds).forEach(
                    course -> courseNameMap.put(course.getId(), course.getTitle()));
        }

        return result.convert(record -> toDTO(record, courseNameMap));
    }

    @Override
    public Map<String, Object> getStudyStats(Long userId) {
        LambdaQueryWrapper<StudyRecord> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(StudyRecord::getUserId, userId);
        List<StudyRecord> records = list(wrapper);

        int totalDuration = records.stream()
                .mapToInt(r -> r.getDuration() != null ? r.getDuration() : 0)
                .sum();
        int totalInteractions = records.stream()
                .mapToInt(r -> r.getInteractionCount() != null ? r.getInteractionCount() : 0)
                .sum();

        Long courseCount = enrollmentMapper.selectCount(
                new LambdaQueryWrapper<CourseEnrollment>()
                        .eq(CourseEnrollment::getUserId, userId)
        );

        Map<String, Object> stats = new HashMap<>();
        stats.put("totalDuration", totalDuration);
        stats.put("totalDurationHours", Math.round(totalDuration / 3600.0 * 10) / 10.0);
        stats.put("totalInteractions", totalInteractions);
        stats.put("totalRecords", records.size());
        stats.put("courseCount", courseCount);
        return stats;
    }

    private StudyRecordDTO toDTO(StudyRecord record, Map<Long, String> courseNameMap) {
        StudyRecordDTO dto = new StudyRecordDTO();
        dto.setId(record.getId());
        dto.setCourseId(record.getCourseId());
        dto.setSessionId(record.getSessionId());
        dto.setDuration(record.getDuration());
        dto.setInteractionCount(record.getInteractionCount());
        dto.setSummary(record.getSummary());
        dto.setCreateTime(record.getCreateTime());
        dto.setCourseName(courseNameMap.get(record.getCourseId()));
        return dto;
    }
}

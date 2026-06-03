package com.edu.agent.module.course.service.impl;

import com.edu.agent.module.course.dto.CourseDTO;
import com.edu.agent.module.course.dto.CourseQueryDTO;
import com.edu.agent.module.course.entity.Course;
import com.edu.agent.module.course.mapper.CourseMapper;
import com.edu.agent.module.course.service.CourseService;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class CourseServiceImpl extends ServiceImpl<CourseMapper, Course> implements CourseService {

    @Override
    public Long createCourse(CourseDTO courseDTO) {
        // TODO phase 2: validate teacher role, convert DTO to entity, save to DB, return generated id
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @Override
    public CourseDTO getCourseById(Long id) {
        // TODO phase 2: query course by id, join teacher name, convert to DTO
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @Override
    public void updateCourse(Long id, CourseDTO courseDTO) {
        // TODO phase 2: verify ownership, update course fields, save
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @Override
    public void deleteCourse(Long id) {
        // TODO phase 2: verify permission, delete course
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @Override
    public IPage<CourseDTO> listCourses(CourseQueryDTO queryDTO) {
        // TODO phase 2: build query wrapper from filters, paginate, join teacher name
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @Override
    public void enrollCourse(Long courseId, Long userId) {
        // TODO phase 2: check course status, check duplicate enrollment, insert record, increment studentCount
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }
}

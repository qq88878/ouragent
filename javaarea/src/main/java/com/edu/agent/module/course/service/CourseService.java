package com.edu.agent.module.course.service;

import com.edu.agent.module.course.dto.CourseDTO;
import com.edu.agent.module.course.dto.CourseQueryDTO;
import com.baomidou.mybatisplus.core.metadata.IPage;

import java.util.List;

public interface CourseService {

    Long createCourse(CourseDTO courseDTO);

    CourseDTO getCourseById(Long id);

    void updateCourse(Long id, CourseDTO courseDTO);

    void deleteCourse(Long id);

    IPage<CourseDTO> listCourses(CourseQueryDTO queryDTO);

    void enrollCourse(Long courseId, Long userId);

    List<Long> getEnrolledCourseIds(Long userId);
}
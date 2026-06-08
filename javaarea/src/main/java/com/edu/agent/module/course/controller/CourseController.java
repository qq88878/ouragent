package com.edu.agent.module.course.controller;

import com.edu.agent.common.result.Result;
import com.edu.agent.module.course.dto.CourseDTO;
import com.edu.agent.module.course.dto.CourseQueryDTO;
import com.edu.agent.module.course.service.CourseService;
import com.baomidou.mybatisplus.core.metadata.IPage;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/courses")
@RequiredArgsConstructor
public class CourseController {

    private final CourseService courseService;

    // TODO phase 2: teacher role check
    @PostMapping
    public Result<Long> create(@RequestBody CourseDTO courseDTO) {
        // TODO phase 2: create course for current teacher
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @GetMapping
    public Result<IPage<CourseDTO>> list(CourseQueryDTO queryDTO) {
        // TODO phase 2: list courses with filters and pagination
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    @GetMapping("/{id}")
    public Result<CourseDTO> getById(@PathVariable Long id) {
        // TODO phase 2: get course detail by id
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    // TODO phase 2: verify teacher is owner
    @PutMapping("/{id}")
    public Result<Void> update(@PathVariable Long id, @RequestBody CourseDTO courseDTO) {
        // TODO phase 2: update course (teacher owner only)
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    // TODO phase 2: verify teacher is owner or admin
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        // TODO phase 2: delete course (teacher/admin only)
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }

    // TODO phase 2: student role check
    @PostMapping("/{id}/enroll")
    public Result<Void> enroll(@PathVariable Long id) {
        // TODO phase 2: enroll current student into course
        throw new UnsupportedOperationException("Not implemented yet - phase 2");
    }
}
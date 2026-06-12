package com.edu.agent.module.course.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edu.agent.common.result.Result;
import com.edu.agent.module.course.dto.CourseDTO;
import com.edu.agent.module.course.dto.CourseQueryDTO;
import com.edu.agent.module.course.service.CourseService;
import com.edu.agent.module.user.entity.User;
import com.edu.agent.security.LoginUser;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/courses")
@RequiredArgsConstructor
public class CourseController {

    private final CourseService courseService;

    @PostMapping
    public Result<Long> create(@RequestBody CourseDTO courseDTO) {
        Long courseId = courseService.createCourse(courseDTO);
        return Result.success(courseId);
    }

    @GetMapping
    public Result<IPage<CourseDTO>> list(CourseQueryDTO queryDTO) {
        return Result.success(courseService.listCourses(queryDTO));
    }

    @GetMapping("/{id}")
    public Result<CourseDTO> getById(@PathVariable Long id) {
        return Result.success(courseService.getCourseById(id));
    }

    @PutMapping("/{id}")
    public Result<Void> update(@PathVariable Long id, @RequestBody CourseDTO courseDTO) {
        courseService.updateCourse(id, courseDTO);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        courseService.deleteCourse(id);
        return Result.success();
    }

    @PostMapping("/{id}/enroll")
    public Result<Void> enroll(@PathVariable Long id) {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        courseService.enrollCourse(id, loginUser.getUser().getId());
        return Result.success();
    }
}

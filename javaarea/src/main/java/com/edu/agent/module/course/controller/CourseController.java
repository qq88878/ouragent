package com.edu.agent.module.course.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edu.agent.common.result.Result;
import com.edu.agent.module.course.dto.CourseDTO;
import com.edu.agent.module.course.dto.CourseQueryDTO;
import com.edu.agent.module.course.service.CourseService;
import com.edu.agent.security.LoginUser;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/courses")
public class CourseController {

    private final CourseService courseService;
    public CourseController(CourseService courseService) {
        this.courseService = courseService;
    }

    @PostMapping
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
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
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
    public Result<Void> update(@PathVariable Long id, @RequestBody CourseDTO courseDTO) {
        courseService.updateCourse(id, courseDTO);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    @PreAuthorize("hasAnyRole('TEACHER','ADMIN')")
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

    @GetMapping("/enrolled")
    @PreAuthorize("hasRole('STUDENT')")
    public Result<List<Long>> getEnrolled() {
        LoginUser loginUser = (LoginUser) SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        return Result.success(courseService.getEnrolledCourseIds(loginUser.getUser().getId()));
    }
}
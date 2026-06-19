package com.edu.agent.module.course.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.course.dto.CourseDTO;
import com.edu.agent.module.course.dto.CourseQueryDTO;
import com.edu.agent.module.course.entity.Course;
import com.edu.agent.module.course.entity.CourseEnrollment;
import com.edu.agent.module.course.mapper.CourseEnrollmentMapper;
import com.edu.agent.module.course.mapper.CourseMapper;
import com.edu.agent.module.course.service.CourseService;
import com.edu.agent.module.user.entity.User;
import com.edu.agent.module.user.mapper.UserMapper;
import com.edu.agent.security.LoginUser;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class CourseServiceImpl extends ServiceImpl<CourseMapper, Course> implements CourseService {
    private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(CourseServiceImpl.class);

    private final CourseEnrollmentMapper enrollmentMapper;
    private final UserMapper userMapper;
    public CourseServiceImpl(CourseEnrollmentMapper enrollmentMapper, UserMapper userMapper) {
        this.enrollmentMapper = enrollmentMapper;
        this.userMapper = userMapper;
    }

    @Override
    @Transactional
    public Long createCourse(CourseDTO courseDTO) {
        LoginUser loginUser = getCurrentLoginUser();
        if (!"TEACHER".equals(loginUser.getUser().getRole()) && !"ADMIN".equals(loginUser.getUser().getRole())) {
            throw new BizException(ResultCode.FORBIDDEN, "只有教师可以创建课程");
        }

        Course course = new Course();
        course.setTitle(courseDTO.getTitle());
        course.setDescription(courseDTO.getDescription());
        course.setCoverImage(courseDTO.getCoverImage());
        course.setTeacherId(loginUser.getUser().getId());
        course.setCategory(courseDTO.getCategory());
        course.setDifficulty(courseDTO.getDifficulty());
        course.setStatus(0); // draft by default
        save(course);

        log.info("课程创建成功: id={}, title={}", course.getId(), course.getTitle());
        return course.getId();
    }

    @Override
    public CourseDTO getCourseById(Long id) {
        Course course = getById(id);
        if (course == null) {
            throw new BizException(ResultCode.NOT_FOUND, "课程不存在");
        }
        return toDTO(course);
    }

    @Override
    @Transactional
    public void updateCourse(Long id, CourseDTO courseDTO) {
        Course course = getById(id);
        if (course == null) {
            throw new BizException(ResultCode.NOT_FOUND, "课程不存在");
        }

        LoginUser loginUser = getCurrentLoginUser();
        if (!course.getTeacherId().equals(loginUser.getUser().getId()) && !"ADMIN".equals(loginUser.getUser().getRole())) {
            throw new BizException(ResultCode.FORBIDDEN, "只能修改自己的课程");
        }

        if (courseDTO.getTitle() != null) {
            course.setTitle(courseDTO.getTitle());
        }
        if (courseDTO.getDescription() != null) {
            course.setDescription(courseDTO.getDescription());
        }
        if (courseDTO.getCoverImage() != null) {
            course.setCoverImage(courseDTO.getCoverImage());
        }
        if (courseDTO.getCategory() != null) {
            course.setCategory(courseDTO.getCategory());
        }
        if (courseDTO.getDifficulty() != null) {
            course.setDifficulty(courseDTO.getDifficulty());
        }
        if (courseDTO.getStatus() != null) {
            course.setStatus(courseDTO.getStatus());
        }
        updateById(course);

        log.info("课程更新成功: id={}", id);
    }

    @Override
    @Transactional
    public void deleteCourse(Long id) {
        Course course = getById(id);
        if (course == null) {
            throw new BizException(ResultCode.NOT_FOUND, "课程不存在");
        }

        LoginUser loginUser = getCurrentLoginUser();
        if (!course.getTeacherId().equals(loginUser.getUser().getId()) && !"ADMIN".equals(loginUser.getUser().getRole())) {
            throw new BizException(ResultCode.FORBIDDEN, "只能删除自己的课程");
        }

        removeById(id);
        log.info("课程删除成功: id={}", id);
    }

    @Override
    public IPage<CourseDTO> listCourses(CourseQueryDTO queryDTO) {
        LambdaQueryWrapper<Course> wrapper = new LambdaQueryWrapper<>();

        if (StringUtils.hasText(queryDTO.getCategory())) {
            wrapper.eq(Course::getCategory, queryDTO.getCategory());
        }
        if (StringUtils.hasText(queryDTO.getDifficulty())) {
            wrapper.eq(Course::getDifficulty, queryDTO.getDifficulty());
        }
        if (StringUtils.hasText(queryDTO.getKeyword())) {
            wrapper.and(w -> w.like(Course::getTitle, queryDTO.getKeyword())
                    .or()
                    .like(Course::getDescription, queryDTO.getKeyword()));
        }
        if (queryDTO.getTeacherId() != null) {
            wrapper.eq(Course::getTeacherId, queryDTO.getTeacherId());
        }
        wrapper.orderByDesc(Course::getCreateTime);

        Page<Course> pageParam = new Page<>(queryDTO.getPage(), queryDTO.getSize());
        Page<Course> result = page(pageParam, wrapper);
        return result.convert(this::toDTO);
    }

    @Override
    @Transactional
    public void enrollCourse(Long courseId, Long userId) {
        Course course = getById(courseId);
        if (course == null) {
            throw new BizException(ResultCode.NOT_FOUND, "课程不存在");
        }
        if (course.getStatus() != 1) {
            throw new BizException(ResultCode.BAD_REQUEST, "课程未发布，无法注册");
        }

        LambdaQueryWrapper<CourseEnrollment> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(CourseEnrollment::getCourseId, courseId)
                .eq(CourseEnrollment::getUserId, userId);
        if (enrollmentMapper.selectCount(wrapper) > 0) {
            throw new BizException(ResultCode.BAD_REQUEST, "已经注册过该课程");
        }

        CourseEnrollment enrollment = new CourseEnrollment();
        enrollment.setCourseId(courseId);
        enrollment.setUserId(userId);
        enrollmentMapper.insert(enrollment);

        log.info("课程注册成功: courseId={}, userId={}", courseId, userId);
    }

    @Override
    public List<Long> getEnrolledCourseIds(Long userId) {
        LambdaQueryWrapper<CourseEnrollment> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(CourseEnrollment::getUserId, userId);
        return enrollmentMapper.selectList(wrapper).stream()
                .map(CourseEnrollment::getCourseId)
                .collect(Collectors.toList());
    }

    private CourseDTO toDTO(Course course) {
        CourseDTO dto = new CourseDTO();
        dto.setId(course.getId());
        dto.setTitle(course.getTitle());
        dto.setDescription(course.getDescription());
        dto.setCoverImage(course.getCoverImage());
        dto.setTeacherId(course.getTeacherId());
        dto.setCategory(course.getCategory());
        dto.setDifficulty(course.getDifficulty());
        dto.setStatus(course.getStatus());
        dto.setCreateTime(course.getCreateTime());

        User teacher = userMapper.selectById(course.getTeacherId());
        if (teacher != null) {
            dto.setTeacherName(teacher.getNickname() != null ? teacher.getNickname() : teacher.getUsername());
        }

        return dto;
    }

    private LoginUser getCurrentLoginUser() {
        Object principal = SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        if (principal instanceof LoginUser loginUser) {
            return loginUser;
        }
        throw new BizException(ResultCode.UNAUTHORIZED, "未登录");
    }
}

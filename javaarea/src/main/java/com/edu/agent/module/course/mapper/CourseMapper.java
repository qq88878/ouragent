package com.edu.agent.module.course.mapper;

import com.edu.agent.module.course.entity.Course;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface CourseMapper extends BaseMapper<Course> {

    // TODO phase 2: select courses by teacher id
    List<Course> selectByTeacherId(@Param("teacherId") Long teacherId);

    // TODO phase 2: select courses by category
    List<Course> selectByCategory(@Param("category") String category);
}

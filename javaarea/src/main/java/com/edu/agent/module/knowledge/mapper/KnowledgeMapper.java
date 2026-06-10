package com.edu.agent.module.knowledge.mapper;

import com.edu.agent.module.knowledge.entity.KnowledgeBase;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface KnowledgeMapper extends BaseMapper<KnowledgeBase> {

    // TODO phase 2: select knowledge entries by course id
    List<KnowledgeBase> selectByCourseId(@Param("courseId") Long courseId);

    // TODO phase 2: select knowledge entries by status
    List<KnowledgeBase> selectByStatus(@Param("status") Integer status);
}

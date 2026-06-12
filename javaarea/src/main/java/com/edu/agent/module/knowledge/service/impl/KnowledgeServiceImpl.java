package com.edu.agent.module.knowledge.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.common.config.FileUploadConfig;
import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.course.entity.Course;
import com.edu.agent.module.course.mapper.CourseMapper;
import com.edu.agent.module.knowledge.dto.KnowledgeDTO;
import com.edu.agent.module.knowledge.dto.KnowledgeUploadDTO;
import com.edu.agent.module.knowledge.entity.KnowledgeBase;
import com.edu.agent.module.knowledge.mapper.KnowledgeMapper;
import com.edu.agent.module.knowledge.service.KnowledgeService;
import com.edu.agent.security.LoginUser;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class KnowledgeServiceImpl extends ServiceImpl<KnowledgeMapper, KnowledgeBase> implements KnowledgeService {

    private final FileUploadConfig fileUploadConfig;
    private final CourseMapper courseMapper;

    @Override
    @Transactional
    public KnowledgeDTO uploadKnowledge(MultipartFile file, KnowledgeUploadDTO dto) {
        LoginUser loginUser = getCurrentLoginUser();
        if (!"TEACHER".equals(loginUser.getUser().getRole()) && !"ADMIN".equals(loginUser.getUser().getRole())) {
            throw new BizException(ResultCode.FORBIDDEN, "只有教师可以上传知识库文件");
        }

        Course course = courseMapper.selectById(dto.getCourseId());
        if (course == null) {
            throw new BizException(ResultCode.NOT_FOUND, "课程不存在");
        }

        String originalFilename = file.getOriginalFilename();
        String fileType = getFileExtension(originalFilename);
        String storedFilename = UUID.randomUUID() + "." + fileType;

        String uploadDir = fileUploadConfig.getUploadPath() + "/knowledge";
        File dir = new File(uploadDir);
        if (!dir.exists()) {
            dir.mkdirs();
        }

        try {
            file.transferTo(new File(uploadDir + "/" + storedFilename));
        } catch (IOException e) {
            log.error("文件上传失败", e);
            throw new BizException(ResultCode.INTERNAL_ERROR, "文件上传失败");
        }

        KnowledgeBase knowledge = new KnowledgeBase();
        knowledge.setCourseId(dto.getCourseId());
        knowledge.setName(StringUtils.hasText(dto.getName()) ? dto.getName() : originalFilename);
        knowledge.setDescription(dto.getDescription());
        knowledge.setFilePath("/knowledge/" + storedFilename);
        knowledge.setFileType(fileType);
        knowledge.setFileSize(file.getSize());
        knowledge.setStatus(0); // pending
        save(knowledge);

        log.info("知识库文件上传成功: id={}, name={}", knowledge.getId(), knowledge.getName());
        return toDTO(knowledge);
    }

    @Override
    public KnowledgeDTO getKnowledgeById(Long id) {
        KnowledgeBase knowledge = getById(id);
        if (knowledge == null) {
            throw new BizException(ResultCode.NOT_FOUND, "知识库文件不存在");
        }
        return toDTO(knowledge);
    }

    @Override
    public List<KnowledgeDTO> listByCourse(Long courseId) {
        LambdaQueryWrapper<KnowledgeBase> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(KnowledgeBase::getCourseId, courseId)
                .orderByDesc(KnowledgeBase::getCreateTime);
        return list(wrapper).stream().map(this::toDTO).toList();
    }

    @Override
    @Transactional
    public void deleteKnowledge(Long id) {
        KnowledgeBase knowledge = getById(id);
        if (knowledge == null) {
            throw new BizException(ResultCode.NOT_FOUND, "知识库文件不存在");
        }

        LoginUser loginUser = getCurrentLoginUser();
        Course course = courseMapper.selectById(knowledge.getCourseId());
        if (course != null && !course.getTeacherId().equals(loginUser.getUser().getId())
                && !"ADMIN".equals(loginUser.getUser().getRole())) {
            throw new BizException(ResultCode.FORBIDDEN, "只能删除自己课程的知识库文件");
        }

        String filePath = fileUploadConfig.getUploadPath() + knowledge.getFilePath();
        File file = new File(filePath);
        if (file.exists()) {
            file.delete();
        }

        removeById(id);
        log.info("知识库文件删除成功: id={}", id);
    }

    @Override
    @Transactional
    public void reprocessKnowledge(Long id) {
        KnowledgeBase knowledge = getById(id);
        if (knowledge == null) {
            throw new BizException(ResultCode.NOT_FOUND, "知识库文件不存在");
        }

        knowledge.setStatus(0); // reset to pending
        updateById(knowledge);

        log.info("知识库文件重新处理: id={}", id);
    }

    private KnowledgeDTO toDTO(KnowledgeBase knowledge) {
        KnowledgeDTO dto = new KnowledgeDTO();
        dto.setId(knowledge.getId());
        dto.setCourseId(knowledge.getCourseId());
        dto.setName(knowledge.getName());
        dto.setDescription(knowledge.getDescription());
        dto.setFilePath(knowledge.getFilePath());
        dto.setFileType(knowledge.getFileType());
        dto.setFileSize(knowledge.getFileSize());
        dto.setStatus(knowledge.getStatus());
        dto.setCreateTime(knowledge.getCreateTime());
        return dto;
    }

    private String getFileExtension(String filename) {
        if (filename == null || !filename.contains(".")) {
            return "unknown";
        }
        return filename.substring(filename.lastIndexOf(".") + 1).toLowerCase();
    }

    private LoginUser getCurrentLoginUser() {
        Object principal = SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        if (principal instanceof LoginUser loginUser) {
            return loginUser;
        }
        throw new BizException(ResultCode.UNAUTHORIZED, "未登录");
    }
}

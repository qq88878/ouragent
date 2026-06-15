package com.edu.agent.module.knowledge.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.common.config.FileUploadConfig;
import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.chat.service.client.AgentServiceClient;
import com.edu.agent.module.course.entity.Course;
import com.edu.agent.module.course.mapper.CourseMapper;
import com.edu.agent.module.user.entity.User;
import com.edu.agent.module.user.mapper.UserMapper;
import com.edu.agent.module.knowledge.dto.BatchApproveDTO;
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
    private final UserMapper userMapper;
    private final AgentServiceClient agentServiceClient;

    @Override
    @Transactional
    public KnowledgeDTO uploadKnowledge(MultipartFile file, KnowledgeUploadDTO dto) {
        LoginUser loginUser = getCurrentLoginUser();
        if (!"TEACHER".equals(loginUser.getUser().getRole()) && !"ADMIN".equals(loginUser.getUser().getRole())) {
            throw new BizException(ResultCode.FORBIDDEN, "只有教师可以上传知识库文件");
        }

        if (dto.getCourseId() != null) {
            Course course = courseMapper.selectById(dto.getCourseId());
            if (course == null) {
                throw new BizException(ResultCode.NOT_FOUND, "课程不存在");
            }
            if (!course.getTeacherId().equals(loginUser.getUser().getId()) && !"ADMIN".equals(loginUser.getUser().getRole())) {
                throw new BizException(ResultCode.FORBIDDEN, "只能给自己创建的课程上传辅材");
            }
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
        knowledge.setUploadedBy(loginUser.getUser().getId());
        knowledge.setName(StringUtils.hasText(dto.getName()) ? dto.getName() : originalFilename);
        knowledge.setDescription(dto.getDescription());
        knowledge.setFilePath("/knowledge/" + storedFilename);
        knowledge.setFileType(fileType);
        knowledge.setFileSize(file.getSize());
        knowledge.setStatus(0); // pending vectorization
        // Teachers need admin approval, admins auto-approved
        knowledge.setApprovalStatus("ADMIN".equals(loginUser.getUser().getRole()) ? "APPROVED" : "PENDING");
        save(knowledge);

        // TODO: async vectorization via Python Agent (deferred)
        updateById(knowledge);

        log.info("知识库文件上传成功: id={}, name={}, status={}", knowledge.getId(), knowledge.getName(), knowledge.getStatus());
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
        LoginUser loginUser = getCurrentLoginUser();
        String role = loginUser.getUser().getRole();
        Long userId = loginUser.getUser().getId();

        LambdaQueryWrapper<KnowledgeBase> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(KnowledgeBase::getCourseId, courseId);

        // Filter by role
        if ("STUDENT".equals(role)) {
            wrapper.eq(KnowledgeBase::getApprovalStatus, "APPROVED");
        } else if ("TEACHER".equals(role)) {
            wrapper.eq(KnowledgeBase::getUploadedBy, userId);
        }
        // ADMIN sees all

        wrapper.orderByDesc(KnowledgeBase::getCreateTime);
        List<KnowledgeDTO> result = list(wrapper).stream().map(this::toDTO).toList();
        enrichCourseNames(result);
        return result;
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


    @Override
    public List<KnowledgeDTO> listAll() {
        LoginUser loginUser = getCurrentLoginUser();
        String role = loginUser.getUser().getRole();
        Long userId = loginUser.getUser().getId();

        LambdaQueryWrapper<KnowledgeBase> wrapper = new LambdaQueryWrapper<>();

        // Filter by role
        if ("STUDENT".equals(role)) {
            wrapper.eq(KnowledgeBase::getApprovalStatus, "APPROVED");
        } else if ("TEACHER".equals(role)) {
            wrapper.eq(KnowledgeBase::getUploadedBy, userId);
        }
        // ADMIN sees all

        wrapper.orderByDesc(KnowledgeBase::getCreateTime);
        List<KnowledgeDTO> result = list(wrapper).stream().map(this::toDTO).toList();
        enrichCourseNames(result);
        return result;
    }

    @Override
    public List<KnowledgeDTO> listByApprovalStatus(String approvalStatus) {
        LoginUser loginUser = getCurrentLoginUser();
        if (!"ADMIN".equals(loginUser.getUser().getRole())) {
            throw new BizException(ResultCode.FORBIDDEN, "只有管理员可以按审核状态查询");
        }

        LambdaQueryWrapper<KnowledgeBase> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(KnowledgeBase::getApprovalStatus, approvalStatus)
                .orderByDesc(KnowledgeBase::getCreateTime);
        List<KnowledgeDTO> result = list(wrapper).stream().map(this::toDTO).toList();
        enrichCourseNames(result);
        return result;
    }

    @Override
    @Transactional
    public void approveKnowledge(Long id, boolean approved, String remark) {
        LoginUser loginUser = getCurrentLoginUser();
        if (!"ADMIN".equals(loginUser.getUser().getRole())) {
            throw new BizException(ResultCode.FORBIDDEN, "只有管理员可以审核知识库文件");
        }

        KnowledgeBase knowledge = getById(id);
        if (knowledge == null) {
            throw new BizException(ResultCode.NOT_FOUND, "知识库文件不存在");
        }

        knowledge.setApprovalStatus(approved ? "APPROVED" : "REJECTED");
        knowledge.setApprovalRemark(remark);
        updateById(knowledge);
        log.info("知识库文件审核: id={}, approved={}, remark={}", id, approved, remark);
    }

    @Override
    @Transactional
    public void batchApprove(BatchApproveDTO dto) {
        LoginUser loginUser = getCurrentLoginUser();
        if (!"ADMIN".equals(loginUser.getUser().getRole())) {
            throw new BizException(ResultCode.FORBIDDEN, "只有管理员可以审核知识库文件");
        }

        if (dto.getIds() == null || dto.getIds().isEmpty()) {
            throw new BizException(ResultCode.BAD_REQUEST, "请选择要审核的文件");
        }

        for (Long id : dto.getIds()) {
            KnowledgeBase knowledge = getById(id);
            if (knowledge == null) {
                log.warn("知识库文件不存在，跳过: id={}", id);
                continue;
            }
            knowledge.setApprovalStatus(dto.isApproved() ? "APPROVED" : "REJECTED");
            knowledge.setApprovalRemark(dto.getRemark());
            updateById(knowledge);
        }
        log.info("批量审核完成: ids={}, approved={}", dto.getIds(), dto.isApproved());
    }
    @Override
    @Transactional
    public void assignToCourse(Long knowledgeId, Long courseId) {
        KnowledgeBase knowledge = getById(knowledgeId);
        if (knowledge == null) {
            throw new BizException(ResultCode.NOT_FOUND, "知识库文件不存在");
        }

        LoginUser loginUser = getCurrentLoginUser();

        if (courseId != null) {
            Course targetCourse = courseMapper.selectById(courseId);
            if (targetCourse == null) {
                throw new BizException(ResultCode.NOT_FOUND, "目标课程不存在");
            }
            if (!targetCourse.getTeacherId().equals(loginUser.getUser().getId()) && !"ADMIN".equals(loginUser.getUser().getRole())) {
                throw new BizException(ResultCode.FORBIDDEN, "只能给自己创建的课程关联辅材");
            }
        }

        // Use raw SQL SET to bypass MyBatis-Plus NOT_NULL field strategy
        LambdaUpdateWrapper<KnowledgeBase> wrapper = new LambdaUpdateWrapper<>();
        wrapper.eq(KnowledgeBase::getId, knowledgeId);
        if (courseId == null) {
            wrapper.setSql("course_id = NULL");
        } else {
            wrapper.set(KnowledgeBase::getCourseId, courseId);
        }
        update(wrapper);
        log.info("知识库文件关联更新: knowledgeId={}, courseId={}", knowledgeId, courseId);
    }

    private void enrichCourseNames(List<KnowledgeDTO> list) {
        if (list == null || list.isEmpty()) return;
        for (KnowledgeDTO dto : list) {
            if (dto.getCourseId() != null) {
                Course course = courseMapper.selectById(dto.getCourseId());
                if (course != null) {
                    dto.setCourseName(course.getTitle());
                }
            }
        }
    }

    private KnowledgeDTO toDTO(KnowledgeBase knowledge) {
        KnowledgeDTO dto = new KnowledgeDTO();
        dto.setId(knowledge.getId());
        dto.setCourseId(knowledge.getCourseId());
        dto.setUploadedBy(knowledge.getUploadedBy());
        dto.setName(knowledge.getName());
        dto.setDescription(knowledge.getDescription());
        dto.setFilePath(knowledge.getFilePath());
        dto.setFileType(knowledge.getFileType());
        dto.setFileSize(knowledge.getFileSize());
        dto.setStatus(knowledge.getStatus());
        dto.setApprovalStatus(knowledge.getApprovalStatus());
        dto.setApprovalRemark(knowledge.getApprovalRemark());
        dto.setCreateTime(knowledge.getCreateTime());

        // Get uploader name
        if (knowledge.getUploadedBy() != null) {
            var uploader = userMapper.selectById(knowledge.getUploadedBy());
            if (uploader != null) {
                dto.setUploadedByName(uploader.getNickname() != null ? uploader.getNickname() : uploader.getUsername());
            }
        }
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

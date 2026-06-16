package com.edu.agent.module.knowledge.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.common.config.FileUploadConfig;
import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.chat.dto.AgentIngestResponse;
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
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.*;
import java.util.stream.Collectors;

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
        // Teachers and admins auto-approved; approval workflow reserved for future use
        knowledge.setApprovalStatus("APPROVED");
        save(knowledge);

        // Trigger vectorization via Python Agent
        try {
            File savedFile = new File(uploadDir + "/" + storedFilename);
            AgentIngestResponse result = agentServiceClient.ingestKnowledgeFile(
                    knowledge.getId(), dto.getCourseId(), savedFile);
            Integer chunks = result.getChunks();
            if (chunks != null && chunks > 0) {
                knowledge.setStatus(1); // indexed
            } else {
                knowledge.setStatus(2); // vectorization failed (no chunks)
                log.warn("向量化返回0个分块: knowledgeId={}", knowledge.getId());
            }
        } catch (Exception e) {
            knowledge.setStatus(2); // vectorization failed
            log.error("向量化调用失败，文件已保存但未索引: knowledgeId={}", knowledge.getId(), e);
        }
        updateById(knowledge);

        log.info("知识库文件上传成功: id={}, name={}, status={}", knowledge.getId(), knowledge.getName(), knowledge.getStatus());
        // Build single-item maps for DTO enrichment
        Map<Long, Course> courseMap = new HashMap<>();
        if (dto.getCourseId() != null) {
            Course course = courseMapper.selectById(dto.getCourseId());
            if (course != null) courseMap.put(course.getId(), course);
        }
        Map<Long, User> userMap = new HashMap<>();
        userMap.put(loginUser.getUser().getId(), loginUser.getUser());
        return toDTO(knowledge, courseMap, userMap);
    }

    @Override
    public KnowledgeDTO getKnowledgeById(Long id) {
        KnowledgeBase knowledge = getById(id);
        if (knowledge == null) {
            throw new BizException(ResultCode.NOT_FOUND, "知识库文件不存在");
        }
        // Single-item: fetch course and uploader individually
        Map<Long, Course> courseMap = new HashMap<>();
        Map<Long, User> userMap = new HashMap<>();
        if (knowledge.getCourseId() != null) {
            Course course = courseMapper.selectById(knowledge.getCourseId());
            if (course != null) courseMap.put(course.getId(), course);
        }
        if (knowledge.getUploadedBy() != null) {
            User user = userMapper.selectById(knowledge.getUploadedBy());
            if (user != null) userMap.put(user.getId(), user);
        }
        return toDTO(knowledge, courseMap, userMap);
    }

    @Override
    public List<KnowledgeDTO> listByCourse(Long courseId) {
        LoginUser loginUser = getCurrentLoginUser();
        String role = loginUser.getUser().getRole();
        Long userId = loginUser.getUser().getId();

        LambdaQueryWrapper<KnowledgeBase> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(KnowledgeBase::getCourseId, courseId);

        if ("STUDENT".equals(role)) {
            wrapper.eq(KnowledgeBase::getApprovalStatus, "APPROVED");
        } else if ("TEACHER".equals(role)) {
            wrapper.eq(KnowledgeBase::getUploadedBy, userId);
        }

        wrapper.orderByDesc(KnowledgeBase::getCreateTime);
        List<KnowledgeBase> entities = list(wrapper);
        return toDTOList(entities);
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

        if ("STUDENT".equals(role)) {
            wrapper.eq(KnowledgeBase::getApprovalStatus, "APPROVED");
        } else if ("TEACHER".equals(role)) {
            wrapper.eq(KnowledgeBase::getUploadedBy, userId);
        }

        wrapper.orderByDesc(KnowledgeBase::getCreateTime);
        List<KnowledgeBase> entities = list(wrapper);
        return toDTOList(entities);
    }

    @Override
    public List<KnowledgeDTO> searchByName(String keyword) {
        LoginUser loginUser = getCurrentLoginUser();
        String role = loginUser.getUser().getRole();
        Long userId = loginUser.getUser().getId();

        LambdaQueryWrapper<KnowledgeBase> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(keyword)) {
            wrapper.like(KnowledgeBase::getName, keyword);
        }

        // Filter by role
        if ("STUDENT".equals(role)) {
            wrapper.eq(KnowledgeBase::getApprovalStatus, "APPROVED");
        } else if ("TEACHER".equals(role)) {
            wrapper.eq(KnowledgeBase::getUploadedBy, userId);
        }
        // ADMIN sees all

        wrapper.orderByDesc(KnowledgeBase::getCreateTime);
        List<KnowledgeBase> entities = list(wrapper);
        return toDTOList(entities);
    }

    private static final java.util.Set<String> TEXT_EXTENSIONS = java.util.Set.of(
        "txt", "md", "csv", "tsv", "json", "xml", "html", "htm", "css", "js", "ts",
        "py", "java", "kt", "c", "cpp", "h", "hpp", "go", "rs", "rb", "php", "sh", "bat",
        "yaml", "yml", "toml", "ini", "cfg", "conf", "properties", "sql", "log", "svg"
    );

    @Override
    public String getContent(Long id) {
        KnowledgeBase knowledge = getById(id);
        if (knowledge == null) {
            throw new BizException(ResultCode.NOT_FOUND, "知识库文件不存在");
        }

        String fileType = knowledge.getFileType();
        if (fileType == null || !TEXT_EXTENSIONS.contains(fileType.toLowerCase())) {
            return "[此文件类型（." + (fileType != null ? fileType : "unknown") + "）不支持在线预览，请下载后查看]";
        }

        String fullPath = fileUploadConfig.getUploadPath() + knowledge.getFilePath();
        java.io.File file = new java.io.File(fullPath);
        if (!file.exists()) {
            throw new BizException(ResultCode.NOT_FOUND, "文件内容不存在，可能已被删除");
        }
        try {
            return Files.readString(Paths.get(fullPath), StandardCharsets.UTF_8);
        } catch (IOException e) {
            try {
                byte[] bytes = Files.readAllBytes(Paths.get(fullPath));
                return new String(bytes, StandardCharsets.UTF_8);
            } catch (IOException ex) {
                throw new BizException(ResultCode.INTERNAL_ERROR, "无法读取文件内容");
            }
        }
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
        List<KnowledgeBase> entities = list(wrapper);
        return toDTOList(entities);
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

    private List<KnowledgeDTO> toDTOList(List<KnowledgeBase> entities) {
        if (entities == null || entities.isEmpty()) {
            return Collections.emptyList();
        }

        // Batch fetch courses
        Set<Long> courseIds = entities.stream()
                .map(KnowledgeBase::getCourseId)
                .filter(java.util.Objects::nonNull)
                .collect(Collectors.toSet());
        Map<Long, Course> courseMap = new HashMap<>();
        if (!courseIds.isEmpty()) {
            courseMapper.selectBatchIds(courseIds).forEach(c -> courseMap.put(c.getId(), c));
        }

        // Batch fetch uploaders
        Set<Long> userIds = entities.stream()
                .map(KnowledgeBase::getUploadedBy)
                .filter(java.util.Objects::nonNull)
                .collect(Collectors.toSet());
        Map<Long, User> userMap = new HashMap<>();
        if (!userIds.isEmpty()) {
            userMapper.selectBatchIds(userIds).forEach(u -> userMap.put(u.getId(), u));
        }

        return entities.stream()
                .map(e -> toDTO(e, courseMap, userMap))
                .toList();
    }

    private KnowledgeDTO toDTO(KnowledgeBase knowledge, Map<Long, Course> courseMap, Map<Long, User> userMap) {
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

        if (knowledge.getCourseId() != null && courseMap != null) {
            Course course = courseMap.get(knowledge.getCourseId());
            if (course != null) {
                dto.setCourseName(course.getTitle());
            }
        }

        if (knowledge.getUploadedBy() != null && userMap != null) {
            User uploader = userMap.get(knowledge.getUploadedBy());
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

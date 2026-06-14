package com.edu.agent.module.admin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.edu.agent.module.admin.dto.DashboardStatsDTO;
import com.edu.agent.module.admin.dto.SystemConfigDTO;
import com.edu.agent.module.admin.service.AdminService;
import com.edu.agent.module.chat.entity.ChatMessage;
import com.edu.agent.module.chat.mapper.ChatMessageMapper;
import com.edu.agent.module.chat.service.client.AgentServiceClient;
import com.edu.agent.module.course.mapper.CourseMapper;
import com.edu.agent.module.knowledge.mapper.KnowledgeMapper;
import com.edu.agent.module.user.entity.User;
import com.edu.agent.module.user.mapper.UserMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class AdminServiceImpl implements AdminService {

    private final UserMapper userMapper;
    private final CourseMapper courseMapper;
    private final ChatMessageMapper chatMessageMapper;
    private final KnowledgeMapper knowledgeMapper;
    private final AgentServiceClient agentServiceClient;
    private final StringRedisTemplate redisTemplate;

    @Override
    public DashboardStatsDTO getDashboardStats() {
        DashboardStatsDTO stats = new DashboardStatsDTO();

        // Total users
        long totalUsers = userMapper.selectCount(null);
        stats.setTotalUsers((int) totalUsers);

        // Teachers and students
        LambdaQueryWrapper<User> teacherWrapper = new LambdaQueryWrapper<>();
        teacherWrapper.eq(User::getRole, "TEACHER");
        long totalTeachers = userMapper.selectCount(teacherWrapper);
        stats.setTotalTeachers((int) totalTeachers);

        LambdaQueryWrapper<User> studentWrapper = new LambdaQueryWrapper<>();
        studentWrapper.eq(User::getRole, "STUDENT");
        long totalStudents = userMapper.selectCount(studentWrapper);
        stats.setTotalStudents((int) totalStudents);

        // Total courses
        long totalCourses = courseMapper.selectCount(null);
        stats.setTotalCourses((int) totalCourses);

        // Total conversations (messages)
        long totalMessages = chatMessageMapper.selectCount(null);
        stats.setTotalConversations(totalMessages);

        // Active students today
        LocalDateTime todayStart = LocalDateTime.of(LocalDate.now(), LocalTime.MIN);
        LambdaQueryWrapper<ChatMessage> todayWrapper = new LambdaQueryWrapper<>();
        todayWrapper.eq(ChatMessage::getRole, "USER")
                .ge(ChatMessage::getCreateTime, todayStart);
        long activeToday = chatMessageMapper.selectCount(todayWrapper);
        stats.setActiveStudentsToday((int) Math.min(activeToday, totalStudents));

        // Total knowledge items
        long totalKnowledge = knowledgeMapper.selectCount(null);
        stats.setTotalKnowledgeItems((int) totalKnowledge);

        return stats;
    }

    @Override
    public SystemConfigDTO getSystemHealth() {
        SystemConfigDTO health = new SystemConfigDTO();

        // Agent service health
        try {
            boolean agentHealthy = agentServiceClient.isHealthy();
            health.setAgentStatus(agentHealthy ? "healthy" : "unhealthy");
        } catch (Exception e) {
            health.setAgentStatus("unavailable");
        }
        health.setAgentUrl("http://agent-service:8000");

        // DB status (if we can query, it's healthy)
        try {
            userMapper.selectCount(null);
            health.setDbStatus("healthy");
        } catch (Exception e) {
            health.setDbStatus("unhealthy");
        }

        // Redis status
        try {
            redisTemplate.getConnectionFactory().getConnection().ping();
            health.setRedisStatus("healthy");
        } catch (Exception e) {
            health.setRedisStatus("unhealthy");
        }

        // Uptime
        health.setUptime("Running");

        return health;
    }
}

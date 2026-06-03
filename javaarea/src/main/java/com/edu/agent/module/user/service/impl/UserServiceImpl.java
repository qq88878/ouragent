package com.edu.agent.module.user.service.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.module.user.dto.UserDTO;
import com.edu.agent.module.user.entity.User;
import com.edu.agent.module.user.mapper.UserMapper;
import com.edu.agent.module.user.service.UserService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {

    // TODO: 注入 SecurityContextHolder 或 SecurityContextUtils

    @Override
    public UserDTO getUserById(Long id) {
        // TODO: 阶段一 - 根据ID查询用户
        // TODO: 阶段一 - 转换为UserDTO（排除密码字段）
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @Override
    public UserDTO getCurrentUser() {
        // TODO: 阶段一 - 从SecurityContext获取当前用户ID
        // TODO: 阶段一 - 调用getUserById获取用户信息
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @Override
    public void updateUser(Long id, UserDTO dto) {
        // TODO: 阶段一 - 验证用户存在
        // TODO: 阶段一 - 更新允许修改的字段（nickname, email, phone, avatar）
        // TODO: 阶段一 - 调用updateById保存
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @Override
    public IPage<UserDTO> listUsers(int page, int size) {
        // TODO: 阶段一 - 构建分页查询条件
        // TODO: 阶段一 - 执行分页查询
        // TODO: 阶段一 - 转换为UserDTO分页结果
        throw new UnsupportedOperationException("Not implemented yet");
    }

    @Override
    public void updateStatus(Long id, Integer status) {
        // TODO: 阶段一 - 验证用户存在
        // TODO: 阶段一 - 更新用户状态
        throw new UnsupportedOperationException("Not implemented yet");
    }
}

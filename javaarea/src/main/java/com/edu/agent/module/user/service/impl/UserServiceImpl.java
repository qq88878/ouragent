package com.edu.agent.module.user.service.impl;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.edu.agent.common.exception.BizException;
import com.edu.agent.common.result.ResultCode;
import com.edu.agent.module.user.dto.UserDTO;
import com.edu.agent.module.user.entity.User;
import com.edu.agent.module.user.mapper.UserMapper;
import com.edu.agent.module.user.service.UserService;
import com.edu.agent.security.LoginUser;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {

    @Override
    public UserDTO getUserById(Long id) {
        User user = getById(id);
        if (user == null) {
            throw new BizException(ResultCode.NOT_FOUND, "用户不存在");
        }
        return toDTO(user);
    }

    @Override
    public UserDTO getCurrentUser() {
        Long userId = getCurrentUserId();
        return getUserById(userId);
    }

    @Override
    public void updateUser(Long id, UserDTO dto) {
        User user = getById(id);
        if (user == null) {
            throw new BizException(ResultCode.NOT_FOUND, "用户不存在");
        }
        if (dto.getNickname() != null) {
            user.setNickname(dto.getNickname());
        }
        if (dto.getEmail() != null) {
            user.setEmail(dto.getEmail());
        }
        if (dto.getPhone() != null) {
            user.setPhone(dto.getPhone());
        }
        if (dto.getAvatar() != null) {
            user.setAvatar(dto.getAvatar());
        }
        updateById(user);
    }

    @Override
    public IPage<UserDTO> listUsers(int page, int size) {
        Page<User> pageParam = new Page<>(page, size);
        Page<User> result = page(pageParam);
        return result.convert(this::toDTO);
    }

    @Override
    public void updateStatus(Long id, Integer status) {
        User user = getById(id);
        if (user == null) {
            throw new BizException(ResultCode.NOT_FOUND, "用户不存在");
        }
        user.setStatus(status);
        updateById(user);
    }

    private UserDTO toDTO(User user) {
        UserDTO dto = new UserDTO();
        dto.setId(user.getId());
        dto.setUsername(user.getUsername());
        dto.setNickname(user.getNickname());
        dto.setEmail(user.getEmail());
        dto.setPhone(user.getPhone());
        dto.setAvatar(user.getAvatar());
        dto.setRole(user.getRole());
        dto.setStatus(user.getStatus());
        dto.setLastLoginTime(user.getLastLoginTime());
        return dto;
    }

    private Long getCurrentUserId() {
        Object principal = SecurityContextHolder.getContext().getAuthentication().getPrincipal();
        if (principal instanceof LoginUser loginUser) {
            return loginUser.getUser().getId();
        }
        throw new BizException(ResultCode.UNAUTHORIZED, "未登录");
    }
}
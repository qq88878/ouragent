package com.edu.agent.module.user.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edu.agent.module.user.dto.UserDTO;

public interface UserService {

    /**
     * 根据ID获取用户信息
     *
     * @param id 用户ID
     * @return 用户DTO
     */
    UserDTO getUserById(Long id);

    /**
     * 获取当前登录用户信息
     *
     * @return 用户DTO
     */
    UserDTO getCurrentUser();

    /**
     * 更新用户信息
     *
     * @param id   用户ID
     * @param dto  用户DTO
     */
    void updateUser(Long id, UserDTO dto);

    /**
     * 分页查询用户列表
     *
     * @param page 页码
     * @param size 每页大小
     * @return 分页结果
     */
    IPage<UserDTO> listUsers(int page, int size);

    /**
     * 更新用户状态（启用/禁用）
     *
     * @param id     用户ID
     * @param status 状态值
     */
    void updateStatus(Long id, Integer status);
}

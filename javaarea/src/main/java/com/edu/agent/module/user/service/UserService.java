package com.edu.agent.module.user.service;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.edu.agent.module.user.dto.UserDTO;

public interface UserService {

    UserDTO getUserById(Long id);

    UserDTO getCurrentUser();

    void updateUser(Long id, UserDTO dto);

    IPage<UserDTO> listUsers(int page, int size);

    void updateStatus(Long id, Integer status);

    void deleteUser(Long id);
}
package com.edu.agent.module.user.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.edu.agent.module.user.entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {

    /**
     * 根据用户名查询用户
     *
     * @param username 用户名
     * @return 用户实体
     */
    default User selectByUsername(String username) {
        // TODO: 阶段一 - 实现根据用户名查询
        throw new UnsupportedOperationException("Not implemented yet");
    }

    /**
     * 根据角色查询用户列表
     *
     * @param role 角色
     * @return 用户列表
     */
    default java.util.List<User> selectByRole(String role) {
        // TODO: 阶段一 - 实现根据角色查询
        throw new UnsupportedOperationException("Not implemented yet");
    }
}

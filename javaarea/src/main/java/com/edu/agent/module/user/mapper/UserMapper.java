package com.edu.agent.module.user.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.edu.agent.module.user.entity.User;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface UserMapper extends BaseMapper<User> {

    default User selectByUsername(String username) {
        return selectOne(new QueryWrapper<User>().eq("username", username));
    }

    default User selectByEmail(String email) {
        return selectOne(new QueryWrapper<User>().eq("email", email));
    }

    default List<User> selectByRole(String role) {
        return selectList(new QueryWrapper<User>().eq("role", role));
    }
}
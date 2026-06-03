package com.edu.agent.security;

import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

/**
 * UserDetailsService implementation that loads user from database.
 *
 * TODO [Phase 1]: Implement user loading
 *   1. Query UserMapper by username
 *   2. If user not found, throw UsernameNotFoundException
 *   3. Wrap User entity in LoginUser
 *   4. Return LoginUser (which implements UserDetails)
 */
@Slf4j
@Service
public class UserDetailsServiceImpl implements UserDetailsService {

    // TODO: Inject UserMapper once User entity and mapper are created
    // private final UserMapper userMapper;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        // TODO: Query user from database
        //   1. User user = userMapper.selectByUsername(username);
        //   2. if (user == null) throw new UsernameNotFoundException("User not found: " + username);
        //   3. return new LoginUser(user);

        log.debug("loadUserByUsername called for: {}", username);
        throw new UsernameNotFoundException("Not implemented yet: " + username);
    }
}

package com.edu.agent.security;

import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.Collections;

/**
 * UserDetails wrapper around the User entity for Spring Security.
 *
 * TODO: Replace Object user placeholder with actual User entity once created.
 */
public class LoginUser implements UserDetails {

    private static final long serialVersionUID = 1L;

    // TODO: Replace Object with actual User entity
    private final Object user;

    // TODO: Change constructor parameter type from Object to actual User entity
    public LoginUser(Object user) {
        this.user = user;
    }

    /**
     * Get authorities from user's role field.
     */
    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        // TODO: Extract role from user entity and return as SimpleGrantedAuthority
        //   e.g. return Collections.singletonList(new SimpleGrantedAuthority("ROLE_" + user.getRole()));
        return Collections.emptyList();
    }

    @Override
    public String getPassword() {
        // TODO: return user.getPassword();
        return null;
    }

    @Override
    public String getUsername() {
        // TODO: return user.getUsername();
        return null;
    }

    @Override
    public boolean isAccountNonExpired() {
        // TODO: Implement based on business logic if needed
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        // TODO: Implement based on business logic if needed
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        // TODO: Implement based on business logic if needed
        return true;
    }

    @Override
    public boolean isEnabled() {
        // TODO: Implement based on user status field if needed
        return true;
    }

    /**
     * Get the wrapped user entity.
     */
    // TODO: Change return type from Object to actual User entity
    public Object getUser() {
        return user;
    }
}

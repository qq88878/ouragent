package com.edu.agent.security;

import com.edu.agent.module.user.entity.User;
import com.edu.agent.module.user.mapper.UserMapper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtProvider jwtProvider;
    private final UserMapper userMapper;
    private final RedisTemplate<String, Object> redisTemplate;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {

        String token = extractToken(request);
        if (token == null) {
            filterChain.doFilter(request, response);
            return;
        }

        try {
            if (jwtProvider.isTokenExpired(token)) {
                filterChain.doFilter(request, response);
                return;
            }

            try {
                if (Boolean.TRUE.equals(redisTemplate.hasKey("blacklist:" + token))) {
                    filterChain.doFilter(request, response);
                    return;
                }
            } catch (Exception e) {
                log.debug("Redis unavailable, skipping blacklist check: {}", e.getMessage());
            }

            String username = jwtProvider.getUsernameFromToken(token);
            if (username == null) {
                filterChain.doFilter(request, response);
                return;
            }

            User user = userMapper.selectByUsername(username);
            if (user == null) {
                filterChain.doFilter(request, response);
                return;
            }

            LoginUser loginUser = new LoginUser(user);
            if (!loginUser.isEnabled()) {
                log.debug("User {} is disabled, rejecting request", username);
                response.setStatus(HttpServletResponse.SC_FORBIDDEN);
                response.setContentType("application/json;charset=UTF-8");
                response.getWriter().write("{\"code\":403,\"message\":\"账号已被禁用\"}");
                return;
            }

            UsernamePasswordAuthenticationToken authentication =
                    new UsernamePasswordAuthenticationToken(loginUser, null, loginUser.getAuthorities());
            authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));

            SecurityContextHolder.getContext().setAuthentication(authentication);
        } catch (Exception e) {
            log.debug("JWT auth failed: {}", e.getMessage());
        }

        filterChain.doFilter(request, response);
    }

    private String extractToken(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}
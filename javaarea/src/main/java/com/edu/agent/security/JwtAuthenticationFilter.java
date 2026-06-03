package com.edu.agent.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * JWT authentication filter that runs once per request.
 *
 * TODO [Phase 1]: Implement JWT verification
 *   1. Extract Bearer token from Authorization header
 *   2. Validate token (signature, expiration)
 *   3. Parse user info and roles from token claims
 *   4. Build UsernamePasswordAuthenticationToken and set SecurityContextHolder
 *   5. Call filterChain.doFilter to continue the chain
 */
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    // TODO: Inject JwtUtils / JwtService for token parsing and validation
    // private final JwtUtils jwtUtils;

    // TODO: Inject UserDetailsService for loading user details if needed
    // private final UserDetailsService userDetailsService;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {

        // TODO [Phase 1] - Implement JWT verification
        //   1. Get "Authorization" header from request
        //   2. Check if header starts with "Bearer "
        //   3. Extract token string (substring after "Bearer ")
        //   4. Call jwtUtils.validateToken(token)
        //   5. If valid, extract username and roles
        //   6. Build UsernamePasswordAuthenticationToken (with authorities)
        //   7. Set into SecurityContextHolder:
        //      SecurityContextHolder.getContext().setAuthentication(authToken)
        //   8. If token is invalid or missing, just continue (anonymous access)

        filterChain.doFilter(request, response);
    }
}

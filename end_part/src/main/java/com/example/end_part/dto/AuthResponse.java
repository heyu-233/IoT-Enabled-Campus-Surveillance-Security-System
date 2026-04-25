package com.example.end_part.dto;

import lombok.Data;

@Data
public class AuthResponse {
    private String token;
    private UserDto user;
}

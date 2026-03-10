package com.microservices.iam.dto.request;

import com.microservices.iam.entity.Role;
import lombok.Data;

@Data
public class AdminCreateUserRequest {
    private String orgName;
    private String contactEmail;
    private Role role;
}


package com.microservices.iam.dto.request;

import com.microservices.iam.entity.Role;
import jakarta.validation.constraints.Email;
import lombok.Data;

@Data
public class UpdateUserRequest {

    private String orgName;

    private Role role;

    private Boolean isActive;
}

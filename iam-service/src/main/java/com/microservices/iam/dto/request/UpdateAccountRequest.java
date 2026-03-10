package com.microservices.iam.dto.request;

import com.microservices.iam.entity.Role;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class UpdateAccountRequest {
    private String orgName;
    private String avatarUrl;
}

package com.microservices.market.dto.request;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.*;

import java.math.BigDecimal;
import java.util.UUID;

@Data
public class PortfolioRequestDTO {

    @NotNull
    private UUID userId;

    @NotBlank
    private String asset;

    @NotNull
    private BigDecimal quantity;

    @NotBlank
    private String unit;

    private BigDecimal entryPrice;

    @NotBlank
    private String currency;
}

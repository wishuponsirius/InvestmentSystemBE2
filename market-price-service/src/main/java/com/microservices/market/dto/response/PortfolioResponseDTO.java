package com.microservices.market.dto.response;

import lombok.*;

import java.math.BigDecimal;

@Data
@Builder
public class PortfolioResponseDTO {

    private String asset;

    private BigDecimal quantity;

    private String unit;

    private BigDecimal entryPrice;

    private String currency;
}

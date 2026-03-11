package com.microservices.market.dto.response;

import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@Builder
public class PriceResponseDTO {

    private LocalDateTime timestamp;

    private BigDecimal buyPrice;

    private BigDecimal sellPrice;

    private BigDecimal transferPrice;

    private BigDecimal spread;

}

package com.microservices.market.dto.reponse;


import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@Builder
public class ForexResponseDTO {

    private String currency;

    private BigDecimal buyPrice;

    private BigDecimal transferPrice;

    private BigDecimal sellPrice;

    private LocalDateTime timestamp;
}

package com.microservices.market.dto.response;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PremiumPriceResponseDTO {
    private Integer assetId;
    private String displayUnit;
    private BigDecimal vietnamBuyPrice;
    private BigDecimal globalBuyPrice;
    private BigDecimal premiumPrice;
    private LocalDateTime vietnamTimestamp;
    private LocalDateTime globalTimestamp;
}
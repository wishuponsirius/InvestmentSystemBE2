package com.microservices.market.entity;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "exchange_rates")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ExchangeRate {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "rate_id")
    private Integer rateId;

    @ManyToOne
    @JoinColumn(name = "currency_code", nullable = false)
    private Currency currency;

    @Column(name = "buy_price", precision = 20, scale = 6)
    private BigDecimal buyPrice;

    @Column(name = "transfer_price", precision = 20, scale = 6)
    private BigDecimal transferPrice;

    @Column(name = "sell_price", precision = 20, scale = 6)
    private BigDecimal sellPrice;

    @ManyToOne
    @JoinColumn(name = "source_id")
    private DataSource source;

    @ManyToOne
    @JoinColumn(name = "base_currency_code")
    private Currency baseCurrency;

    @Column(name = "timestamp")
    private LocalDateTime timestamp;
}

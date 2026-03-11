package com.microservices.market.entity;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;

@Entity
@Table(name = "unit_conversion")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UnitConversion {

    @EmbeddedId
    private UnitConversionId id;

    @ManyToOne
    @MapsId("fromUnitId")
    @JoinColumn(name = "from_unit_id")
    private Unit fromUnit;

    @ManyToOne
    @MapsId("toUnitId")
    @JoinColumn(name = "to_unit_id")
    private Unit toUnit;

    @Column(nullable = false, precision = 20, scale = 10)
    private BigDecimal factor;
}

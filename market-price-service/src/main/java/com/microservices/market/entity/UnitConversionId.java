package com.microservices.market.entity;

import jakarta.persistence.*;
import lombok.*;

import java.io.Serializable;

@Embeddable
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
public class UnitConversionId implements Serializable {

    @Column(name = "from_unit_id")
    private Integer fromUnitId;

    @Column(name = "to_unit_id")
    private Integer toUnitId;
}
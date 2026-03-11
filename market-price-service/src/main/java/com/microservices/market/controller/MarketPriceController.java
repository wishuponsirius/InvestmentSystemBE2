package com.microservices.market.controller;

import com.microservices.market.dto.reponse.ForexResponseDTO;
import com.microservices.market.dto.reponse.PriceResponseDTO;
import com.microservices.market.service.ForexService;
import com.microservices.market.service.MarketPriceService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/prices")
@RequiredArgsConstructor
@Tag(
        name = "Market Prices",
        description = "Retrieve historical market prices for assets such as gold and silver across regions."
)
public class MarketPriceController {

    private final MarketPriceService service;
    private final ForexService ForexService;

    @Operation(
            summary = "Get market prices",
            description = """
                    Returns historical market prices for a specific asset and region.
                    
                    Supported Regions:
                    - VN-ALL: Vietnam market
                    - GLOBAL: Global market
                    
                    Supported Assets:
                    - GOLD
                    - SILVER
                    
                    Supported Time Ranges:
                    - 1d : Last 24 hours
                    - 1w : Last 7 days
                    - 1m : Last 30 days
                    - 1y : Last 1 year
                    - all : Entire available dataset
                    """
    )
    @GetMapping("/{region}/{asset}/{range}")
    public List<PriceResponseDTO> getPrices(

            @Parameter(
                    description = "Region of the market",
                    example = "vn-all"
            )
            @PathVariable String region,

            @Parameter(
                    description = "Asset type",
                    example = "gold"
            )
            @PathVariable String asset,

            @Parameter(
                    description = "Time range filter",
                    example = "1w"
            )
            @PathVariable String range
    ) {
        return service.getPrices(region, asset, range);
    }

    @Operation(
            summary = "Get forex prices",
            description = """
                    Retrieve historical foreign exchange rates against VND.
            
                    Supported currencies:
                    AUD, CAD, CHF, CNY, DKK, EUR, GBP, HKD, INR, JPY,
                    KRW, KWD, MYR, NOK, RUB, SEK, SGD, THB, USD
            
                    Note:
                    - VND is the base currency
                    
                    Supported Time Ranges:
                    - 1d : Last 24 hours
                    - 1w : Last 7 days
                    - 1m : Last 30 days
                    - 1y : Last 1 year
                    - all : Entire available dataset
                    """
    )
    @GetMapping("/{currency}/{range}")
    public List<ForexResponseDTO> getRates(
            @PathVariable String currency,
            @PathVariable String range
    ) {
        return ForexService.getRates(currency, range);
    }
}
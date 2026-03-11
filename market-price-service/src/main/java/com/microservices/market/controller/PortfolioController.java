package com.microservices.market.controller;
import com.microservices.market.dto.request.PortfolioRequestDTO;
import com.microservices.market.dto.response.ApiResponse;
import com.microservices.market.dto.response.PortfolioResponseDTO;
import com.microservices.market.service.PortfolioService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/portfolio")
@RequiredArgsConstructor
@Tag(name = "Portfolio", description = "User asset portfolio tracking")
public class PortfolioController {

    private final PortfolioService service;

    @Operation(summary = "Get user portfolio")
    @GetMapping("/{userId}")
    public List<PortfolioResponseDTO> getPortfolio(
            @PathVariable UUID userId
    ) {
        return service.getPortfolio(userId);
    }

    @Operation(summary = "Add or update asset in portfolio",
            description = """
                    Retrieve historical foreign exchange rates against VND.
                    
                    Supported assets: Gold, Silver, Forex (currencies list is the same as below)
                    
                    Supported Units: Lượng, Chỉ, Gram, Troy Ounce, Tael, Kilogram, Currency Unit
            
                    Supported currencies:
                    AUD, CAD, CHF, CNY, DKK, EUR, GBP, HKD, INR, JPY,
                    KRW, KWD, MYR, NOK, RUB, SEK, SGD, THB, USD
            
                    
                    """
    )
    @PostMapping
    public PortfolioResponseDTO addAsset(
            @Valid @RequestBody PortfolioRequestDTO request
    ) {
        return service.addOrUpdate(request);
    }

    @Operation(summary = "Delete asset from portfolio")
    @DeleteMapping("/{userId}/{asset}")
    public ResponseEntity<ApiResponse> deleteAsset(
            @PathVariable UUID userId,
            @PathVariable String asset
    ) {

        String message = service.deleteAsset(userId, asset);

        return ResponseEntity.ok(new ApiResponse(message));
    }
}

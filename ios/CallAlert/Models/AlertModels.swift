import Foundation

struct CallAlertsResponse: Codable, Sendable {
    let generatedAt: String
    let date: String
    let disclaimer: String
    let criteria: AlertCriteria
    let universeSize: Int
    let alertsCount: Int
    let alerts: [CallAlert]
    let nextPollSeconds: Int
    let demo: Bool?

    enum CodingKeys: String, CodingKey {
        case generatedAt = "generated_at"
        case date
        case disclaimer
        case criteria
        case universeSize = "universe_size"
        case alertsCount = "alerts_count"
        case alerts
        case nextPollSeconds = "next_poll_seconds"
        case demo
    }
}

struct AlertCriteria: Codable, Sendable {
    let minPremium: Double?
    let maxPremium: Double?
    let minDte: Int?
    let maxDte: Int?
    let monthlyExpiry: Bool?
    let otmOnly: Bool?
    let bullish150Ma: Bool?

    enum CodingKeys: String, CodingKey {
        case minPremium = "min_premium"
        case maxPremium = "max_premium"
        case minDte = "min_dte"
        case maxDte = "max_dte"
        case monthlyExpiry = "monthly_expiry"
        case otmOnly = "otm_only"
        case bullish150Ma = "bullish_150_ma"
    }
}

struct CallAlert: Codable, Identifiable, Hashable, Sendable {
    let ticker: String
    let underlyingPrice: Double
    let contractSymbol: String
    let strike: Double
    let expiry: String
    let daysToExpiry: Int
    let bid: Double
    let ask: Double
    let lastPrice: Double
    let midPrice: Double
    let volume: Int
    let openInterest: Int
    let impliedVolatility: Double
    let pctOtm: Double
    let spreadPct: Double
    let underlyingSignal: String
    let underlyingScore: Double
    let reason: String
    let score: Double
    let action: String

    var id: String { contractSymbol.isEmpty ? "\(ticker)-\(strike)-\(expiry)" : contractSymbol }

    enum CodingKeys: String, CodingKey {
        case ticker
        case underlyingPrice = "underlying_price"
        case contractSymbol = "contract_symbol"
        case strike
        case expiry
        case daysToExpiry = "days_to_expiry"
        case bid
        case ask
        case lastPrice = "last_price"
        case midPrice = "mid_price"
        case volume
        case openInterest = "open_interest"
        case impliedVolatility = "implied_volatility"
        case pctOtm = "pct_otm"
        case spreadPct = "spread_pct"
        case underlyingSignal = "underlying_signal"
        case underlyingScore = "underlying_score"
        case reason
        case score
        case action
    }

    var headline: String {
        let strikeText = String(format: "%.2f", strike)
        return "\(action.replacingOccurrences(of: "_", with: " ")) \(ticker) $\(strikeText) \(expiry)"
    }

    var premiumLabel: String {
        String(format: "$%.2f mid", midPrice)
    }
}

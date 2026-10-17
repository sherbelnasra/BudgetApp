import SwiftUI

struct AlertDetailView: View {
    let alert: CallAlert

    var body: some View {
        List {
            Section("Action") {
                LabeledContent("Signal", value: alert.action.replacingOccurrences(of: "_", with: " "))
                LabeledContent("Contract", value: alert.contractSymbol)
                LabeledContent("Score", value: String(format: "%.2f", alert.score))
            }
            Section("Contract") {
                LabeledContent("Underlying", value: String(format: "$%.2f", alert.underlyingPrice))
                LabeledContent("Strike", value: String(format: "$%.2f", alert.strike))
                LabeledContent("Expiry", value: "\(alert.expiry) (\(alert.daysToExpiry)d)")
                LabeledContent("% OTM", value: String(format: "%.1f%%", alert.pctOtm))
            }
            Section("Pricing") {
                LabeledContent("Bid", value: String(format: "$%.2f", alert.bid))
                LabeledContent("Ask", value: String(format: "$%.2f", alert.ask))
                LabeledContent("Last", value: String(format: "$%.2f", alert.lastPrice))
                LabeledContent("Mid", value: String(format: "$%.2f", alert.midPrice))
                LabeledContent("Spread", value: String(format: "%.1f%%", alert.spreadPct))
                LabeledContent("IV", value: String(format: "%.1f%%", alert.impliedVolatility * 100))
            }
            Section("Liquidity") {
                LabeledContent("Volume", value: "\(alert.volume)")
                LabeledContent("Open interest", value: "\(alert.openInterest)")
            }
            Section("Why this alert") {
                Text(alert.reason)
                Text(alert.underlyingSignal)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle(alert.ticker)
        .navigationBarTitleDisplayMode(.inline)
    }
}

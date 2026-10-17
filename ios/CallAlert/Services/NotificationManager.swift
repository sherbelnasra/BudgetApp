import Foundation
import UserNotifications

actor NotificationManager {
    static let shared = NotificationManager()

    private let defaultsKey = "notified_contract_symbols"

    func requestAuthorization() async {
        let center = UNUserNotificationCenter.current()
        _ = try? await center.requestAuthorization(options: [.alert, .sound, .badge])
    }

    func notifyNewAlerts(_ alerts: [CallAlert]) async {
        guard !alerts.isEmpty else { return }

        let defaults = UserDefaults.standard
        var seen = Set(defaults.stringArray(forKey: defaultsKey) ?? [])
        let center = UNUserNotificationCenter.current()

        for alert in alerts where !seen.contains(alert.id) {
            let content = UNMutableNotificationContent()
            content.title = "Buy call: \(alert.ticker)"
            content.subtitle = alert.premiumLabel
            content.body = "\(alert.contractSymbol) · strike \(String(format: "%.2f", alert.strike)) · expires \(alert.expiry). \(alert.reason)"
            content.sound = .default

            let request = UNNotificationRequest(
                identifier: alert.id,
                content: content,
                trigger: nil
            )
            try? await center.add(request)
            seen.insert(alert.id)
        }

        // Keep the set bounded.
        if seen.count > 200 {
            seen = Set(seen.suffix(100))
        }
        defaults.set(Array(seen), forKey: defaultsKey)
    }

    func clearHistory() {
        UserDefaults.standard.removeObject(forKey: defaultsKey)
    }
}

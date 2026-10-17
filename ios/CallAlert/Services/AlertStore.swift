import Foundation
import Combine

@MainActor
final class AlertStore: ObservableObject {
    @Published private(set) var alerts: [CallAlert] = []
    @Published private(set) var disclaimer: String = ""
    @Published private(set) var generatedAt: String = ""
    @Published private(set) var isLoading = false
    @Published private(set) var lastError: String?
    @Published private(set) var isDemo = false

    @Published var baseURLString: String {
        didSet { UserDefaults.standard.set(baseURLString, forKey: "api_base_url") }
    }
    @Published var useDemoData: Bool {
        didSet { UserDefaults.standard.set(useDemoData, forKey: "use_demo_data") }
    }
    @Published var notificationsEnabled: Bool {
        didSet { UserDefaults.standard.set(notificationsEnabled, forKey: "notifications_enabled") }
    }

    private var pollTask: Task<Void, Never>?
    private var pollSeconds: Int = 300

    init() {
        self.baseURLString = UserDefaults.standard.string(forKey: "api_base_url")
            ?? "http://127.0.0.1:8000"
        self.useDemoData = UserDefaults.standard.object(forKey: "use_demo_data") as? Bool ?? true
        self.notificationsEnabled = UserDefaults.standard.object(forKey: "notifications_enabled") as? Bool ?? true
    }

    func refresh(force: Bool = false) async {
        if isLoading && !force { return }
        isLoading = true
        lastError = nil
        defer { isLoading = false }

        guard let baseURL = URL(string: baseURLString) else {
            lastError = "Invalid API URL"
            return
        }

        do {
            let response = try await APIClient.shared.fetchAlerts(
                baseURL: baseURL,
                useDemo: useDemoData
            )
            alerts = response.alerts
            disclaimer = response.disclaimer
            generatedAt = response.generatedAt
            isDemo = response.demo ?? useDemoData
            pollSeconds = max(60, response.nextPollSeconds)

            if notificationsEnabled {
                await NotificationManager.shared.notifyNewAlerts(response.alerts)
            }
            restartPolling()
        } catch {
            lastError = error.localizedDescription
        }
    }

    func restartPolling() {
        pollTask?.cancel()
        let seconds = pollSeconds
        pollTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: UInt64(seconds) * 1_000_000_000)
                guard !Task.isCancelled else { break }
                await self?.refresh()
            }
        }
    }

    func stopPolling() {
        pollTask?.cancel()
        pollTask = nil
    }
}

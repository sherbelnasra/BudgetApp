import SwiftUI

struct SettingsView: View {
    @EnvironmentObject private var store: AlertStore
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField("API base URL", text: $store.baseURLString)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .keyboardType(.URL)
                    Toggle("Use demo data", isOn: $store.useDemoData)
                    Toggle("Buy alerts (local notifications)", isOn: $store.notificationsEnabled)
                } header: {
                    Text("Connection")
                } footer: {
                    Text("Point the app at your Mac/PC running the CallAlert API (uvicorn). On a physical iPhone use your computer’s LAN IP, e.g. http://192.168.1.20:8000, and allow local networking.")
                }

                Section("Premium band") {
                    LabeledContent("Min", value: "$0.15")
                    LabeledContent("Max", value: "$0.20")
                    LabeledContent("Expiry", value: "Next monthly (3rd Friday)")
                }

                Section {
                    Button("Clear notified history") {
                        Task { await NotificationManager.shared.clearHistory() }
                    }
                } footer: {
                    Text("Clears which contracts already triggered a notification so the same alert can fire again.")
                }
            }
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        Task {
                            await store.refresh(force: true)
                            dismiss()
                        }
                    }
                }
            }
        }
    }
}

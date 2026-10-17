import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var store: AlertStore
    @State private var showSettings = false

    var body: some View {
        NavigationStack {
            ZStack {
                background
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        hero
                        if let error = store.lastError {
                            Text(error)
                                .font(.footnote)
                                .foregroundStyle(Color(red: 0.77, green: 0.36, blue: 0.15))
                        }
                        if store.alerts.isEmpty && !store.isLoading {
                            emptyState
                        } else {
                            LazyVStack(spacing: 14) {
                                ForEach(store.alerts) { alert in
                                    NavigationLink(value: alert) {
                                        AlertRow(alert: alert)
                                    }
                                    .buttonStyle(.plain)
                                }
                            }
                        }
                        if !store.disclaimer.isEmpty {
                            Text(store.disclaimer)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .padding(.top, 8)
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.vertical, 16)
                }
            }
            .navigationTitle("CallAlert")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button {
                        showSettings = true
                    } label: {
                        Image(systemName: "gearshape")
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        Task { await store.refresh(force: true) }
                    } label: {
                        if store.isLoading {
                            ProgressView()
                        } else {
                            Image(systemName: "arrow.clockwise")
                        }
                    }
                    .disabled(store.isLoading)
                }
            }
            .navigationDestination(for: CallAlert.self) { alert in
                AlertDetailView(alert: alert)
            }
            .sheet(isPresented: $showSettings) {
                SettingsView()
                    .environmentObject(store)
            }
        }
    }

    private var background: some View {
        LinearGradient(
            colors: [
                Color(red: 0.85, green: 0.95, blue: 0.90),
                Color(red: 0.93, green: 0.95, blue: 0.94),
                Color(red: 0.95, green: 0.90, blue: 0.85),
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
    }

    private var hero: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("CallAlert")
                .font(.system(size: 36, weight: .bold, design: .rounded))
                .foregroundStyle(Color(red: 0.06, green: 0.10, blue: 0.08))
            Text("Monthly OTM calls priced $0.15–$0.20 when the underlying clears a rising 150-day MA.")
                .font(.system(.body, design: .rounded))
                .foregroundStyle(.secondary)
            HStack(spacing: 8) {
                Tag(text: store.isDemo ? "DEMO" : "LIVE")
                if !store.generatedAt.isEmpty {
                    Tag(text: String(store.generatedAt.prefix(19)))
                }
            }
        }
        .padding(.top, 8)
    }

    private var emptyState: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("No alerts right now")
                .font(.headline)
            Text("No monthly calls in the $0.15–$0.20 band matched the bullish filter. Pull to refresh or open Settings to use demo data.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 24)
    }
}

private struct Tag: View {
    let text: String
    var body: some View {
        Text(text)
            .font(.system(.caption2, design: .monospaced).weight(.semibold))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .overlay(
                Rectangle()
                    .stroke(Color.black.opacity(0.12), lineWidth: 1)
            )
    }
}

struct AlertRow: View {
    let alert: CallAlert

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .firstTextBaseline) {
                Text(alert.ticker)
                    .font(.system(.title3, design: .rounded).weight(.bold))
                Spacer()
                Text(alert.premiumLabel)
                    .font(.system(.body, design: .monospaced).weight(.semibold))
                    .foregroundStyle(Color(red: 0.12, green: 0.66, blue: 0.48))
            }
            Text("Strike $\(String(format: "%.2f", alert.strike)) · Exp \(alert.expiry) · \(alert.daysToExpiry)d")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Text(alert.reason)
                .font(.footnote)
                .foregroundStyle(.secondary)
                .lineLimit(2)
        }
        .padding(.vertical, 14)
        .padding(.horizontal, 4)
        .overlay(alignment: .top) {
            Rectangle()
                .fill(Color(red: 0.12, green: 0.66, blue: 0.48))
                .frame(height: 2)
        }
    }
}

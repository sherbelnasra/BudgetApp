import Foundation

enum APIClientError: LocalizedError {
    case invalidURL
    case badStatus(Int)
    case decoding(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API base URL."
        case .badStatus(let code):
            return "Server returned HTTP \(code)."
        case .decoding(let error):
            return "Could not decode alerts: \(error.localizedDescription)"
        }
    }
}

actor APIClient {
    static let shared = APIClient()

    func fetchAlerts(baseURL: URL, useDemo: Bool, topN: Int = 10) async throws -> CallAlertsResponse {
        var components = URLComponents(
            url: baseURL.appending(path: useDemo ? "v1/call-alerts/demo" : "v1/call-alerts"),
            resolvingAgainstBaseURL: false
        )
        if !useDemo {
            components?.queryItems = [
                URLQueryItem(name: "top_n", value: String(topN)),
                URLQueryItem(name: "min_premium", value: "0.15"),
                URLQueryItem(name: "max_premium", value: "0.20"),
            ]
        }
        guard let url = components?.url else { throw APIClientError.invalidURL }

        var request = URLRequest(url: url)
        request.timeoutInterval = 120
        request.setValue("application/json", forHTTPHeaderField: "Accept")

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw APIClientError.badStatus(-1)
        }
        guard (200..<300).contains(http.statusCode) else {
            throw APIClientError.badStatus(http.statusCode)
        }

        do {
            return try JSONDecoder().decode(CallAlertsResponse.self, from: data)
        } catch {
            throw APIClientError.decoding(error)
        }
    }
}

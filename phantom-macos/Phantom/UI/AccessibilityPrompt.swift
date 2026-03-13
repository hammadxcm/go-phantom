// AccessibilityPrompt.swift — AXIsProcessTrusted() + guidance

import AppKit
import ApplicationServices
import SwiftUI

enum AccessibilityPrompt {
    /// Check if the app has Accessibility permissions.
    static var isTrusted: Bool {
        AXIsProcessTrusted()
    }

    /// Check with prompt — shows system dialog to grant permission.
    static func checkWithPrompt() -> Bool {
        let options = [kAXTrustedCheckOptionPrompt.takeUnretainedValue(): true] as CFDictionary
        return AXIsProcessTrustedWithOptions(options)
    }

    /// Open System Settings > Privacy > Accessibility.
    static func openAccessibilitySettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility") {
            NSWorkspace.shared.open(url)
        }
    }
}

struct AccessibilityAlertView: View {
    @State private var isChecking = false

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "hand.raised.circle.fill")
                .font(.system(size: 48))
                .foregroundStyle(.orange)

            Text("Accessibility Permission Required")
                .font(.headline)

            Text("Phantom needs Accessibility access to simulate mouse movements, keyboard presses, and other input events.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)

            Button("Open System Settings") {
                AccessibilityPrompt.openAccessibilitySettings()
            }
            .buttonStyle(.borderedProminent)
        }
        .padding(24)
        .frame(width: 360)
    }
}

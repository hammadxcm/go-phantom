// MouseSimulator.swift — CGEvent .mouseMoved + Bezier paths

import CoreGraphics
import Foundation
import os.log

private let logger = Logger(subsystem: "com.phantom.app", category: "MouseSimulator")

final class MouseSimulator: Simulator {
    let name = "mouse"

    func execute(config: PhantomConfig) {
        let mouseConfig = config.mouse
        let mainDisplay = CGMainDisplayID()
        let screenWidth = CGDisplayPixelsWide(mainDisplay)
        let screenHeight = CGDisplayPixelsHigh(mainDisplay)

        // Get current mouse position
        let currentEvent = CGEvent(source: nil)
        let currentPos = currentEvent?.location ?? CGPoint.zero
        let currentX = Int(currentPos.x)
        let currentY = Int(currentPos.y)

        // Generate random target within max_distance bounds
        var targetX = currentX + Int.random(in: -mouseConfig.maxDistance...mouseConfig.maxDistance)
        var targetY = currentY + Int.random(in: -mouseConfig.maxDistance...mouseConfig.maxDistance)

        // Clamp to screen
        targetX = clamp(targetX, lo: 0, hi: screenWidth - 1)
        targetY = clamp(targetY, lo: 0, hi: screenHeight - 1)

        // Ensure minimum distance
        let dx = targetX - currentX
        let dy = targetY - currentY
        if abs(dx) + abs(dy) < mouseConfig.minDistance {
            let signX = dx >= 0 ? 1 : -1
            let signY = dy >= 0 ? 1 : -1
            targetX = clamp(currentX + signX * mouseConfig.minDistance, lo: 0, hi: screenWidth - 1)
            targetY = clamp(currentY + signY * mouseConfig.minDistance, lo: 0, hi: screenHeight - 1)
        }

        let start: Point = (Double(currentX), Double(currentY))
        let end: Point = (Double(targetX), Double(targetY))
        let path = Randomizer.bezierPath(start: start, end: end, steps: mouseConfig.bezierSteps)

        // Move along path
        for point in path {
            let cgPoint = CGPoint(x: point.x, y: point.y)
            if let event = CGEvent(mouseEventSource: nil, mouseType: .mouseMoved,
                                   mouseCursorPosition: cgPoint, mouseButton: .left) {
                event.post(tap: .cghidEventTap)
            }
            usleep(UInt32(Randomizer.stepDelay() * 1_000_000))
        }

        // Micro-correction: subtle drift after arriving (30% chance)
        if Double.random(in: 0..<1) < 0.3 {
            var jitterX = targetX + Int.random(in: -2...2)
            var jitterY = targetY + Int.random(in: -2...2)
            jitterX = clamp(jitterX, lo: 0, hi: screenWidth - 1)
            jitterY = clamp(jitterY, lo: 0, hi: screenHeight - 1)

            usleep(UInt32(Double.random(in: 0.08...0.20) * 1_000_000))

            let correctionSteps = 8
            var cx = Double(targetX)
            var cy = Double(targetY)
            let stepDx = Double(jitterX - targetX) / Double(correctionSteps)
            let stepDy = Double(jitterY - targetY) / Double(correctionSteps)

            for _ in 0..<correctionSteps {
                cx += stepDx
                cy += stepDy
                let cgPoint = CGPoint(x: cx, y: cy)
                if let event = CGEvent(mouseEventSource: nil, mouseType: .mouseMoved,
                                       mouseCursorPosition: cgPoint, mouseButton: .left) {
                    event.post(tap: .cghidEventTap)
                }
                usleep(UInt32(Double.random(in: 0.010...0.025) * 1_000_000))
            }
        }

        logger.debug("Mouse moved to (\(targetX), \(targetY))")
    }

    private func clamp(_ value: Int, lo: Int, hi: Int) -> Int {
        return max(lo, min(hi, value))
    }
}

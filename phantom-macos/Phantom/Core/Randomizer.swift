// Randomizer.swift — Exact port of phantom/core/randomization.py

import Foundation

typealias Point = (x: Double, y: Double)

enum Randomizer {
    // Mouse path constants
    static let controlPointOffsetMin: Double = 0.05
    static let controlPointOffsetMax: Double = 0.20
    static let noiseSigmaMin: Double = 0.3
    static let noiseSigmaMax: Double = 1.0

    // Timing constants
    static let defaultIntervalMean: Double = 8.0
    static let defaultIntervalStddev: Double = 4.0
    static let defaultIntervalMin: Double = 0.5
    static let idleChance: Double = 0.10
    static let idleMin: Double = 15.0
    static let idleMax: Double = 120.0

    // Keystroke constants
    static let keystrokeBaseMin: Double = 0.05
    static let keystrokeBaseMax: Double = 0.20
    static let thinkingPauseChance: Double = 0.05
    static let thinkingPauseMin: Double = 0.30
    static let thinkingPauseMax: Double = 0.80

    // MARK: - Bezier

    /// Evaluate a cubic Bezier curve at parameter t.
    static func bezierPoint(t: Double, p0: Point, p1: Point, p2: Point, p3: Point) -> Point {
        let u = 1.0 - t
        let x = u*u*u * p0.x + 3*u*u*t * p1.x + 3*u*t*t * p2.x + t*t*t * p3.x
        let y = u*u*u * p0.y + 3*u*u*t * p1.y + 3*u*t*t * p2.y + t*t*t * p3.y
        return (x, y)
    }

    /// Generate a control point offset perpendicular to the line.
    static func perpendicularOffset(start: Point, end: Point, fraction: Double) -> Point {
        let dx = end.x - start.x
        let dy = end.y - start.y
        let dist = max(hypot(dx, dy), 1.0)
        let sign: Double = Bool.random() ? 1.0 : -1.0
        let offset = dist * fraction * sign
        let px = -dy / dist * offset
        let py = dx / dist * offset
        return (px, py)
    }

    /// Generate two random control points for a cubic Bezier.
    static func bezierControlPoints(start: Point, end: Point) -> (Point, Point) {
        let cp1Frac = Double.random(in: controlPointOffsetMin...controlPointOffsetMax)
        let cp2Frac = Double.random(in: controlPointOffsetMin...controlPointOffsetMax)

        let off1 = perpendicularOffset(start: start, end: end, fraction: cp1Frac)
        let off2 = perpendicularOffset(start: start, end: end, fraction: cp2Frac)

        let t1 = Double.random(in: 0.2...0.4)
        let t2 = Double.random(in: 0.6...0.8)
        let mid1 = (start.x + (end.x - start.x) * t1, start.y + (end.y - start.y) * t1)
        let mid2 = (start.x + (end.x - start.x) * t2, start.y + (end.y - start.y) * t2)

        let cp1 = (mid1.0 + off1.x, mid1.1 + off1.y)
        let cp2 = (mid2.0 + off2.x, mid2.1 + off2.y)
        return (cp1, cp2)
    }

    /// Smooth ease-in-out curve.
    static func easeInOut(_ t: Double) -> Double {
        return t * t * (3.0 - 2.0 * t)
    }

    /// Generate a human-like Bezier mouse path from start to end.
    static func bezierPath(start: Point, end: Point, steps: Int = 50) -> [Point] {
        let (cp1, cp2) = bezierControlPoints(start: start, end: end)
        let sigma = Double.random(in: noiseSigmaMin...noiseSigmaMax)
        var path: [Point] = []

        for i in 0...steps {
            let t = easeInOut(Double(i) / Double(steps))
            var (x, y) = bezierPoint(t: t, p0: start, p1: cp1, p2: cp2, p3: end)

            // Light noise in the middle of the path only, fade near endpoints
            if i > 0 && i < steps {
                let fade = 1.0 - abs(2.0 * Double(i) / Double(steps) - 1.0)
                x += gaussianRandom(mean: 0, stddev: sigma * fade)
                y += gaussianRandom(mean: 0, stddev: sigma * fade)
            }
            path.append((x.rounded(), y.rounded()))
        }
        return path
    }

    // MARK: - Timing

    /// Return a gaussian-distributed action interval in seconds.
    static func actionInterval(
        mean: Double = defaultIntervalMean,
        stddev: Double = defaultIntervalStddev,
        minimum: Double = defaultIntervalMin
    ) -> Double {
        return max(minimum, gaussianRandom(mean: mean, stddev: stddev))
    }

    /// Decide whether to enter an idle pause.
    static func shouldIdle() -> Bool {
        return Double.random(in: 0..<1) < idleChance
    }

    /// Return an exponential-distributed idle duration.
    static func idleDuration() -> Double {
        let raw = -30.0 * log(Double.random(in: 0..<1))  // expovariate(1/30)
        return max(idleMin, min(idleMax, raw + idleMin))
    }

    /// Return a human-like delay between keystrokes.
    static func keystrokeDelay() -> Double {
        var base = Double.random(in: keystrokeBaseMin...keystrokeBaseMax)
        if Double.random(in: 0..<1) < thinkingPauseChance {
            base += Double.random(in: thinkingPauseMin...thinkingPauseMax)
        }
        return base
    }

    /// Return the delay between individual mouse movement steps (8-25ms).
    static func stepDelay() -> Double {
        return Double.random(in: 0.008...0.025)
    }

    /// Perform a weighted random selection.
    static func weightedChoice(options: [(String, Double)]) -> String {
        let totalWeight = options.reduce(0) { $0 + $1.1 }
        var roll = Double.random(in: 0..<totalWeight)
        for (name, weight) in options {
            roll -= weight
            if roll <= 0 { return name }
        }
        return options.last!.0
    }

    // MARK: - Gaussian

    /// Box-Muller transform for gaussian random numbers.
    static func gaussianRandom(mean: Double = 0, stddev: Double = 1) -> Double {
        let u1 = Double.random(in: Double.leastNormalMagnitude..<1)
        let u2 = Double.random(in: 0..<1)
        let z = sqrt(-2.0 * log(u1)) * cos(2.0 * .pi * u2)
        return mean + stddev * z
    }
}

# Template only — not a tap. The published formula lives in
# hammadxcm/homebrew-tap and is generated with real checksums by the
# publish-homebrew job in .github/workflows/release.yml.
#
# Install with: brew install hammadxcm/tap/phantom
class Phantom < Formula
  desc "Cross-platform activity simulator"
  homepage "https://github.com/hammadxcm/go-phantom"
  version "0.0.0"
  license "MIT"

  # ponytail: ships the release binary instead of a source venv — no resource
  # blocks to keep in sync. Switch back to virtualenv_install_with_resources
  # only if a formula-audit rule ever requires building from source.
  on_macos do
    on_arm do
      url "https://github.com/hammadxcm/go-phantom/releases/download/v0.0.0/phantom-macos-arm64"
      sha256 "0000000000000000000000000000000000000000000000000000000000000000"
    end
  end

  on_linux do
    on_intel do
      url "https://github.com/hammadxcm/go-phantom/releases/download/v0.0.0/phantom-linux-x86_64"
      sha256 "0000000000000000000000000000000000000000000000000000000000000000"
    end
  end

  def install
    bin.install Dir["phantom-*"].first => "phantom"
  end

  test do
    assert_match "phantom", shell_output("#{bin}/phantom --help")
  end
end

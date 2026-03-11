class Phantom < Formula
  include Language::Python::Virtualenv

  desc "Cross-platform activity simulator"
  homepage "https://github.com/hammadxcm/go-phantom"
  url "https://github.com/hammadxcm/go-phantom/archive/refs/tags/v0.0.1.tar.gz"
  sha256 "PLACEHOLDER_SHA256"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "phantom", shell_output("#{bin}/phantom --help")
  end
end

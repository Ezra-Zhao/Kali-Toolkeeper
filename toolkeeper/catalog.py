"""Catalog: which packages are security tools, their categories, binaries, profiles.

TODO(ezra): expand this catalog. Kali ships 600+ tools; this is a curated
starter set (~45). A good next step is generating it from the
kali-tools-* metapackage dependencies on a live Kali box.
"""
from __future__ import annotations

# Category -> package names. Keep alphabetical inside each list.
TOOL_CATEGORIES: dict[str, list[str]] = {
    "recon": [
        "amass",
        "masscan",
        "nmap",
        "recon-ng",
        "theharvester",
    ],
    "web": [
        "burpsuite",
        "dirb",
        "gobuster",
        "nikto",
        "sqlmap",
        "whatweb",
        "wpscan",
    ],
    "wireless": [
        "aircrack-ng",
        "reaver",
        "wifite",
    ],
    "forensics": [
        "autopsy",
        "binwalk",
        "foremost",
        "volatility3",
    ],
    "exploitation": [
        "metasploit-framework",
        "beef-xss",
        "exploitdb",
    ],
    "password": [
        "hashcat",
        "hydra",
        "john",
    ],
    "sniffing": [
        "wireshark",
        "tcpdump",
        "ettercap-graphical",
        "dsniff",
    ],
}

# Reverse lookup: package -> category.
PACKAGE_CATEGORY: dict[str, str] = {
    pkg: category for category, pkgs in TOOL_CATEGORIES.items() for pkg in pkgs
}

# Package -> binary name when it differs from the package name.
BINARY_FOR: dict[str, str] = {
    "metasploit-framework": "msfconsole",
    "theharvester": "theHarvester",
    "volatility3": "vol",
    "john": "john",
}


def categorize(package_name: str) -> str:
    """Category for a package; 'other' for uncatalogued packages."""
    return PACKAGE_CATEGORY.get(package_name, "other")


def binary_for(package_name: str) -> str:
    """Binary to probe with `<binary> --version`."""
    return BINARY_FOR.get(package_name, package_name)


# Install profiles: named bundles for one-command setup/teardown.
PROFILES: dict[str, list[str]] = {
    "top10": [
        "nmap",
        "metasploit-framework",
        "burpsuite",
        "wireshark",
        "aircrack-ng",
        "hydra",
        "john",
        "sqlmap",
        "nikto",
        "theharvester",
    ],
    "web": [
        "burpsuite",
        "dirb",
        "gobuster",
        "nikto",
        "sqlmap",
        "whatweb",
        "wpscan",
    ],
    "wireless": [
        "aircrack-ng",
        "reaver",
        "wifite",
    ],
    "forensics": [
        "autopsy",
        "binwalk",
        "foremost",
        "volatility3",
    ],
    "recon": [
        "amass",
        "masscan",
        "nmap",
        "recon-ng",
        "theharvester",
    ],
    "password": [
        "hashcat",
        "hydra",
        "john",
    ],
}


def list_profiles() -> list[str]:
    return sorted(PROFILES)


def get_profile(name: str) -> list[str] | None:
    return PROFILES.get(name)

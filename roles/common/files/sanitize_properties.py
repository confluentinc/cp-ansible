#!/usr/bin/env python
"""
Confluent Platform Property File Sanitizer

Sanitizes sensitive data from configuration files while preserving
non-sensitive metadata like paths, algorithms, and timeout values.
"""

import re
import sys
import argparse
from pathlib import Path


class PropertySanitizer:
    """Sanitizes Confluent Platform configuration files."""

    # ===== Unified Sensitive Pattern Registry =====
    # Core sensitive keywords - single source of truth for all file types
    CORE_SENSITIVE_KEYWORDS = ['password', 'secret', 'key', 'token', 'credential']

    # Exact match patterns (confluent-specific and high-priority)
    EXACT_SENSITIVE = {
        'confluent.license',
        'ldap.java.naming.security.credentials',
        'confluent.security.master.key',
        'CONFLUENT_SECURITY_MASTER_KEY',
    }

    # Additional property-specific suffixes beyond core keywords
    ADDITIONAL_PROPERTY_SUFFIXES = [
        '.basic.auth.user.info',
        '.basic.auth.credentials',
        '.sasl.jaas.config',
        '.client.secret',
        'keystorePassword',  # Jolokia format
    ]

    # Ansible-specific sensitive variables
    ANSIBLE_SENSITIVE_VARS = [
        'ansible_ssh_private_key_file',
        'ansible_password',
        'ansible_become_password',
        'ansible_ssh_pass',
        'ansible_become_pass',
    ]

    # Properties that should NOT be sanitized (even if they match sensitive patterns)
    EXCLUDE_PATTERNS = [
        r'.*\.path$',                           # File paths
        r'.*\.location$',                       # File locations
        r'.*\.algorithm$',                      # Algorithm names (RS256, etc.)
        r'.*\.provider$',                       # Provider types (BASIC, BEARER)
        r'.*\.lifetime\.ms$',                   # Timeout values
        r'.*\.max\.lifetime\.ms$',              # Max lifetime values
        r'.*\.interval\.ms$',                   # Interval values
        r'.*\.authentication\.method$',         # Auth method types
        r'.*\.security\.protocol$',             # Security protocols
        r'.*\.mechanism$',                      # SASL mechanisms
        r'.*\.enabled\.mechanisms$',            # Enabled mechanisms list
        r'.*\.service\.name$',                  # Kerberos service names
        r'.*\.protocol\.map$',                  # Protocol mappings
    ]

    def __init__(self):
        self.exclude_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in self.EXCLUDE_PATTERNS]

    def is_excluded(self, key):
        """Check if a property key should be excluded from sanitization."""
        return any(pattern.match(key) for pattern in self.exclude_compiled)

    def is_sensitive(self, key):
        """Determine if a property key contains sensitive data."""
        # Check exact matches first
        if key in self.EXACT_SENSITIVE:
            return True

        # Check if excluded (takes precedence)
        if self.is_excluded(key):
            return False

        key_lower = key.lower()

        # Check core keywords as suffixes (e.g., .password, .secret, .key, .token)
        for keyword in self.CORE_SENSITIVE_KEYWORDS:
            if key_lower.endswith(f'.{keyword}'):
                return True

        # Check additional property-specific suffixes
        for suffix in self.ADDITIONAL_PROPERTY_SUFFIXES:
            if key_lower.endswith(suffix.lower()):
                return True

        return False

    def _sanitize_file_base(self, file_path, line_processor, item_type, in_place=True):
        """
        Base method for sanitizing files with common I/O logic.

        Args:
            file_path: Path to the file to sanitize
            line_processor: Function(line) -> (processed_line, was_sanitized)
            item_type: Description of items being sanitized (for logging)
            in_place: If True, modify file in place; if False, return sanitized content

        Returns:
            Sanitized content string if in_place=False, else None
        """
        path = Path(file_path)
        if not path.exists():
            print(f"Warning: File not found: {file_path}", file=sys.stderr)
            return None

        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.readlines()

        lines = []
        sanitized_count = 0

        # Add sanitization header
        lines.append("# THIS FILE HAS BEEN SANITIZED - SENSITIVE VALUES REDACTED\n")

        for line in content:
            # Skip existing sanitization headers
            if 'THIS FILE HAS BEEN SANITIZED' in line:
                continue

            # Process line using the provided processor
            processed_line, was_sanitized = line_processor(line)
            lines.append(processed_line)
            if was_sanitized:
                sanitized_count += 1

        sanitized_content = ''.join(lines)

        if in_place:
            # Write back to file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(sanitized_content)
            print(f"Sanitized {sanitized_count} {item_type} in {file_path}")
            return None
        else:
            # Return content for dry-run
            return sanitized_content

    def sanitize_properties_file(self, file_path, in_place=True):
        """
        Sanitize a .properties file.

        Args:
            file_path: Path to the properties file
            in_place: If True, modify file in place; if False, return sanitized content

        Returns:
            Sanitized content if in_place=False, else None
        """
        def process_properties_line(line):
            """Process a single line from a .properties file."""
            # Preserve comments and empty lines
            if line.strip().startswith('#') or not line.strip():
                return line, False

            # Parse property line (key=value format)
            match = re.match(r'^([^=]+)=(.*)', line)
            if not match:
                return line, False

            key = match.group(1).strip()

            # Check if this property should be sanitized
            if self.is_sensitive(key):
                return f"{key}=***REDACTED***\n", True

            return line, False

        return self._sanitize_file_base(file_path, process_properties_line, "properties", in_place)

    def sanitize_override_file(self, file_path, in_place=True):
        """
        Sanitize a systemd override.conf file.

        Args:
            file_path: Path to the override.conf file
            in_place: If True, modify file in place; if False, return sanitized content
        """
        def process_override_line(line):
            """Process a single line from an override.conf file."""
            # Check for Environment= lines with sensitive variables
            if line.strip().startswith('Environment='):
                line_upper = line.upper()

                # Check if line contains any core sensitive keyword
                should_sanitize = any(keyword.upper() in line_upper
                                      for keyword in self.CORE_SENSITIVE_KEYWORDS)

                # Also check exact sensitive matches
                should_sanitize = should_sanitize or any(exact in line
                                                         for exact in self.EXACT_SENSITIVE)

                if should_sanitize:
                    # Extract variable name and redact value
                    match = re.match(r'^(Environment=\s*[^=]+=).*', line)
                    if match:
                        return f"{match.group(1)}***REDACTED***\n", True
                    return line, False

                return line, False

            return line, False

        return self._sanitize_file_base(file_path, process_override_line, "environment variables", in_place)

    def sanitize_inventory_file(self, file_path, in_place=True):
        """
        Sanitize an Ansible inventory file (YAML format).

        Args:
            file_path: Path to the inventory file
            in_place: If True, modify file in place; if False, return sanitized content
        """
        def process_inventory_line(line):
            """Process a single line from an Ansible inventory file."""
            # Skip comments
            if line.strip().startswith('#'):
                return line, False

            # Check for Ansible-specific sensitive variables (exact match)
            for var in self.ANSIBLE_SENSITIVE_VARS:
                # Match: ansible_password: value (YAML format)
                pattern = rf'^(\s*{var}\s*:\s*).*$'
                match = re.match(pattern, line)
                if match:
                    return f"{match.group(1)}***REDACTED***\n", True

            # Check for general sensitive patterns using unified core keywords
            # But only in YAML value context (after :)
            if ':' in line:
                lower_line = line.lower()

                # Build patterns from core keywords (password:, secret:, key:, token:, credential:)
                sensitive_patterns = [f'{keyword}:' for keyword in self.CORE_SENSITIVE_KEYWORDS]

                # Avoid false positives like 'ssl_key_path' by being more specific
                if any(pattern in lower_line for pattern in sensitive_patterns):
                    # Don't sanitize if it's a path/location/algorithm/provider
                    if not any(exclude in lower_line for exclude in ['_path:', '_location:', '_algorithm:', '_provider:']):
                        # Extract key and redact value
                        match = re.match(r'^(\s*[^#:]+:\s*).*$', line)
                        if match:
                            return f"{match.group(1)}***REDACTED***\n", True

            # No sanitization needed
            return line, False

        return self._sanitize_file_base(file_path, process_inventory_line, "variables", in_place)


def main():
    parser = argparse.ArgumentParser(
        description='Sanitize Confluent Platform configuration files'
    )
    parser.add_argument('file', help='File to sanitize')
    parser.add_argument('--type', choices=['properties', 'override', 'inventory'],
                        help='File type (auto-detected if not specified)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print sanitized output without modifying file')

    args = parser.parse_args()

    # Auto-detect file type if not specified
    file_path = Path(args.file)
    file_type = args.type

    if not file_type:
        if file_path.suffix == '.properties':
            file_type = 'properties'
        elif file_path.name == 'override.conf':
            file_type = 'override'
        elif file_path.suffix in ['.yml', '.yaml'] or 'inventory' in file_path.name.lower():
            file_type = 'inventory'
        else:
            print(f"Error: Cannot auto-detect file type for {args.file}", file=sys.stderr)
            sys.exit(1)

    sanitizer = PropertySanitizer()

    # Dispatch to the appropriate sanitization method
    handlers = {
        'properties': sanitizer.sanitize_properties_file,
        'override': sanitizer.sanitize_override_file,
        'inventory': sanitizer.sanitize_inventory_file,
    }
    result = handlers[file_type](args.file, in_place=not args.dry_run)

    if args.dry_run and result:
        print(result)


if __name__ == '__main__':
    main()

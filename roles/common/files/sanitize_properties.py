#!/usr/bin/env python3
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

    # Properties that MUST be sanitized (exact matches)
    EXACT_SENSITIVE = {
        'confluent.license',
        'ldap.java.naming.security.credentials',
        'confluent.security.master.key',
        'CONFLUENT_SECURITY_MASTER_KEY',
    }

    # Suffix patterns that indicate sensitive values
    SENSITIVE_SUFFIXES = [
        '.password',
        '.secret',
        '.basic.auth.user.info',
        '.basic.auth.credentials',
        '.sasl.jaas.config',
        '.client.secret',
        'keystorePassword',  # Jolokia format
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

        # Check suffix patterns
        key_lower = key.lower()
        for suffix in self.SENSITIVE_SUFFIXES:
            if key_lower.endswith(suffix.lower()):
                return True

        return False

    def sanitize_jaas_partial(self, value):
        """
        Partially sanitize JAAS config: redact passwords and keytabs,
        but preserve principals (they're identifiers, not secrets).
        """
        # Redact password values (quoted and unquoted)
        value = re.sub(r'(password\s*=\s*")[^"]*"', r'\1***REDACTED***"', value, flags=re.IGNORECASE)
        value = re.sub(r"(password\s*=\s*')[^']*'", r"\1***REDACTED***'", value, flags=re.IGNORECASE)
        value = re.sub(r'(password\s*=\s*)([^;\s]+)', r'\1***REDACTED***', value, flags=re.IGNORECASE)

        # Redact keyTab paths (they can reveal system structure)
        value = re.sub(r'(keyTab\s*=\s*")[^"]*"', r'\1***REDACTED***"', value, flags=re.IGNORECASE)
        value = re.sub(r"(keyTab\s*=\s*')[^']*'", r"\1***REDACTED***'", value, flags=re.IGNORECASE)

        # Keep principals - they're identifiers, not secrets
        return value

    def sanitize_properties_file(self, file_path, in_place=True):
        """
        Sanitize a .properties file.

        Args:
            file_path: Path to the properties file
            in_place: If True, modify file in place; if False, return sanitized content

        Returns:
            Sanitized content if in_place=False, else None
        """
        path = Path(file_path)
        if not path.exists():
            print(f"Warning: File not found: {file_path}", file=sys.stderr)
            return None

        lines = []
        sanitized_count = 0

        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.readlines()

        # Add sanitization header
        lines.append("# THIS FILE HAS BEEN SANITIZED - SENSITIVE VALUES REDACTED\n")

        for line in content:
            # Skip existing sanitization headers
            if line.strip().startswith('# THIS FILE HAS BEEN SANITIZED'):
                continue

            # Preserve comments and empty lines
            if line.strip().startswith('#') or not line.strip():
                lines.append(line)
                continue

            # Parse property line (key=value format)
            match = re.match(r'^([^=]+)=(.*)', line)
            if not match:
                lines.append(line)
                continue

            key = match.group(1).strip()
            value = match.group(2)

            # Check if this property should be sanitized
            if self.is_sensitive(key):
                # Special handling for JAAS configs - partial sanitization
                if key.lower().endswith('.sasl.jaas.config'):
                    sanitized_value = self.sanitize_jaas_partial(value)
                    lines.append(f"{key}={sanitized_value}\n")
                else:
                    # Full redaction
                    lines.append(f"{key}= ***REDACTED***\n")
                sanitized_count += 1
            else:
                lines.append(line)

        sanitized_content = ''.join(lines)

        if in_place:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(sanitized_content)
            print(f"Sanitized {sanitized_count} properties in {file_path}")
            return None
        else:
            return sanitized_content

    def sanitize_jaas_file(self, file_path, in_place=True):
        """
        Sanitize a JAAS configuration file.

        Args:
            file_path: Path to the JAAS file
            in_place: If True, modify file in place; if False, return sanitized content
        """
        path = Path(file_path)
        if not path.exists():
            print(f"Warning: File not found: {file_path}", file=sys.stderr)
            return None

        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Add sanitization header
        sanitized_content = "// THIS FILE HAS BEEN SANITIZED - SENSITIVE VALUES REDACTED\n\n"

        # Remove existing header if present
        content = re.sub(r'^//\s*THIS FILE HAS BEEN SANITIZED[^\n]*\n\n?', '', content)

        # Partial sanitization: redact passwords and keytabs, preserve principals
        sanitized_content += self.sanitize_jaas_partial(content)

        if in_place:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(sanitized_content)
            print(f"Sanitized JAAS file: {file_path}")
            return None
        else:
            return sanitized_content

    def sanitize_override_file(self, file_path, in_place=True):
        """
        Sanitize a systemd override.conf file.

        Args:
            file_path: Path to the override.conf file
            in_place: If True, modify file in place; if False, return sanitized content
        """
        path = Path(file_path)
        if not path.exists():
            print(f"Warning: File not found: {file_path}", file=sys.stderr)
            return None

        lines = []
        sanitized_count = 0

        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.readlines()

        # Add sanitization header
        lines.append("# THIS FILE HAS BEEN SANITIZED - SENSITIVE VALUES REDACTED\n")

        sensitive_env_patterns = [
            'PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'CREDENTIAL',
            'CONFLUENT_SECURITY_MASTER_KEY'
        ]

        for line in content:
            # Skip existing sanitization headers
            if 'THIS FILE HAS BEEN SANITIZED' in line:
                continue

            # Check for Environment= lines with sensitive variables
            if line.strip().startswith('Environment='):
                should_sanitize = any(pattern in line.upper() for pattern in sensitive_env_patterns)

                if should_sanitize:
                    # Extract variable name and redact value
                    match = re.match(r'^(Environment=\s*[^=]+=).*', line)
                    if match:
                        lines.append(f"{match.group(1)}***REDACTED***\n")
                        sanitized_count += 1
                    else:
                        lines.append(line)
                else:
                    lines.append(line)
            else:
                lines.append(line)

        sanitized_content = ''.join(lines)

        if in_place:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(sanitized_content)
            print(f"Sanitized {sanitized_count} environment variables in {file_path}")
            return None
        else:
            return sanitized_content

    def sanitize_inventory_file(self, file_path, in_place=True):
        """
        Sanitize an Ansible inventory file (YAML format).

        Args:
            file_path: Path to the inventory file
            in_place: If True, modify file in place; if False, return sanitized content
        """
        path = Path(file_path)
        if not path.exists():
            print(f"Warning: File not found: {file_path}", file=sys.stderr)
            return None

        lines = []
        sanitized_count = 0

        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.readlines()

        # Add sanitization header
        lines.append("# THIS INVENTORY HAS BEEN SANITIZED - SENSITIVE VALUES REDACTED\n")

        # Ansible-specific sensitive variables
        ansible_sensitive_vars = [
            'ansible_ssh_private_key_file',
            'ansible_password',
            'ansible_become_password',
            'ansible_ssh_pass',
            'ansible_become_pass',
        ]

        for line in content:
            # Skip existing sanitization headers
            if 'THIS INVENTORY HAS BEEN SANITIZED' in line:
                continue

            # Skip comments
            if line.strip().startswith('#'):
                lines.append(line)
                continue

            # Check for Ansible-specific sensitive variables (exact match)
            sanitized = False
            for var in ansible_sensitive_vars:
                # Match: ansible_password: value or ansible_password=value
                pattern = rf'^(\s*{var}\s*[:=]\s*).*$'
                match = re.match(pattern, line)
                if match:
                    lines.append(f"{match.group(1)}***REDACTED***\n")
                    sanitized_count += 1
                    sanitized = True
                    break

            if sanitized:
                continue

            # Check for general sensitive patterns (password, secret, key, token, credential)
            # But only in YAML value context (after : or =)
            if ':' in line or '=' in line:
                lower_line = line.lower()

                # Avoid false positives like 'ssl_key_path' by being more specific
                if any(pattern in lower_line for pattern in ['password:', 'password=',
                                                               'secret:', 'secret=',
                                                               'token:', 'token=',
                                                               'credential:', 'credential=']):
                    # Don't sanitize if it's a path/location/algorithm/provider
                    if not any(exclude in lower_line for exclude in ['_path:', '_path=',
                                                                      '_location:', '_location=',
                                                                      '_algorithm:', '_algorithm=',
                                                                      '_provider:', '_provider=']):
                        # Extract key and redact value
                        match = re.match(r'^(\s*[^#:=]+[:=]\s*).*$', line)
                        if match:
                            lines.append(f"{match.group(1)}***REDACTED***\n")
                            sanitized_count += 1
                            continue

            # No sanitization needed, keep line as-is
            lines.append(line)

        sanitized_content = ''.join(lines)

        if in_place:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(sanitized_content)
            print(f"Sanitized {sanitized_count} variables in {file_path}")
            return None
        else:
            return sanitized_content


def main():
    parser = argparse.ArgumentParser(
        description='Sanitize Confluent Platform configuration files'
    )
    parser.add_argument('file', help='File to sanitize')
    parser.add_argument('--type', choices=['properties', 'jaas', 'override', 'inventory'],
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
        elif 'jaas' in file_path.name.lower():
            file_type = 'jaas'
        elif file_path.name == 'override.conf':
            file_type = 'override'
        elif file_path.suffix in ['.yml', '.yaml'] or 'inventory' in file_path.name.lower():
            file_type = 'inventory'
        else:
            print(f"Error: Cannot auto-detect file type for {args.file}", file=sys.stderr)
            sys.exit(1)

    sanitizer = PropertySanitizer()

    # Sanitize based on file type
    if file_type == 'properties':
        result = sanitizer.sanitize_properties_file(args.file, in_place=not args.dry_run)
    elif file_type == 'jaas':
        result = sanitizer.sanitize_jaas_file(args.file, in_place=not args.dry_run)
    elif file_type == 'override':
        result = sanitizer.sanitize_override_file(args.file, in_place=not args.dry_run)
    elif file_type == 'inventory':
        result = sanitizer.sanitize_inventory_file(args.file, in_place=not args.dry_run)

    if args.dry_run and result:
        print(result)


if __name__ == '__main__':
    main()

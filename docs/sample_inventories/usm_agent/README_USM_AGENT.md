# USM Agent Sample Inventory Variables

This document explains the variables used in the USM Agent sample inventories for different authentication modes.

## Authentication Variables

### `usm_agent_basic_auth_enabled`
- **Values**: `true` or `false`
- **Purpose**: Enables/disables basic authentication for USM Agent
- **`false`**: No basic authentication (used for no auth and mTLS)
- **`true`**: Basic username/password authentication

### `usm_agent_ssl_enabled`
- **Values**: `true` or `false`
- **Purpose**: Enables/disables SSL/TLS encryption for USM Agent communication
- **`false`**: HTTP communication (no auth, basic auth)
- **`true`**: HTTPS communication (basic auth + TLS, mTLS)

### `usm_agent_ssl_mutual_auth_enabled`
- **Values**: `true` or `false`
- **Purpose**: Enables mutual TLS authentication (client certificates)
- **`false`**: Server-side TLS only
- **`true`**: Both client and server certificates required (mTLS)

## Client Authentication Variables

### `usm_agent_client_username`
- **Purpose**: Username for client authentication to USM Agent
- **Required**: For basic authentication modes
- **Usage**: Kafka components use this to authenticate with USM Agent

### `usm_agent_client_password`
- **Purpose**: Password for client authentication to USM Agent
- **Required**: For basic authentication modes
- **Usage**: Kafka components use this to authenticate with USM Agent

## Server Authentication Variables

### `usm_agent_basic_users`
- **Purpose**: Defines users allowed to authenticate with USM Agent
- **Required**: For basic authentication modes
- **Structure**: Dictionary of users with principal and password
- **Usage**: USM Agent validates client credentials against this list

## SSL Certificate Variables

### `ssl_custom_certs`
- **Values**: `true` or `false`
- **Purpose**: Enables custom SSL certificate configuration
- **Required**: For TLS/mTLS modes

### `ssl_ca_cert_filepath`
- **Purpose**: Path to the CA certificate bundle
- **Required**: For TLS/mTLS modes
- **Usage**: Validates server certificates

### `ssl_signed_cert_filepath`
- **Purpose**: Path to the signed certificate chain
- **Required**: For TLS/mTLS modes
- **Usage**: Server certificate for USM Agent

### `ssl_key_filepath`
- **Purpose**: Path to the private key file
- **Required**: For TLS/mTLS modes
- **Usage**: Private key for USM Agent certificate

## CCloud Integration Variables

### `usm_agent_ccloud_credential`
- **Purpose**: Confluent Cloud API credentials
- **Required**: For all USM Agent deployments
- **Structure**: Contains username (API key) and password (API secret)

### `usm_agent_ccloud_host`
- **Purpose**: Confluent Cloud API endpoint
- **Required**: For all USM Agent deployments
- **Example**: `https://api.confluent.cloud:443`

### `usm_agent_ccloud_environment_id`
- **Purpose**: Confluent Cloud environment ID
- **Required**: For all USM Agent deployments
- **Usage**: Identifies the target environment for USM Agent

## Variable Usage by Authentication Mode

### No Authentication
- `usm_agent_basic_auth_enabled: false` - No basic authentication
- `usm_agent_ssl_enabled: false` - No SSL/TLS
- No client credentials or SSL certificates needed

### Basic Authentication
- `usm_agent_basic_auth_enabled: true` - Basic auth enabled
- `usm_agent_ssl_enabled: false` - No SSL/TLS
- Client credentials required
- Server users defined in `usm_agent_basic_users`

### Basic Authentication + TLS
- `usm_agent_basic_auth_enabled: true` - Basic auth enabled
- `usm_agent_ssl_enabled: true` - SSL/TLS enabled
- Client credentials required
- SSL certificates required
- Server users defined in `usm_agent_basic_users`

### Mutual TLS (mTLS)
- `usm_agent_basic_auth_enabled: false` - No basic authentication
- `usm_agent_ssl_enabled: true` - SSL/TLS enabled
- `usm_agent_ssl_mutual_auth_enabled: true` - Mutual TLS enabled
- No client credentials needed (certificate-based)
- SSL certificates required for both client and server

## Usage

```bash
# Deploy with specific authentication mode
ansible-playbook -i docs/sample_inventories/usm_agent/usm_agent_no_auth.yml playbook.yml
ansible-playbook -i docs/sample_inventories/usm_agent/usm_agent_basic_auth.yml playbook.yml
ansible-playbook -i docs/sample_inventories/usm_agent/usm_agent_basic_auth_tls.yml playbook.yml
ansible-playbook -i docs/sample_inventories/usm_agent/usm_agent_mtls.yml playbook.yml
```

import jwt
import time
import uuid
import subprocess
import random
import os

# Config
AUDIENCE = "https://oauth1:8443/realms/cp-ansible-realm/protocol/openid-connect/token"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PRIVATE_KEY_FILE = os.path.join(SCRIPT_DIR, "keycloak-tokenKeypair.pem")
ALGORITHM = "RS256"
EXPIRY_SECONDS = 300

# Container configurations with base paths and required components
CONTAINER_CONFIGS = {
    # Broker containers
    # "kafka-broker1": {
    #     "base_path": "/tmp",
    #     "components": ["mds_client", "kafka_client", "schema_registry_client", "monitoring_interceptor_client"]
    # },
    # "kafka-broker2": {
    #     "base_path": "/tmp",
    #     "components": ["mds_client", "kafka_client", "schema_registry_client", "monitoring_interceptor_client"]
    # },
    # "kafka-broker3": {
    #     "base_path": "/tmp",
    #     "components": ["mds_client", "kafka_client", "schema_registry_client", "monitoring_interceptor_client"]
    # },
    # # Controller containers
    # "controller1": {
    #     "base_path": "/tmp",
    #     "components": ["mds_client", "kafka_client"]
    # },
    # "controller2": {
    #     "base_path": "/tmp",
    #     "components": ["mds_client", "kafka_client"]
    # },
    # "controller3": {
    #     "base_path": "/tmp",
    #     "components": ["mds_client", "kafka_client"]
    # },
    # # Service containers
    # "kafka-rest1": {
    #     "base_path": "/tmp",
    #     "components": ["kafka_client", "schema_registry_client", "mds_client"]
    # },
    # "kafka-connect1": {
    #     "base_path": "/tmp",
    #     "components": ["kafka_client", "schema_registry_client", "mds_client"]
    # },
    "ksql1": {
        "base_path": "/tmp",
        "components": ["kafka_client", "schema_registry_client", "mds_client", "ksql_client"]
    },

}

# Client ID mapping for different components
COMPONENT_CLIENT_ID_MAP = {
    "mds_client": "superuser",
    "kafka_client": "kafka_broker",
    "schema_registry_client": "schema_registry",
    "monitoring_interceptor_client": "monitoring_interceptor",
    "ksql_client": "ksql",
    "kafka_connect_client": "kafka_connect",
    "kafka_rest_client": "kafka_rest"
}


def load_private_key():
    """Load the private key from file."""
    with open(PRIVATE_KEY_FILE, "r") as f:
        return f.read()


def generate_token(client_id, custom_msg):
    """Generate a JWT token for the given client ID."""
    now = int(time.time())
    now_ns = int(time.time() * 1e9)
    payload = {
        "iss": client_id,
        "sub": client_id,
        "aud": AUDIENCE,
        "jti": f"{custom_msg}-{uuid.uuid4()}-{now_ns}-{random.getrandbits(32)}",
        "iat": now + random.randint(-10, -1),  # Add a small random offset to avoid collisions
        "exp": now + EXPIRY_SECONDS
    }
    private_key = load_private_key()
    token = jwt.encode(payload, private_key, algorithm=ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def is_container_running(container_name):
    """Check if a Docker container is running."""
    try:
        output = subprocess.check_output(["docker", "inspect", "-f", "{{.State.Running}}", container_name])
        return output.strip().decode("utf-8") == "true"
    except subprocess.CalledProcessError:
        return False


def create_directory_in_container(container_name, directory_path):
    """Create directory in container if it doesn't exist."""
    try:
        subprocess.run([
            "docker", "exec", container_name, 
            "mkdir", "-p", directory_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[WARNING] Failed to create directory {directory_path} in {container_name}: {e}")
        return False


def write_and_copy_component_tokens(container_name, config):
    """Generate and write component tokens directly to container."""
    if not is_container_running(container_name):
        print(f"[WARNING] Container {container_name} is not running. Skipping.")
        return

    base_path = config["base_path"]
    components = config["components"]
    
    # Create base directory in container
    create_directory_in_container(container_name, base_path)
    
    print(f"\n--- Processing container: {container_name} ---")
    
    for component in components:
        # Get client ID for this component
        client_id = COMPONENT_CLIENT_ID_MAP.get(component, component)
        
        # Generate paths
        filename = f"{component}.jwt"
        container_dest_path = f"{base_path}/{filename}"
        
        # Generate token
        token = generate_token(client_id, f"{container_name}-{component}")
        print(f"  ✓ Generated token for {component} (client_id: {client_id})")
        
        # Write directly to container using docker exec
        try:
            subprocess.run([
                "docker", "exec", container_name,
                "sh", "-c", f"echo '{token}' > {container_dest_path}"
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  ✓ Written directly to {container_name}:{container_dest_path}")
        except subprocess.CalledProcessError as e:
            print(f"  ✗ Failed to write to {container_name}:{container_dest_path}: {e}")


def list_container_files(container_name, base_path):
    """List files in container directory for verification."""
    try:
        output = subprocess.check_output([
            "docker", "exec", container_name, 
            "ls", "-la", base_path
        ], stderr=subprocess.DEVNULL)
        return output.decode("utf-8")
    except subprocess.CalledProcessError:
        return None


def verify_tokens():
    """Verify that tokens were created successfully."""
    print("\n" + "="*60)
    print("VERIFICATION - Files in containers:")
    print("="*60)
    
    for container_name, config in CONTAINER_CONFIGS.items():
        if is_container_running(container_name):
            print(f"\n{container_name}:")
            files_output = list_container_files(container_name, config["base_path"])
            if files_output:
                # Filter for .jwt files
                lines = files_output.strip().split('\n')
                jwt_files = [line for line in lines if '.jwt' in line]
                if jwt_files:
                    for line in jwt_files:
                        print(f"  {line}")
                else:
                    print("  No JWT files found")
            else:
                print("  Unable to list files")
        else:
            print(f"\n{container_name}: NOT RUNNING")


def main():
    """Main execution function."""
    print("JWT Token Generator for Confluent Platform Components")
    print("="*60)
    
    # Process all containers
    for container_name, config in CONTAINER_CONFIGS.items():
        write_and_copy_component_tokens(container_name, config)
    
    # Verify the results
    verify_tokens()
    
    print(f"\n{'='*60}")
    print("Token generation completed!")
    print(f"{'='*60}")


def run_continuous():
    """Run the token generation continuously."""
    print("Starting continuous token generation...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            main()
            print(f"\nSleeping for {EXPIRY_SECONDS - 60} seconds before next generation...")
            time.sleep(EXPIRY_SECONDS - 60)  # Refresh before expiry
    except KeyboardInterrupt:
        print("\nStopping token generation...")


if __name__ == "__main__":
    # Run once
    main()
    
    #Uncomment the line below to run continuously
    run_continuous()

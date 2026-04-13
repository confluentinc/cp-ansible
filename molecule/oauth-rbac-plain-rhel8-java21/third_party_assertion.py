import jwt
import time
import uuid
import subprocess
import random
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# Config
AUDIENCE = "https://oauth1:8443/realms/cp-ansible-realm/protocol/openid-connect/token"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PRIVATE_KEY_FILE = os.path.join(SCRIPT_DIR, "keycloak-tokenKeypair.pem")
ALGORITHM = "RS256"
EXPIRY_SECONDS = 300

# Container configurations with base paths and required components
CONTAINER_CONFIGS = {
    # Broker containers
    "kafka-broker1": {
        "client_id": "kafka_broker",
        "base_path": "/tmp",
        "components": ["mds_client", "kafka_broker_client", "embedded_rest_proxy_client", "embedded_rest_proxy_rbac_oauth_client", "metrics_reporter_client", "audit_logs_destination_client", "audit_logs_destination_admin_client"]
    },
    "kafka-broker2": {
        "client_id": "kafka_broker",
        "base_path": "/tmp",
        "components": ["mds_client", "kafka_broker_client", "embedded_rest_proxy_client", "embedded_rest_proxy_rbac_oauth_client", "metrics_reporter_client", "audit_logs_destination_client", "audit_logs_destination_admin_client"]
    },
    "kafka-broker3": {
        "client_id": "kafka_broker",
        "base_path": "/tmp",
        "components": ["mds_client", "kafka_broker_client", "embedded_rest_proxy_client", "embedded_rest_proxy_rbac_oauth_client", "metrics_reporter_client", "audit_logs_destination_client", "audit_logs_destination_admin_client"]
    },
    # Controller containers
    "controller1": {
        "client_id": "kafka_controller",
        "base_path": "/tmp",
        "components": ["mds_client", "controller_client", "metric_reporters_client", "audit_logs_destination_client", "audit_logs_destination_admin_client"]
    },
    "controller2": {
        "client_id": "kafka_controller",
        "base_path": "/tmp",
        "components": ["mds_client", "controller_client", "metric_reporters_client", "audit_logs_destination_client", "audit_logs_destination_admin_client"]
    },
    "controller3": {
        "client_id": "kafka_controller",
        "base_path": "/tmp",
        "components": ["mds_client", "controller_client", "metric_reporters_client", "audit_logs_destination_client", "audit_logs_destination_admin_client"]
    },
    # Service containers - optimized for higher parallelism
    # "kafka-rest1": {
    #     "client_id": "kafka_rest",
    #     "base_path": "/tmp",
    #     "components": ["license_client", "kafka_client", "monitoring_interceptor_client", "mds_client", "kafka_rest_client"],
    #     "max_workers": 8  # Higher concurrency for kafka-rest
    # },
    # "kafka-connect1": {
    #     "client_id": "kafka_connect",
    #     "base_path": "/tmp",
    #     "components": ["kafka_client", "producer_client", "consumer_client", "mds_client", "producer_monitoring_interceptor_client","consumer_monitoring_interceptor_client","secret_registry_client","kafka_connect_client"],
    #     "max_workers": 12  # Higher concurrency for kafka-connect
    # },
    # "ksql1": {
    #     "client_id": "ksql",
    #     "base_path": "/tmp",
    #     "components": ["kafka_client", "schema_registry_client", "mds_client", "ksql_client", "monitoring_interceptor_client"]
    # },
    "schema-registry1": {
        "client_id": "schema_registry",
        "base_path": "/tmp",
        "components": ["kafka_client", "schema_registry_client", "mds_client"]
    },
}

CONTAINER_CONFIGS2 = {
    # Broker containers
    "kafka-broker1": {
        "base_path": "/tmp",
        "components": ["schema_registry_client"],
        "client_id": "schema_registry"
    },
    "kafka-broker2": {
        "base_path": "/tmp",
        "components": ["schema_registry_client"],
        "client_id": "schema_registry"
    },
    "kafka-broker3": {
        "base_path": "/tmp",
        "components": ["schema_registry_client"],
        "client_id": "schema_registry"
    }
}

CONTAINER_CONFIGS3 = {
    # Broker containers
    "kafka-broker1": {
        "base_path": "/tmp",
        "components": ["superuser_client"],
        "client_id": "superuser"
    },
    "kafka-broker2": {
        "base_path": "/tmp",
        "components": ["superuser_client"],
        "client_id": "superuser"
    },
    "kafka-broker3": {
        "base_path": "/tmp",
        "components": ["superuser_client"],
        "client_id": "superuser"
    }
}

# Cache for private key to avoid repeated file reads
_private_key_cache = None
_private_key_lock = threading.Lock()

# Global counter and lock for unique token generation
_token_counter = 0
_counter_lock = threading.Lock()


def get_unique_counter():
    """Get a unique counter value thread-safely."""
    global _token_counter
    with _counter_lock:
        _token_counter += 1
        return _token_counter


def load_private_key():
    """Load the private key from file (cached)."""
    global _private_key_cache
    if _private_key_cache is None:
        with _private_key_lock:
            if _private_key_cache is None:  # Double-check locking
                with open(PRIVATE_KEY_FILE, "r") as f:
                    _private_key_cache = f.read()
    return _private_key_cache


def generate_token(client_id, container_name, component):
    """Generate a unique JWT token for the given client ID and component."""
    now = int(time.time())
    now_ns = int(time.time() * 1e9)

    # Create a unique identifier using multiple sources of entropy
    unique_counter = get_unique_counter()
    thread_id = threading.get_ident()
    random_bits = random.getrandbits(64)

    # Create a hash of the unique components to ensure uniqueness
    unique_string = f"{container_name}-{component}-{unique_counter}-{thread_id}-{now_ns}-{random_bits}"
    unique_hash = hashlib.sha256(unique_string.encode()).hexdigest()[:16]

    # Generate JTI with multiple entropy sources
    jti = f"{client_id}-{container_name}-{component}-{unique_hash}-{uuid.uuid4()}"

    payload = {
        "iss": client_id,
        "sub": client_id,
        "aud": AUDIENCE,
        "jti": jti,
        "iat": now + random.randint(-30, -1),  # Larger random offset to avoid collisions
        "exp": now + EXPIRY_SECONDS,
        # Add custom claims to ensure uniqueness
        "container": container_name,
        "component": component,
        "counter": unique_counter
    }
    private_key = load_private_key()
    token = jwt.encode(payload, private_key, algorithm=ALGORITHM)
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def is_container_running(container_name):
    """Check if a Docker container is running."""
    try:
        output = subprocess.check_output(
            ["docker", "inspect", "-f", "{{.State.Running}}", container_name],
            stderr=subprocess.DEVNULL
        )
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


def process_single_component(container_name, component, client_id, base_path):
    """Process a single component token - optimized for parallel execution."""
    # Generate paths with timestamp to avoid conflicts
    timestamp = int(time.time() * 1000000)  # microsecond precision
    thread_id = threading.get_ident()
    filename = f"{component}.jwt"
    container_dest_path = f"{base_path}/{filename}"
    tmp_path = f"/tmp/{client_id}_{component}_{container_name}_{timestamp}_{thread_id}_client_assertion.jwt"
    try:
        # Generate unique token
        token = generate_token(client_id, container_name, component)
        # Write to temp file
        with open(tmp_path, "w") as f:
            f.write(token)
        # Copy to container with retries for reliability
        max_retries = 3
        for attempt in range(max_retries):
            try:
                subprocess.run(
                    ["docker", "cp", tmp_path, f"{container_name}:{container_dest_path}"], 
                    check=True, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    timeout=30  # Add timeout to prevent hanging
                )
                break
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff

        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

        return f"  ✓ {container_name}:{component} -> {container_dest_path}"

    except subprocess.CalledProcessError as e:
        return f"  ✗ {container_name}:{component} FAILED: {e}"
    except subprocess.TimeoutExpired as e:
        return f"  ✗ {container_name}:{component} TIMEOUT: {e}"
    except Exception as e:
        return f"  ✗ {container_name}:{component} ERROR: {e}"
    finally:
        # Ensure cleanup of temp file
        try:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except OSError:
            pass


def write_and_copy_component_tokens_optimized(container_name, config):
    """Generate and write component tokens with maximum parallelization."""
    if not is_container_running(container_name):
        print(f"[WARNING] Container {container_name} is not running. Skipping.")
        return

    base_path = config["base_path"]
    components = config["components"]
    client_id = config["client_id"]
    # Get container-specific max_workers or use default
    max_workers = config.get("max_workers", min(len(components), 6))

    # Create base directory in container
    create_directory_in_container(container_name, base_path)

    print(f"\n--- Processing container: {container_name} (workers: {max_workers}) ---")

    # Process all components in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all component tasks
        future_to_component = {
            executor.submit(process_single_component, container_name, component, client_id, base_path): component
            for component in components
        }
        # Collect results as they complete
        for future in as_completed(future_to_component):
            result = future.result()
            print(result)


def process_container_batch(container_configs, batch_name=""):
    """Process a batch of container configurations in parallel."""
    print(f"\n{'='*60}")
    print(f"Processing {batch_name} batch...")
    print(f"{'='*60}")
    # Determine optimal concurrency based on container types
    priority_containers = ["kafka-connect1", "kafka-rest1"]
    max_container_workers = 10
    # Use ThreadPoolExecutor for container-level parallelism
    with ThreadPoolExecutor(max_workers=max_container_workers) as executor:
        futures = []
        # Submit priority containers first
        for container_name, config in container_configs.items():
            if container_name in priority_containers:
                future = executor.submit(write_and_copy_component_tokens_optimized, container_name, config)
                futures.append(future)
        # Submit remaining containers
        for container_name, config in container_configs.items():
            if container_name not in priority_containers:
                future = executor.submit(write_and_copy_component_tokens_optimized, container_name, config)
                futures.append(future)

        # Wait for all containers to complete
        for future in as_completed(futures):
            try:
                future.result()  # This will raise any exceptions that occurred
            except Exception as e:
                print(f"[ERROR] Container processing failed: {e}")


def list_container_files(container_name, base_path):
    """List files in container directory for verification."""
    try:
        output = subprocess.check_output([
            "docker", "exec", container_name,
            "ls", "-la", base_path
        ], stderr=subprocess.DEVNULL, timeout=10)
        return output.decode("utf-8")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def verify_tokens():
    """Verify that tokens were created successfully."""
    print("\n" + "="*60)
    print("VERIFICATION - Files in containers:")
    print("="*60)
    all_containers = {}
    all_containers.update(CONTAINER_CONFIGS)
    all_containers.update(CONTAINER_CONFIGS2)
    all_containers.update(CONTAINER_CONFIGS3)
    for container_name, config in all_containers.items():
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
    """Main execution function with optimized parallel processing."""
    print("JWT Token Generator for Confluent Platform Components")
    print("="*60)

    start_time = time.time()

    # Process all container batches in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(process_container_batch, CONTAINER_CONFIGS, "MAIN"),
            executor.submit(process_container_batch, CONTAINER_CONFIGS2, "SCHEMA_REGISTRY"),
            executor.submit(process_container_batch, CONTAINER_CONFIGS3, "SUPERUSER")
        ]
        # Wait for all batches to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR] Batch processing failed: {e}")

    end_time = time.time()
    # Verify the results
    # verify_tokens()
    print(f"\n{'='*60}")
    print(f"Token generation completed in {end_time - start_time:.2f} seconds!")
    print(f"{'='*60}")


def run_continuous():
    """Run the token generation continuously."""
    print("Starting continuous token generation...")
    print("Press Ctrl+C to stop")
    try:
        while True:
            main()
    except KeyboardInterrupt:
        print("\nStopping token generation...")


if __name__ == "__main__":
    # Run once
    main()
    # Uncomment the line below to run continuously
    run_continuous()

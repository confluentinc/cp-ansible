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
BROKER_CONTAINERS = ["kafka-broker1", "kafka-broker2", "kafka-broker3"]
CONTROLLER_CONTAINERS = ["controller1", "controller2", "controller3"]
KAFKAREST_CONTANERS = "kafka-rest1"
KAFKACONNECT_CONTAINER = "kafka-connect1"
KSQL_CONTAINER = "ksql1"
SCHEMA_REGISTRY_CONTAINER = "schema-registry1"


def load_private_key():
    with open(PRIVATE_KEY_FILE, "r") as f:
        return f.read()


def generate_token(client_id, custom_msg):
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
    try:
        output = subprocess.check_output(["docker", "inspect", "-f", "{{.State.Running}}", container_name])
        return output.strip().decode("utf-8") == "true"
    except subprocess.CalledProcessError:
        return False


def write_and_copy_token(client_id, container_name):
    tmp_path = f"/tmp/{client_id}_client_assertion.jwt"
    container_dest_path = f"/tmp/{client_id}_client_assertion.jwt"

    token = generate_token(client_id, container_name)
    print(f"Generated token for {client_id}")

    with open(tmp_path, "w") as f:
        f.write(token)

    if is_container_running(container_name):
        try:
            subprocess.run(["docker", "cp", tmp_path, f"{container_name}:{container_dest_path}"], check=True)
            print(f"Copied token to {container_name}:{container_dest_path}")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to copy token to container {container_name}: {e}")
    else:
        print(f"[WARNING] Container {container_name} is not running. Skipping.")


def main():
    while True:
        for container in BROKER_CONTAINERS:
            write_and_copy_token("schema_registry", container)
            write_and_copy_token("superuser", container)
        for container in CONTROLLER_CONTAINERS:
            write_and_copy_token("superuser", container)
        write_and_copy_token("schema_registry", SCHEMA_REGISTRY_CONTAINER)
        write_and_copy_token("kafka_connect", KAFKACONNECT_CONTAINER)
        write_and_copy_token("kafka_rest", KAFKAREST_CONTANERS)
        write_and_copy_token("ksql", KSQL_CONTAINER)


if __name__ == "__main__":
    main()

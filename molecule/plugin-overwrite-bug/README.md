# Plugin Overwrite Bug Test Case

This Molecule test case validates the fix for the plugin overwrite bug described in [GitHub issue #1766](https://github.com/confluentinc/cp-ansible/issues/1766).

## Problem Description

When custom JAR files are placed inside Kafka Connect plugin directories using `kafka_connect_copy_files`, they get overwritten during plugin installation because:

1. The "Copy Kafka Connect Files" task runs **before** the "Install Connect Plugins" task
2. Plugin installation with `--force` flag deletes and recreates the plugin directory
3. Custom JARs placed inside plugin directories are lost

## Test Scenario

This test verifies that:

1. **Plugin installation works correctly** (JDBC plugin is installed)
2. **Custom JAR is preserved** inside the plugin directory after installation
3. **The fix is working** (copy task runs after plugin installation)

## Test Configuration

- **Plugin**: `confluentinc/kafka-connect-jdbc:10.7.4`
- **Custom JAR**: `ibm-mq-connector.jar` (placeholder file)
- **Destination**: `/usr/share/java/connect_plugins/confluentinc-kafka-connect-jdbc/ibm-mq-connector.jar`
- **Installation Method**: Archive

## Running the Test

### Prerequisites

Follow the setup instructions in [HOW_TO_TEST.md](../../docs/HOW_TO_TEST.md) to install:
- Python3
- Ansible >= 4.x
- Docker (version 4.2.0 or earlier)
- Molecule >= 3.3

### Test Commands

```bash
# Run the complete test (creates, converges, verifies, destroys)
molecule test -s plugin-overwrite-bug

# Run individual phases
molecule converge -s plugin-overwrite-bug  # Deploy and test
molecule verify -s plugin-overwrite-bug    # Run verification
molecule destroy -s plugin-overwrite-bug   # Clean up

# SSH into the container for investigation
molecule login -s plugin-overwrite-bug -h kafka-connect1
```

### Using Molecule in Container (Alternative)

If you encounter pip installation issues, use the container approach:

```bash
# Set up alias (add to .bashrc for permanence)
export CP_ANSIBLE_PATH=$PWD
alias molecule="docker run -it --rm --dns="8.8.8.8" -v "/var/run/docker.sock:/var/run/docker.sock" -v ~/.cache:/root/.cache -v "$CP_ANSIBLE_PATH:$CP_ANSIBLE_PATH" -w "$CP_ANSIBLE_PATH" quay.io/ansible/molecule:3.1.5 molecule"

# Run the test
molecule test -s plugin-overwrite-bug
```

## Expected Results

✅ **Test should pass** if the fix is working correctly
✅ **Custom JAR should exist** inside the plugin directory
✅ **Plugin should be properly installed** with all standard files

## Verification Details

The test verifies:
- Custom JAR exists at `/usr/share/java/connect_plugins/confluentinc-kafka-connect-jdbc/ibm-mq-connector.jar`
- Root level JAR exists at `/usr/share/java/connect_plugins/ibm-mq-connector.jar`
- Plugin directory contains all standard files (assets, doc, etc, lib, manifest.json)

## Related Files

- `molecule.yml`: Test configuration
- `converge.yml`: Main test playbook
- `verify.yml`: Verification tasks
- `test-jars/ibm-mq-connector.jar`: Test JAR file

## Integration

This test case can be integrated into:
- **CI/CD pipelines** (GitHub Actions, Jenkins, GitLab CI)
- **Local development** testing
- **Regression testing** to prevent the bug from reoccurring

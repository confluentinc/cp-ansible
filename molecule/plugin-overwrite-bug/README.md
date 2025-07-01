# Plugin Overwrite Bug Test Case

This Molecule test case validates the fix for the plugin overwrite bug described in [GitHub issue #1766](https://github.com/confluentinc/cp-ansible/issues/1766).

## Problem Description

When custom JAR files are placed inside Kafka Connect plugin directories using `kafka_connect_copy_files`, they get overwritten during plugin installation because:

1. The "Copy Kafka Connect Files" task runs **before** the "Install Connect Plugins" task
2. Plugin installation with `--force` flag deletes and recreates the plugin directory
3. Custom JARs placed inside plugin directories are lost

## Test Scenario

This test verifies that:

1. **Plugin installation works correctly** (Spooldir plugin is installed)
2. **Custom JAR is preserved** inside the plugin directory after installation
3. **The fix is working** (copy task runs after plugin installation)

## Test Configuration

- **Plugin**: `jcustenborder/kafka-connect-spooldir:2.0.43`
- **Custom JAR**: `ibm-mq-connector.jar` (placeholder file)
- **Destination**: `/usr/share/java/connect_plugins/jcustenborder-kafka-connect-spooldir/ibm-mq-connector.jar`
- **Installation Method**: Archive
- **Components**: Zookeeper, Kafka Broker, Kafka Connect
- **Authentication**: SASL Plain (no SSL)


## Expected Results

✅ **Test should pass** if the fix is working correctly
✅ **Custom JAR should exist** inside the plugin directory
✅ **Plugin should be properly installed** with all standard files
✅ **Kafka Connect API should be accessible** on port 8083

## Verification Details

The test verifies:
- Custom JAR exists at `/usr/share/java/connect_plugins/jcustenborder-kafka-connect-spooldir/ibm-mq-connector.jar`
- Root level JAR exists at `/usr/share/java/connect_plugins/ibm-mq-connector.jar`
- Plugin directory contains all standard files (assets, doc, etc, lib, manifest.json)
- Kafka Connect REST API responds with status 200

## Test Validation

To validate the test is working correctly:

1. **Run with fix applied**: Test should pass ✅
2. **Revert the fix**: Test should fail ❌ (proving bug exists)
3. **Re-apply the fix**: Test should pass ✅ (proving fix works)

## Related Files

- `molecule.yml`: Test configuration with Zookeeper, Kafka Broker, and Kafka Connect
- `converge.yml`: Main test playbook
- `verify.yml`: Verification tasks
- `test-jars/ibm-mq-connector.jar`: Test JAR file (placeholder)

## Integration

This test case can be integrated into:
- **CI/CD pipelines** (GitHub Actions, Jenkins, GitLab CI)
- **Local development** testing
- **Regression testing** to prevent the bug from reoccurring

## Troubleshooting

### Common Issues

1. **File not found errors**: Ensure the test JAR file is committed to git (use `git add -f molecule/plugin-overwrite-bug/test-jars/`)
2. **Connection refused**: Verify Zookeeper and Kafka Broker are running before Kafka Connect
3. **Plugin installation failures**: Check network connectivity for Confluent Hub downloads

# Runs sanity and galaxy-importer checks on collection to ensure all the checks are met

set -ex

echo "Sanity + Galaxy-Importer Test Block"
echo "----------------"
echo "Python $PYTHON_VERSION"
echo "Ansible $ANSIBLE_VERSION"


cd $PATH_TO_CPA

version_gte() {
    # returns 0 if first arg version is greater than equal to second arg else returns 1

    local actual_ansi_version="$1"
    local min_allowed_ansi_version="$2"

    # Sort the versions in ascending order
    sorted_versions=$(printf "%s\n%s" "$actual_ansi_version" "$min_allowed_ansi_version" | sort -V)

    versions=($sorted_versions)
    # Split the sorted versions into an array

    if [[ "${versions[0]}" = "$min_allowed_ansi_version" ]]; then
        echo 0
        # actual ansible core version >= min allowed
    else
        echo 1
        # min core version allowed > actual ansible version
    fi
}

# This is very bad practice of grepping from yml files. Whenever someone will change the yml file significantly then this might break
MIN_ALLOWED_CORE_VERSION_LINE=$(cat meta/runtime.yml | grep 'requires_ansible:')
MIN_ALLOWED_CORE_VERSION=${MIN_ALLOWED_CORE_VERSION_LINE:21:4}
ANSI_CORE_VERSION_OKAY=$(version_gte $ANSIBLE_CORE_VERSION $MIN_ALLOWED_CORE_VERSION)
if [[ $ANSI_CORE_VERSION_OKAY -eq 1 ]]; then
    echo "Skipping this block as meta/runtime.yml specified minimum version is newer than this" >> $LOG_FILE
    exit
fi

sudo apt install -y shellcheck

# prepend the desired default python version to .python-version file
{ echo "$PYTHON_VERSION"; cat .python-version 2>/dev/null || true; } > .python-version.tmp && mv .python-version.tmp .python-version

pip install wheel
pip install pylint
pip install "ansible==$ANSIBLE_VERSION"
pip install yamllint
pip install galaxy-importer
pip install setuptools

python --version
ansible --version

export PYTHON_INTERPRETER=$(which python)
echo $PYTHON_INTERPRETER

# Test1
export GALAXY_IMPORTER_CONFIG="$PATH_TO_CPA/galaxy-importer/galaxy-importer.cfg"
echo "Running galaxy-importer..."
GALAXY_OUTPUT=$(python -m galaxy_importer.main $ARTEFACT 2>&1)

# Extract ansible-lint section from galaxy-importer output and check for warnings
ANSIBLE_LINT_SECTION=$(echo "$GALAXY_OUTPUT" | sed -n '/Linting collection via ansible-lint/,/\.\.\.ansible-lint run complete/p')

# Check if there are any warnings in the ansible-lint section
if echo "$ANSIBLE_LINT_SECTION" | grep -q "WARNING:"; then
    echo "ERROR: ansible-lint warnings detected. Pipeline should fail on warnings."
    exit 1
fi

# Check if the galaxy-importer itself failed
if [ $GALAXY_EXIT_CODE -ne 0 ]; then
    echo "ERROR: galaxy-importer failed with exit code $GALAXY_EXIT_CODE"
    exit $GALAXY_EXIT_CODE
fi

echo "galaxy-importer completed successfully with no ansible-lint warnings."

# Test2
echo "Running ansible-test sanity..."
ansible-test sanity

# Builds the tar file of ansible collection

set -ex

cd $PATH_TO_CPA

pyenv local $PYTHON_VERSION 3.9 3.8 3.9 3.10 3.11 3.12 # This creates .python-version file which lists all these versions.
# 1st version in list will be 3.9 and also become the default version of python
pip install wheel
pip install pylint
pip install "ansible==$ANSIBLE_VERSION"

python --version
ansible --version

export PYTHON_INTERPRETER=$(which python)
echo $PYTHON_INTERPRETER
ansible-galaxy collection build

# Check if the tar file exists
if [[ -f "$PATH_TO_CPA/$ARTEFACT" ]]; then
    echo "The collection($ARTEFACT) has been built."
else
    echo "Collection build failed and $ARTEFACT file does not exist."
    exit 1
fi
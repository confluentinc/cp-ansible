# Builds the tar file of ansible collection

set -ex

cd $PATH_TO_CPA

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

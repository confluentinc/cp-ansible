for d in roles/* ; do
    pushd $d
    if [ -d "molecule" ]
    then
        echo "Running Molecule Test in role $d"
        molecule test --all
    fi
    popd
done

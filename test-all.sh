for d in roles/* ; do
    pushd $d
    [ -d "molecule/" ] && echo "Running Molecule Test in role $d" && molecule test --all
    popd
done

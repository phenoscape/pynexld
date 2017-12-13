#!/bin/bash
td=../nexld/tests/example_nexml
if ! test -d ${td} ; then
    echo "Skipping tests from nexld because ${td} was not found"
else
    if ! test -d cruft ; then
        mkdir cruft
    fi
    for fp in ${td}/*.xml ; do
        fn=$(basename "${fp}")
        echo "Transforming ${fn} to JSON-LD"
        python pynexld/__init__.py "${fp}" > "cruft/unnorm-$fn" 2> "cruft/err-$fn"
    done
    if which jq 2>/dev/null ; then
        for fp in ${td}/*.xml ; do
        fn=$(basename "${fp}")
        echo "Normalizing JSON formatting of ${fn}"
        cat "cruft/unnorm-$fn" | jq -S . > "cruft/jq-$fn"
    done
    else
        echo "Skipping transformation because jq is not found"
    fi
fi
python -m pytest
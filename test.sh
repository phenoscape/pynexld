#!/bin/bash
td=../nexld/tests/example_nexml
tdo=../nexld/tests/example_jsonld
if ! test -d ${td} ; then
    echo "Skipping tests from nexld because ${td} was not found"
else
    if ! test -d cruft ; then
        mkdir cruft
    fi
    for fp in ${td}/*.xml ; do
        fn=$(basename "${fp}")
        jfn=$(echo $fn | sed 's/.xml$/.json/')
        efn=$(echo $fn | sed 's/.xml$/.txt/')
        echo "Transforming ${fn} to JSON-LD ..."
        python pynexld/__init__.py "${fp}" > "cruft/unnorm-${jfn}" 2> "cruft/err-${efn}" || exit
    done
    if which jq >/dev/null ; then
        for fp in ${td}/*.xml ; do
            fn=$(basename "${fp}")
            jfn=$(echo $fn | sed 's/.xml$/.json/')
            echo "Normalizing JSON formatting of cruft/unnorm-${jfn} ..."
            cat "cruft/unnorm-${jfn}" | jq -S . > "cruft/jq-${jfn}"  || exit
            rjqi="${tdo}/${jfn}"
            if test -f "${rjqi}" ; then
                rjqo=cruft/jq-r-${jfn}
                if ! test -f ${rjqo} ; then
                    echo "Normalizing JSON formatting of ${rjqi} ..."
                    cat "${rjqi}" | jq -S . > "${rjqo}" || exit
                fi
                echo "Diffing ${rjqo} and cruft/jq-${jfn} ..."
                diff "${rjqo}"  "cruft/jq-${jfn}" > "cruft/diff-R-Python-${jfn}.txt" 2>&1
            else
                echo "R output ${rjqi} does not exist"
            fi
        done
    else
        echo "Skipping transformation because jq is not found"
    fi
fi
python -m pytest || exit
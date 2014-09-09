#!/bin/bash

status=0
for f in $(find . -name '*.py');
do
  if [[ "$f" == *__openerp__.py ]]; then
    dummy=$(diff <(head -n 12 travis/compassion_openerp_header.txt) <(head -n 12 $f))
    isOk=$?
    dummy=$(diff <(sed -n '14,28p;28q' travis/compassion_openerp_header.txt) <(sed -n '14,28p;28q' $f))
    isOk2=$?
  else
    dummy=$(diff <(head -n 5 travis/compassion_py_header.txt) <(head -n 5 $f))
    isOk=$?
    dummy=$(diff <(sed -n '7,10p;10q' travis/compassion_py_header.txt) <(sed -n '7,10p;10q' $f))
    isOk2=$?
  fi
  if [[ $isOk -ne 0 || $isOK2 -ne 0 ]]; then
    echo "$f has wrong header"
    status=1
  fi
done < <(cat)

exit $status

#!/bin/bash

status=0
for f in $(find . -name '*.py');
do
  if [[ "$f" == *__openerp__.py ]]; then
    dummy=$(diff <(sed 's/^\xef\xbb\xbf//' <(sed 's/\r$//' <(head -n 11 travis/compassion_openerp_header.txt))) <(sed 's/^\xef\xbb\xbf//' <(sed 's/^\xef\xbb\xbf//' <(sed 's/\r$//' <(head -n 11 $f)))))
    isOk=$?
    dummy=$(diff <(sed 's/^\xef\xbb\xbf//' <(sed 's/\r$//' <(sed -n '14,28p;28q' travis/compassion_openerp_header.txt))) <(sed 's/\r$//' <(sed 's/^\xef\xbb\xbf//' <(sed -n '14,28p;28q' $f))))
    isOk2=$?
    isOk3=0
  else
    dummy=$(diff <(sed 's/^\xef\xbb\xbf//' <(sed 's/\r$//' <(head -n 3 travis/compassion_py_header.txt))) <(sed 's/^\xef\xbb\xbf//' <(sed 's/\r$//' <(head -n 3 $f))))
    isOk=$?
    dummy=$(diff <(sed 's/^\xef\xbb\xbf//' <(sed 's/\r$//' <(sed -n '5p;5q' travis/compassion_py_header.txt))) <(sed 's/^\xef\xbb\xbf//' <(sed 's/\r$//' <(sed -n '5p;5q' $f))))
    isOk2=$?
    dummy=$(diff <(sed 's/^\xef\xbb\xbf//' <(sed 's/\r$//' <(sed -n '7,10p;10q' travis/compassion_py_header.txt))) <(sed 's/^\xef\xbb\xbf//' <(sed 's/\r$//' <(sed -n '7,10p;10q' $f))))
    isOk3=$?
  fi
  if [[ $isOk -ne 0 || $isOk2 -ne 0 || $isOk3 -ne 0 ]]; then
    echo "$f has wrong header"
    status=1
  fi
done < <(cat)

exit $status

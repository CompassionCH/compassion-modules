#! /bin/bash
for f in /usr/local/lib/*.so.3.0.0
do 
    L1=`echo $f | sed 's/\(.*\.\)so.3.0.0/\1so.3.0/'`
    if [ -h "$L1" ]; then
	rm $L1
    fi

    L2=`echo $f | sed 's/\(.*\.\)so.3.0.0/\1so/'`
    if [ -h "$L2" ]; then
	rm $L2
    fi
   
    ln -s $f $L1
    ln -s $L1 $L2
done



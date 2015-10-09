for f in /usr/local/lib/*.so.3.0.0
do 
	ln -s $f `echo $f | sed 's/\(.*\.\)so.3.0.0/\1so.3.0/'`
	ln -s `echo $f | sed 's/\(.*\.\)so.3.0.0/\1so.3.0/'` `echo $f | sed 's/\(.*\.\)so.3.0.0/\1so/'`
done



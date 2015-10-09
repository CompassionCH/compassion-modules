for f in *.so.3.0
do 
	rm "$f"
	ln -s `echo $f | sed 's/\(.*\.\)so.3.0/\1so.3.0.0/'` $f
done

for f in *.so
do 
	rm "$f"
	ln -s `echo $f | sed 's/\(.*\.\)so/\1so.3.0/'`  $f
done


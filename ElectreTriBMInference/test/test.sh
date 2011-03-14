#!/bin/sh

NB_TEST_SETS=3
PYTHON_SCRIPT=infetribm.py

cd ..
for i in $(seq $NB_TEST_SETS); do
	python $PYTHON_SCRIPT --in test/in$i --out test/out$i
	if [ $? == 0 ]; then
		echo "Test $i ok";
	else
		echo "Test $i failed";
	fi
done

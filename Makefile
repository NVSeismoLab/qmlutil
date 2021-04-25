#
# Make targets for qmlutil library
#
ANTELOPE := /opt/antelope/5.6

.PHONY : check clean dist test wheel

# Run unit tests with no deps or integration
check :
	py.test -m "not integration"

# Run full verbose logging test suite with output written to tmp dir
test : 
	ANTELOPE=$(ANTELOPE) py.test -sv --writefiles

clean :
	rm -f ./*.whl 
	rm -rf ./*.egg-info

wheel :
	pip wheel ./


dist : 
	python setup.py sdist



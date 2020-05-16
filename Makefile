#
# Make targets for qmlutil library
#
.PHONY : check clean test wheel

# Run unit tests with no deps or integration
check :
	py.test

# Run full verbose logging test suite with output written to tmp dir
test : 
	py.test -sv --integration --writefiles

clean :
	rm -f ./*.whl 
	rm -rf ./*.egg-info

wheel :
	pip wheel ./




#!/bin/bash
python setup.py sdist

python setup.py bdist_wheel

version=$(python setup.py --version)
echo -n "Enter the upload URL"
read url
twine upload --repository "$url" --sign --verbose dist/tidalapi-$version*

#!/bin/bash
poetry build

echo -n "Enter the upload URL"
read name
read url
poetry config "repositories.${name}" "${url}"
poetry publish -r "${name}"

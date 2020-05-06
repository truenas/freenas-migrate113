#!/bin/bash -eux
rm ../migrate113_* || true
tar -cf  ../migrate113_0.10.orig.tar * .git .idea
gzip ../migrate113_*.orig.tar

docker run --rm -v `pwd`/..:/work -it debian:stable sh -c 'cd /work/freenas-migrate113 && apt update && apt install -y build-essential debhelper-compat python3-all sudo && useradd user && sudo -u user dpkg-buildpackage -us -uc'

debsign -k 97D59B7818EE301EE5453AE75197C3AB44CDF299 ../migrate113_*.dsc
debsign -k 97D59B7818EE301EE5453AE75197C3AB44CDF299 ../migrate113_*.changes
dput truenas ../*changes

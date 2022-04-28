#!/bin/bash
# ES512 public/private key, code from https://gist.github.com/maxogden/62b7119909a93204c747633308a4d769

FILENAME=${1:-ecdsa}

openssl ecparam -genkey -name secp521r1 -noout -out .secrets/$FILENAME.priv.pem
# public key
openssl ec -in .secrets/$FILENAME.priv.pem -pubout -out .secrets/$FILENAME.pub.pem

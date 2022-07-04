# Images

This folder contains IaaC used to build machine images for different cloud providers. 

Images are built using [packer](https://www.packer.io/)

All images should have a similar way to be built. 
Each image has a `Makefile`, a `image.pkr.hcl` and a `variables.prk.hcl`. 

Finally the way to build a image MUST BE:

```
cd images/<provider>/<image_name>
make build
```

`image.pkr.hcl` and `variables.pkr.hcl` could be customized.

Check for each provider whichs variables should be provided. 


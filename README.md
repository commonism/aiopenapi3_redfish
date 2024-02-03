# aiopenapi3_redfish
Python3 DMTF Redfish client library built upon OpenAPI3/aiopenapi3.

DMTF Redfish / SNIA Swordfish OpenAPI3 description documents are processed and adjusted to create an aiopenapi3 client.
A very thin layer is added on top to improve the usability.

## Features
 * high quality serialization & validation of messages \
   pydantic (aiopenapi3)
 * redirect description document retrival to local directory\
   accessing a local disk instead of a (BMC) webserver provides a significant speedup when creating the client (aiopenapi3 Loader)
 * caching of serialized clients\
   a cached copy of a processed description document speeds up initialization  (aiopenapi3)
 * reduction of description document to defined pathes/Operations \
   reducing the number of objects required in the client speeds up initialization (aiopenapi3 Reduce/Cull)
 * description document mangling to align to the OpenAPI standard \
   do not rely on your vendor to release new firmware (aiopenapi3 Document plugin)
 * message manipulation to align oem implementations to the DMTF Redfish/IANA Swordfish protocol specification \
   do not rely on your vendor to release new firmware (aiopenapi3 Message plugin)
 * Oem customization/namespaces/actions support \
   plug in your Oem extensions
 * use with Oem Redfish description documents\
   Oem description documents are smaller - speeding up processing time and include Oem Schemas - improving usability


## Oem Extensions Support

Supporting Oem Extensions requires openapi description documents for the Oem.
Therefore,  default is limited to Oems publishing openapi description documents for their extensions.

At 2023 it looks like this:

| Oem         |                                   OpenAPI                                   | …                                                                                                     |
|-------------|:---------------------------------------------------------------------------:|-------------------------------------------------------------------------------------------------------|
| Dell        |                                     yes                                     | iDRAC firmware >= 4.0.0                                                                               |
| HP          | [#158](https://github.com/HewlettPackard/python-ilorest-library/issues/158) | [HPE iLO 6 Redfish](https://servermanagementportal.ext.hpe.com/docs/redfishservices/ilos/ilo6/ilo6_changelog/) |
| Supermicro  |                                     no                                      | BMC_X13AST2600-ROT-C301MS_20231115_01.01.08_STDsp.bin                                                 |
| Lenovo      |                                   no&ast;                                   | nvgy_fw_xcc_usx338f-3.10_anyos_comp.uxz                                                               |

&ast; openapi.yaml exists but does not have any Oem extensions

### Dell
Dell provides OpenAPI description documents. The clinic assists in making sure the description documents are valid and the protocol dialect is understood.

### HPE
[Extracting](https://mark.honeychurch.org/blog/projects/ahs/) the OpenAPI description documents from the firmware using [ilo4_toolbox](https://github.com/airbus-seclab/ilo4_toolbox) was not possible due to iLO format changes.

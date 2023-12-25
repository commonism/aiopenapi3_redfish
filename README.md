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

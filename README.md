OpenSRS-py
==========

This is a python implementation of the [OpenSRS][opensrs] [XML API][xmlapi].

It is only a light wrapper around the structure of the requests and
responses as defined by the API.

Example Usage
-------------

Here is what a post call looks like:

    from opensrs import OpenSRS
    opensrs = OpenSRS("myusername", "privatekey", test=True)
    opensrs.post("sw_register", "domain",
        attrs={
            "domain": "example.com",
            "auto_renew": 1,
            "link_domains": 0,
            "reg_type": "new",
            "contact_set": {
                "owner": { ... },
                "admin": { ... },
                "billing": { ... },
                "tech": { ... },
                },
            "nameserver_list": [
                {
                    "sortorder": 1,
                    "name": "ns1.fatbox.ca",
                    },
                {
                    "sortorder": 2,
                    "name": "ns2.fatbox.ca",
                    },
                ],
            },
        extra_items = {
            "registrant_ip": "1.2.3.4",
            },
        )

And you get back a data structure like:

    {
        "protocol": "XCP",
        "action": "reply",
        "response_code": "200",
        "is_success": 1,
        "attributes": {
            ...
            },
        }

Requirements
------------

 * xml.etree.ElementTree
 * httplib2

[opensrs]: http://opensrs.com
[xmlapi]: http://opensrs.com/docs/opensrsapixml/index.htm

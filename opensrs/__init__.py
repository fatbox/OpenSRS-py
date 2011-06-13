# Copyright (c) 2011, FatBox Inc.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from xml.etree.ElementTree import fromstring, tostring, SubElement, Element
from urllib import quote, urlencode

import httplib2
import hashlib

OPENSRS_SERVERS = {
        'production': 'https://rr-n1-tor.opensrs.net:55443',
        'test': 'https://horizon.opensrs.net:55443',
        }

OPENSRS_XML_HEADER = "<?xml version='1.0' encoding='UTF-8' standalone='no' ?><!DOCTYPE OPS_envelope SYSTEM 'ops.dtd'>"
OPENSRS_VERSION = '0.9'

class OpenSRSHTTPException(Exception):
    """
    Exception that signals there was an HTTP error during the post to
    the OpenSRS HTTPS API
    """
    pass

class OpenSRSXMLException(Exception):
    """
    Exception that signals there was an error parsing the XML returned
    from the OpenSRS HTTPS API
    """
    pass

class OpenSRS(object):
    """
    Main OpenSRS class.

    The majority of the functionality lies within the post method. It
    turns Python data structures to XML for OpenSRS and then converts
    back the other way for the response.

    Convenience functions exists for some functions, patches are welcome
    """

    H = httplib2.Http()
    server = None
    username = None
    private_key = None

    def __init__(self, username, private_key, test=True):
        """
        Constructor: sets the username, private key and test mode

        Parameters:
        username - your OpenSRS username
        private_key - your OpenSRS private key
        test - set to False for production operation
        """
        self.username = username
        self.private_key = private_key

        key = 'production'
        if test:
            key = 'test'
        self.server = OPENSRS_SERVERS[key]

    def post(self, action, object, attrs, extra_items = {}):
        """
        Post: send an action to the OpenSRS API

        Parameters:
        action - the name of the action (ie. sw_register, name_suggest, etc)
        object - the object type to operate on (ie. domain, trust_service)
        attrs - a data struct to construct the attributes from (see example)
        extra_items - any extra top level items (ie. registrant_ip)

        Example:
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
        """

        def xml_to_data(elm, is_list=False):
            """
            This converts an element that has a bunch of 'item' tags
            as children into a Python data structure.

            If is_list is true it is assumed that the child items all
            have numeric indices and should be treated as a list, else
            they are treated as a dict
            """
            if is_list:
                data = []
            else:
                data = {}

            for child in elm:
                if child.tag == 'item':

                    if len(child) > 0:
                        if child[0].tag == 'dt_assoc':
                            new_data = xml_to_data(child[0])
                        elif child[0].tag == 'dt_array':
                            new_data = xml_to_data(child[0], is_list=True)
                    else:
                        new_data = str(child.text)

                    key = child.get('key')
                    if is_list:
                        data.insert(int(key), new_data)
                    else:
                        data[key] = new_data

            return data

        def data_to_xml(elm, key, data):
            """
            data_to_xml adds a item sub element to elm and then sets the
            text if its not a list or dict, otherwise it recurses
            """
            item = SubElement(elm, 'item', { 'key': key })

            if isinstance(data, dict):
                data_to_dt_assoc(item, data)
            elif isinstance(data, list):
                data_to_dt_array(item, data)
            else:
                item.text = str(data)

            return item

        def data_to_dt_assoc(elm, data):
            """
            Adds an associative array of data in the format that opensrs
            requires, uses data_to_xml to recurse
            """
            _dt_assoc = SubElement(elm, 'dt_assoc')
            for key in data.keys():
                data_to_xml(_dt_assoc, key, data[key])

        def data_to_dt_array(elm, list):
            """
            Adds an list of data in the format that opensrs requires,
            uses data_to_xml to recurse
            """
            _dt_array = SubElement(elm, 'dt_array')
            key = 0
            for ent in list:
                data_to_xml(_dt_array, str(key), ent)
                key += 1

        # build our XML structure
        env = Element("OPS_envelope")

        # add the header
        header = SubElement(env, 'header')
        version = SubElement(header, 'version')
        version.text = str(OPENSRS_VERSION)

        # add the body
        body = SubElement(env, 'body')
        data_block = SubElement(body, 'data_block')
        data_to_dt_assoc(data_block, {
            'protocol': 'XCP',
            'action': action,
            'object': object,
            'attributes': attrs,
            })

        data = "%s%s" % (OPENSRS_XML_HEADER, tostring(env))

        # create our signature:
        # MD5(MD5(data + private_key)+private_key)
        signature = hashlib.md5("%s%s" % (hashlib.md5("%s%s" % (data, self.private_key)).hexdigest(), self.private_key)).hexdigest()

        # send our post
        try:
            resp, content = self.H.request(self.server, "POST",
                    body=data,
                    headers={
                        'Content-Type': 'text/xml',
                        'X-Username': self.username,
                        'X-Signature': signature,
                        'Content-Length': str(len(data)),
                        })
        except httplib2.ServerNotFoundError:
            raise OpenSRSHTTPException("DNS is not working for us.")
        except AttributeError:
            raise OpenSRSHTTPException("Are we offline?")

        if resp.status == 200:
            # parse the XML response
            dom = fromstring(content)

            # check the version
            version = dom.find('header/version')
            if version == None:
                raise OpenSRSXMLException("Response did not contain a version")
            if version.text > OPENSRS_VERSION:
                raise OpenSRSXMLException("Response version is newer than we understand! Response: %s -- Supported: %s" % (version.text, OPENSRS_VERSION))

            # find our response data
            data_block = dom.find('body/data_block/dt_assoc')
            if data_block == None:
                raise OpenSRSXMLException("Response did not contain valid data (could not find body/data_block/dt_assoc)")

            # convert
            data = xml_to_data(data_block)

            return data
        else:
            raise OpenSRSHTTPException("Status returned from POST was not 200")


    def name_suggest(self, query, tlds=[".COM", ".NET", ".ORG", ".INFO", ".BIZ", ".US", ".MOBI"]):
        """
        Shortcut for the name_suggest function
        """
        return self.post("name_suggest", "domain", {
            "searchstring": query,
            "max_wait_time": 3,
            "tlds": tlds,
            })

    def balance(self):
        """
        Shortcut to get the balance.
        """
        return self.post("get_balance", "balance", {})

    def get_domain_price(self, domain_name, period=1, renewal=False):
        """
        Determine the current price for a particular domain.

        domain_name: Must be a full domain name, e.g. 'example.com'
        period: How many years
        renewal: Is this a renewal?
        """
        return self.post("get_price", "domain", {
            "domain": domain_name,
            "period": period,
            "reg_type": "new" if not renewal else "renewal",
            })

    def domain_register(self, domain_name, owner_contact, period, reg_username, reg_password, extra_items, auto_renew=False):
        """
        Register a new domain, for the period specified to the owner specified.

        Also sets the various contacts up as well.
        The owner_contact will be used for the admin and billing contact.

        The tech_contact will assumed to be the default associated with the OpenSRS account.

        reg_username, reg_password these are the registrants username and password. I do not know why they are needed either.

        'extra_items' is used for some zones which have additional requirements (e.g. '.au' domains)

        """
        return self.post("sw_register", "domain", {
                "auto_renew": auto_renew,
                "contact_set": {
                    "owner": owner_contact,
                    "admin": owner_contact,
                    "billing": owner_contact,
                },
                "custom_nameservers": 0,
                "custom_tech_contact": 0,
                "domain": domain_name,
                "f_lock_domain": 1,
                "f_whois_privacy": 1,
                "period": period,
                "reg_username": reg_username,
                "reg_password": reg_password,
                "reg_type": "new",
            }, extra_items )

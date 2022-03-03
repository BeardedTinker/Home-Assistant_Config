"""Helper functions for Mikrotik Router."""


# ---------------------------
#   format_attribute
# ---------------------------
def format_attribute(attr):
    res = attr.replace("-", " ")
    res = res.capitalize()
    res = res.replace(" ip ", " IP ")
    res = res.replace(" mac ", " MAC ")
    res = res.replace(" mtu", " MTU")
    res = res.replace("Sfp", "SFP")
    res = res.replace("Poe", "POE")
    res = res.replace(" tx", " TX")
    res = res.replace(" rx", " RX")
    return res


# ---------------------------
#   format_value
# ---------------------------
def format_value(res):
    res = res.replace("dhcp", "DHCP")
    res = res.replace("dns", "DNS")
    res = res.replace("capsman", "CAPsMAN")
    res = res.replace("wireless", "Wireless")
    res = res.replace("restored", "Restored")
    return res

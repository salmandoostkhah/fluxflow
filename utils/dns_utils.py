from dns import resolver

def get_system_dns():
    try:
        r = resolver.Resolver()
        nameservers = r.nameservers
        return nameservers[0] if nameservers else "Unknown"
    except Exception:
        return "Unknown"
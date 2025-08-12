import re

def refang_ioc(ioc_value: str, ioc_type: str) -> str:
    """
    Konvertiert "defangte" (entschaerfte) IOCs in ihr Standardformat.
    Behandelt gaengige Maskierungen wie [.] oder hxxp://.
    """
    if not isinstance(ioc_value, str):
        return ""

    refanged = ioc_value.replace("[.]", ".").replace("(.)", ".")
    refanged = refanged.replace("[:]", ":")

    if ioc_type == "email":
        refanged = refanged.replace("[@]", "@")

    if ioc_type in ["domain", "url", "email"]:
        refanged = re.sub(r'^(hxxp|h__p)', 'http', refanged, flags=re.IGNORECASE)
        if refanged.endswith('.') and not refanged.endswith('..'):
            refanged = refanged[:-1]

    elif ioc_type == "ipv4":
        refanged = refanged.replace(" ", ".")

    return refanged.strip()
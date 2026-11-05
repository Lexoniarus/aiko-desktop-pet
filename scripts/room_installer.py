"""Generate a removable Web Clip, not a device-management enrollment."""

from __future__ import annotations

import plistlib
import uuid
from urllib.parse import urlsplit, urlunsplit

PROFILE_IDENTIFIER = "de.lexoniarus.aiko.room.installation"


def starter_address(value: str) -> str:
    parts = urlsplit(value)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
        or not parts.path.endswith("/")
    ):
        raise ValueError("Starter address must be a stable HTTPS directory URL")
    return urlunsplit(parts)


def installation_profile(address: str, icon: bytes) -> bytes:
    address = starter_address(address)
    if not icon.startswith(b"\x89PNG\r\n\x1a\n") or len(icon) > 1024 * 1024:
        raise ValueError("Profile requires the existing PNG application icon")
    identity = PROFILE_IDENTIFIER + ":" + address
    clip = {
        "PayloadType": "com.apple.webClip.managed",
        "PayloadVersion": 1,
        "PayloadIdentifier": PROFILE_IDENTIFIER + ".webclip",
        "PayloadUUID": str(uuid.uuid5(uuid.NAMESPACE_URL, identity + ":clip")),
        "PayloadDisplayName": "Aiko",
        "Label": "Aiko",
        "URL": address,
        "FullScreen": True,
        "Precomposed": True,
        "IsRemovable": True,
        "IgnoreManifestScope": False,
        "Icon": icon,
    }
    return plistlib.dumps(
        {
            "PayloadType": "Configuration",
            "PayloadVersion": 1,
            "PayloadIdentifier": PROFILE_IDENTIFIER,
            "PayloadUUID": str(uuid.uuid5(uuid.NAMESPACE_URL, identity)),
            "PayloadDisplayName": "Aiko installieren",
            "PayloadDescription": (
                "Fügt das Aiko-Symbol hinzu. Beim ersten Start lädt Aiko ihre "
                "Programmdaten einmalig aus dem Internet. Danach läuft sie lokal. "
                "Dieses Profil enthält ausschließlich den entfernbaren Web Clip."
            ),
            "PayloadOrganization": "Aiko Desktop Pet",
            "PayloadRemovalDisallowed": False,
            "PayloadContent": [clip],
        },
        fmt=plistlib.FMT_XML,
        sort_keys=True,
    )


def installation_instructions(version: str) -> bytes:
    return (
        f"AIKO AUF DEM IPAD INSTALLIEREN — {version}\n\n"
        "1. Diese ZIP in Dateien entpacken.\n"
        "2. Aiko-installieren.mobileconfig öffnen.\n"
        "3. In Einstellungen das geladene Profil auswählen und Installieren\n"
        "   bestätigen. Gegebenenfalls den iPad-Code eingeben.\n"
        "4. Das neue Aiko-Symbol auf dem Home-Bildschirm antippen.\n"
        "5. Für die erste Einrichtung online bleiben. Aiko lädt ihr Paket\n"
        "   automatisch. Danach läuft sie auf dem iPad, auch offline.\n\n"
        "Du musst keine Adresse öffnen und keine Runtime-ZIP auswählen.\n"
        "Das Profil fügt ausschließlich Aikos entfernbares Startsymbol hinzu;\n"
        "es enthält keine Geräteverwaltung, Zertifikate oder VPN-Einstellungen.\n"
        "Das selbst erzeugte Profil ist nicht signiert. Die Bestätigung\n"
        "in den iPad-Einstellungen ist erforderlich.\n\n"
        "Falls Dateien das Profil nur anzeigt, teile die .mobileconfig-Datei\n"
        "als Anhang an Apple Mail und öffne sie dort. Dieser von Apple\n"
        "dokumentierte Übergabeweg bleibt als Ausweichmöglichkeit vorhanden.\n\n"
        "Die erstmalige Profilinstallation und spätere Betriebssystem-Updates\n"
        "müssen auf dem echten iPad geprüft werden.\n"
    ).encode("utf8")

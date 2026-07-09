pragma Singleton
import QtQuick
import QtQuick.Controls

/**
 * Singleton that gathers useful colors, shades and system palettes.
 */

QtObject {
    readonly property color shotColor: "#1565C0"
    readonly property color assetColor: "#6A1B9A"
    readonly property color sequenceColor: "#00695C"
    readonly property color versionColor: "#BF360C"
    readonly property color defaultEntityColor: "#424242"

    function entityColor(entityType) {
        switch ((entityType || "").toLowerCase()) {
            case "shot":     return shotColor
            case "asset":    return assetColor
            case "sequence": return sequenceColor
            case "version":  return versionColor
            default:         return defaultEntityColor
        }
    }

    function _statusColor(status) {
        if (!status) return "transparent"
        var s = status.toLowerCase()
        if (s === "wtg"  || s === "Waiting To Start"   ) return "#505050"
        if (s === "hld"  || s === "On Hold"            ) return "#5a4120"
        if (s === "rdy"  || s === "Ready To Start"     ) return "#18b38c"
        if (s === "ip"   || s === "In Progress"        ) return "#dfb707"
        if (s === "rev"  || s === "Pending Review"     ) return "#d87a00"
        if (s === "iapr" || s === "Internally Approved") return "#2279ca"
        if (s === "apr"  || s === "Client Approved"    ) return "#44ce21"
        return "#303030"
    }

    function toRgb(color) {
        return [
            parseInt(color.toString().substr(1, 2), 16) / 255, 
            parseInt(color.toString().substr(3, 2), 16) / 255, 
            parseInt(color.toString().substr(5, 2), 16) / 255
        ]
    }

    function interpolate(c1, c2, u) {
        let rgb1 = toRgb(c1)
        let rgb2 = toRgb(c2)
        return Qt.rgba(
            rgb1[0] * (1 - u) + rgb2[0] * u,
            rgb1[1] * (1 - u) + rgb2[1] * u,
            rgb1[2] * (1 - u) + rgb2[2] * u
        )
    }
}

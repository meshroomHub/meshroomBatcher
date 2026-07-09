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
}

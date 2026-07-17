pragma Singleton
import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material 2.15

/**
 * Singleton that gathers useful colors, shades and system palettes.
 */

Control {

    // --- Color Palette ---
    property bool isDark: Material.theme === Material.Dark
    // Specific colors depending on the theme
    property color backgroundColor:    isDark ? "#2a2a2a" : "#ddd"
    property color accent:             isDark ? "#469adf" : "#eb7ec6"
    property color primary:            isDark ? "#2353ad" : "#c0228b"
    property color secondary:          isDark ? "#052747" : "#f092d1"
    property color textOnSecondary:    isDark ? "#d0e4ff" : "#2a2546"
    property color textColor:          isDark ? "#ccc"    : "#333"
    property color hoveredText:        isDark ? "#ffffff" : "#462e44"
    property color primaryText:        isDark ? "#ccc"    : "#fff"  // main text
    property color secondaryText:      isDark ? "#999"    : "#bbb"  // disabled text on header
    property color tertiaryText:       isDark ? "#aaa"    : "#888"  // subtle text over backgroundColor
    property color grey:               isDark ? "#555"    : "#777"
    property color panelBackground:    isDark ? "#1e1e1e" : "#eee"
    property color panelBorder:        isDark ? "#333"    : "#ccc"
    property color headerBackground:   isDark ? "#242424" : "#ccc"
    property color selectedBackground: isDark ? "#1a3a6e" : "#cfe0f7"
    property color hoverBackground:    isDark ? "#2a2a2a" : "#e2e2e2"
    property color rowHoverBackground: isDark ? "#262626" : "#e6e6e6"
    property color separator:          isDark ? "#2a2a2a" : "#ccc"
    property color badgeBackground:    isDark ? "#333"    : "#ccc"
    property color placeholderText:    isDark ? "#666"    : "#999"
    readonly property color startButton: "#43d668"
    readonly property color startButtonText: "#424242"

    Behavior on backgroundColor {
        ColorAnimation { duration: 150 }
    }
    Behavior on accent {
        ColorAnimation { duration: 150 }
    }
    Behavior on primary {
        ColorAnimation { duration: 150 }
    }

    SystemPalette {
        id: sys
        colorGroup: SystemPalette.Active
    }
    SystemPalette {
        id: sysDisabled
        colorGroup: SystemPalette.Disabled
    }

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

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import Qt.labs.platform 1.0 as Platform
import MaterialIcons 2.2

Item {
    id: root
    property var paramData

    width: parent ? parent.width : 0
    // height: rowLayout.implicitHeight + 8
    height: rowLayout.implicitHeight + 16

    property string nodeParam: paramData.nodeParam
    property var currentValue: root._getDefaultValue()

    function _getDefaultValue() {
        switch (paramData.type) {
            case "bool":   return paramData.default === true || paramData.default === "true"
            case "int":    return parseInt(paramData.default)   || 0
            case "float":  return parseFloat(paramData.default) || 0.0
            case "choice": return paramData.default || (paramData.choices[0] || "")
            default:       return String(paramData.default || "")
        }
    }

    Connections {
        target: widgetLoader.item
        ignoreUnknownSignals: true
        function onSelectedValueChanged() {
            root.currentValue = widgetLoader.item.selectedValue
        }
    }

    // --- Row Container ---

    // Border
    Rectangle {
        id: outlineContainer
        anchors.fill: parent
        anchors.margins: 4
        color: "transparent"
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.15)
        radius: 6
    }

    // Items in the row
    RowLayout {
        id: rowLayout
        
        anchors.fill: outlineContainer
        anchors.leftMargin: 12
        anchors.rightMargin: 12
        
        spacing: 16

        RowLayout {
            Layout.preferredWidth: 220
            spacing: 4

            Label {
                text: root.paramData.nodeName
                font.pixelSize: 13
                font.weight: Font.Medium
                elide: Text.ElideRight
                color: "#aaaaaa"
            }
            Label {
                text: MaterialIcons.chevron_right
                font.family: MaterialIcons.fontFamily
                font.pixelSize: 13
                color: "#666666"
            }
            Label {
                text: root.paramData.paramName
                font.pixelSize: 13
                font.weight: Font.Medium
                elide: Text.ElideRight
                Layout.fillWidth: true
            }
        }

        // Widget
        Loader {
            id: widgetLoader
            Layout.fillWidth: true
            Layout.topMargin: 6
            Layout.bottomMargin: 6
            sourceComponent: {
                if (!root.paramData) return null;
                switch (root.paramData.type) {
                    case "bool":   return boolWidget
                    case "int":    return intWidget
                    case "float":  return floatWidget
                    case "choice": return choiceWidget
                    case "file":   return fileWidget
                    default:       return stringWidget
                }
            }

            Connections {
                target: widgetLoader.item
                ignoreUnknownSignals: true
                function onCurrentValueChanged() {
                    root.currentValue = widgetLoader.item.currentValue
                }
            }
        }
    }

    // --- Widgets ---

    // String
    Component {
        id: stringWidget
        TextField {
            property var currentValue: text
            text: String(root.paramData.default || "")
            placeholderText: "Enter value…"
            selectByMouse: true
        }
    }

    // File
    Component {
        id: fileWidget
        RowLayout {
            property var currentValue: pathField.text
            spacing: 6
            TextField {
                id: pathField
                Layout.fillWidth: true
                text: String(root.paramData.default || "")
                placeholderText: "Path…"
                selectByMouse: true
            }
            Button {
                text: "…"
                flat: true
                ToolTip.text: "Browse…"
                ToolTip.visible: hovered
                onClicked: folderDialog.open()
            }
            Platform.FolderDialog {
                id: folderDialog
                onAccepted: {
                    pathField.text = folder.toString().replace("file://", "")
                }
            }
        }
    }

    // Int
    Component {
        id: intWidget
        SpinBox {
            property var currentValue: value
            value: parseInt(root.paramData.default) || 0
            from: -999999; to: 999999
            editable: true
        }
    }

    // Float
    Component {
        id: floatWidget
        TextField {
            property var currentValue: parseFloat(text) || 0.0
            text: String(root.paramData.default || "0.0")
            placeholderText: "0.0"
            inputMethodHints: Qt.ImhFormattedNumbersOnly
            validator: DoubleValidator { decimals: 6 }
            selectByMouse: true
        }
    }

    // Bool
    Component {
        id: boolWidget
        Switch {
            property var currentValue: checked
            checked: root.paramData.default === true || root.paramData.default === "true"
        }
    }

    // Choice
    Component {
        id: choiceWidget
        ComboBox {
            property var selectedValue: currentText
            model: root.paramData.choices || []
            currentIndex: {
                var idx = find(root.paramData.default)
                return idx >= 0 ? idx : 0
            }
        }
    }
}

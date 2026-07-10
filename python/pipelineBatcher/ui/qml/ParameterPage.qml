import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import Qt.labs.platform 1.0 as Platform
import MaterialIcons 2.2

Item {
    id: root

    property var paramInfos: []  // { type, nodeParam, default, choices }

    // --- Build paramInfos ---

    onVisibleChanged: {
        if (visible)
            _buildParamInfos()
    }

    Component.onCompleted: {
        if (visible)
            _buildParamInfos()
    }

    function _buildParamInfos() {
        var params = pipelineBatcherBackend.templateParameters || []
        var infos = []

        for (var i = 0; i < params.length; i++) {
            var nodeParam = params[i]
            var info = {
                nodeParam: nodeParam,
                type:      "string",
                default:   "",
                choices:   []
            }

            try {
                var raw    = pipelineBatcherBackend.getParamInfo(nodeParam)
                var parsed = JSON.parse(raw)
                info.type = parsed.type || "unknown"
                info.nodeName  = parsed.node      || ""
                info.paramName = parsed.paramName || ""
                info.default = parsed.default !== undefined ? parsed.default : ""
                info.choices = parsed.choices  || []
            } catch(e) {
                console.warn("[ParameterPage] getParamInfo failed for", nodeParam, e)
            }

            if (!info.type || info.type !== "unknown") {
                infos.push(info)
            }
        }

        paramInfos = infos
    }

    // --- Collect values set by the user and launch instanciation ---
    function _collectAndStart() {
        var result = {}
        for (var i = 0; i < paramRepeater.count; i++) {
            var item = paramRepeater.itemAt(i)
            if (item && item.nodeParam !== undefined) {
                result[item.nodeParam] = item.currentValue
            }
        }
        pipelineBatcherBackend.setParameters(JSON.stringify(result))
        pipelineBatcherBackend.next()
    }

    // -- Parameter Delegate --
    Component {
        id: paramDelegateComponent

        ParameterDelegate {
            paramData: modelData 
        }
    }

    // --- UI ---
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 12

        Label {
            visible: paramInfos.length > 0
            text: paramInfos.length + " parameter(s) to configure"
            font.pixelSize: 12
            color: "#aaa"
            Layout.fillWidth: true
        }

        // Parameter form
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            // Placeholder
            Label {
                anchors.centerIn: parent
                visible: paramInfos.length === 0
                text: "No parameters - ready to start."
                font.pixelSize: 15
                color: "#aaa"
            }

            ScrollView {
                anchors.fill: parent
                visible: paramInfos.length > 0
                clip: true

                Column {
                    width:   parent.width
                    spacing: 16

                    Repeater {
                        id: paramRepeater
                        model: paramInfos
                        delegate: paramDelegateComponent
                    }
                }
            }
        }

        // Bottom bar
        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: bottomRow.implicitHeight

            RowLayout {
                id: bottomRow
                anchors.fill: parent

                NavigationButton {
                    text: "Cancel"
                    flat: true
                    Material.background: hovered ? Material.Pink : Material.Red
                    highlighted: hovered
                    onClicked: pipelineBatcherBackend.cancel()
                    textColor: "#000000"
                }

                NavigationButton {
                    text: "Back"
                    navIcon: MaterialIcons.chevron_left
                    navIconPosition: "left"
                    flat: true
                    highlighted: hovered
                    onClicked: pipelineBatcherBackend.back()
                }

                Item { Layout.fillWidth: true }

                NavigationButton {
                    text: "Start"
                    navIcon: MaterialIcons.play_arrow
                    navIconPosition: "left"
                    Material.background: hovered ? "#43d668" : "#2a67ad"
                    Material.foreground: hovered ? "#424242" : "#e0e0e0"
                    scale: hovered ? 1.05 : 1.0
                    Behavior on scale {
                        NumberAnimation { duration: 100 }
                    }
                    highlighted: hovered
                    onClicked: _collectAndStart()
                }
            }
        }
    }
}
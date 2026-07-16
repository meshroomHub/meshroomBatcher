import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

import MaterialIcons 2.2

Item {
    id: root

    //--- State ---
    property var templates: []
    property int selectedIndex: -1

    // Load templates when page becomes active
    onVisibleChanged: {
        if (visible && templates.length === 0) {
            _loadTemplates()
        }
    }

    Component.onCompleted: _loadTemplates()

    function _loadTemplates() {
        var tplJsonList = pipelineBatcherBackend.listTemplates()
        try {
            templates = JSON.parse(tplJsonList)
        } catch(e) {
            templates = []
        }
    }

    // --- UI ---
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 12

        // Title
        Label {
            text: "Select a pipeline template"
            font.pixelSize: 16
            font.weight: Font.Medium
        }

        Label {
            text: templates.length === 0
                  ? "No templates found. Add JSON files to the 'templates' folder."
                  : templates.length + " template(s) available"
            font.pixelSize: 12
            color: "#aaa"
        }

        // Template list
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            ListView {
                id: listView
                model: templates
                spacing: 8
                delegate: templateListDelegate
            }
        }

        // Bottom bar
        RowLayout {
            Layout.fillWidth: true

            NavigationButton {
                text: "Cancel"
                flat: true
                Material.background: hovered ? Material.Pink : Material.Red
                highlighted: hovered
                onClicked: pipelineBatcherBackend.cancel()
                textColor: "black"
            }

            Item { Layout.fillWidth: true }
            
            NavigationButton {
                text: "Next"
                navIcon: MaterialIcons.chevron_right
                navIconPosition: "right"
                highlighted: hovered
                enabled: selectedIndex >= 0
                onClicked: {
                    pipelineBatcherBackend.selectTemplate(templates[selectedIndex]["index"])
                }
            }
        }
    }

    // --- Template delegate ---
    Component {
        id: templateListDelegate

        TemplateDelegate {
            width: listView.width
            templateIndex: index
            templateModelData: modelData
            selectedIndex: root.selectedIndex

            onSelected:  (idx) => {
                root.selectedIndex = idx
            }

            onConfirmed: (idx) => {
                root.selectedIndex = idx
                pipelineBatcherBackend.selectTemplate(templates[idx]["index"])
            }
        }
    }
}

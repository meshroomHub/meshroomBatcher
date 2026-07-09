import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15

Item {
    id: root

    required property var wizard

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
            console.warn("Failed to parse template list:", e)
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

            Button {
                text: "Cancel"
                flat: true
                onClicked: wizard.cancel()
            }
            Item { Layout.fillWidth: true }
            Button {
                text: "Next ›"
                Material.accent: Material.Blue
                highlighted: true
                enabled: selectedIndex >= 0
                onClicked: {
                    wizard.template = templates[selectedIndex]
                    wizard.next()
                }
            }
        }
    }

    // --- Template delegate ---
    Component {
        id: templateListDelegate

        TemplateDelegate {
            width: listView.width
            wizard: root.wizard
            templateIndex: index
            templateModelData: modelData
            selectedIndex: root.selectedIndex

            onSelected:  (idx) => {
                root.selectedIndex = idx
            }

            onConfirmed: (idx) => {
                root.selectedIndex = idx
                wizard.template = templates[idx]
                wizard.next()
            }
        }
    }
}

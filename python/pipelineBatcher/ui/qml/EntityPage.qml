// EntityPage.qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import QtQuick.Controls.Material 2.15
import MaterialIcons 2.2
import PBComponents 1.0

Item {
    id: root

    // --- State ---
    property string entityType: ""
    property var treeData: []
    property bool treeDataLoading: false
    property var entityList: []
    property var checkedIds: ({})
    property string activeGroupId: ""

    readonly property int checkedCount: Object.keys(checkedIds).length

    // Refresh tree whenever the page becomes visible with a new entityType
    onVisibleChanged: {
        if (visible && entityType !== "")
            _loadTree()
    }

    onEntityTypeChanged: {
        if (visible && entityType !== "")
            _loadTree()
    }

    Component.onCompleted: {
        if (visible && entityType !== "")
            _loadTree()
    }

    // Theme
    property bool darkTheme: Material.theme == Material.Dark

    // --- Data loading ---

    function _loadTree() {
        root.treeDataLoading = true
        checkedIds = {}
        entityList  = []
        treeData    = []
        activeGroupId = ""

        var raw = pipelineBatcherBackend.getEntitiesTree(entityType)
        try {
            if (!raw || raw === "" || raw === "null") {
                console.error("getEntitiesTree: empty or null raw string")
                treeData = []
                return
            }
            treeData = JSON.parse(raw)
        } catch(e) {
            console.error("JSON.parse failed:", e)
            console.error("raw string was:", raw)
            treeData = []
        }

        // Auto-select first group
        if (treeData.length > 0) {
            _selectGroup(treeData[0].id)
        }

        root.treeDataLoading = false
    }

    function _selectGroup(groupId) {
        activeGroupId = groupId
        entityList = []

        var raw = pipelineBatcherBackend.fetchEntitiesByGroup(entityType, groupId)
        try {
            entityList = JSON.parse(raw)
        } catch(e) {
            entityList = []
        }
    }

    function _toggleEntity(entityId) {
        var updated = Object.assign({}, checkedIds)
        if (updated[entityId])
            delete updated[entityId]
        else
            updated[entityId] = true
        checkedIds = updated
    }

    function _toggleAll(select) {
        var updated = Object.assign({}, checkedIds)
        if (select) {
            for (var i = 0; i < entityList.length; i++)
                updated[entityList[i].id] = true
        } else {
            updated = {}
        }
        checkedIds = updated
    }

    function _commit() {
        // Send selected ids to the backend and switch to the next layout
        var ids = Object.keys(checkedIds)
        pipelineBatcherBackend.setSelectedEntities(JSON.stringify(ids))
    }

    // --- Layout ---
    ColumnLayout {
        id: entityPageLayout
        visible: !root.treeDataLoading
        anchors.fill: parent
        anchors.margins: 20
        spacing: 12

        property color textColor: darkTheme ? "#888" : "#222"

        // Top bar
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                height: 26
                width: entityTypeBadgeLabel.implicitWidth + 40
                radius: 13
                color: PBColors.entityColor(root.entityType)

                Label {
                    id: entityTypeBadgeLabel
                    anchors.centerIn: parent
                    text: root.entityType || "—"
                    font.pixelSize: 12
                    font.weight: Font.Medium
                    color: "white"
                }
            }

            Label {
                text: root.checkedCount > 0
                        ? root.checkedCount + " selected"
                        : entityList.length + " entities in group"
                font.pixelSize: 13
                color: root.checkedCount > 0 ? Material.accent : (root.darkTheme ? "#aaa" : "#666")
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "Select all"
                flat: true
                font.pixelSize: 12
                enabled: entityList.length > 0
                onClicked: root._toggleAll(true)
            }
            Button {
                text: "Deselect all"
                flat: true
                font.pixelSize: 12
                enabled: root.checkedCount > 0
                onClicked: root._toggleAll(false)
            }
        }

        // Main content
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 12

            // --- Left panel: tree view ---
            Rectangle {
                Layout.preferredWidth: 200
                Layout.minimumWidth: 140
                Layout.fillHeight: true
                radius: 8
                color: root.darkTheme ? "#1e1e1e" : "#eee"
                border.color: "#333"
                border.width: 1
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 1
                    spacing: 0

                    Label {
                        Layout.fillWidth: true
                        text: "Browse"
                        font.pixelSize: 11
                        font.weight: Font.Medium
                        color: entityPageLayout.textColor
                        leftPadding: 12
                        topPadding: 10
                        bottomPadding: 8
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: "#333"
                    }

                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                        ListView {
                            id: treeView
                            model: root.treeData
                            spacing: 0
                            delegate: EntityTreeNode {
                                width: treeView.width
                                nodeData: modelData
                                activeGroupId: root.activeGroupId
                                depth: 0
                                onGroupSelected: (id) => root._selectGroup(id)
                                textColor: entityPageLayout.textColor
                            }
                        }
                    }
                }
            }

            // --- Right panel: entity list ---
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 8
                color: root.darkTheme ? "#1e1e1e" : "#eee"
                border.color: "#333"
                border.width: 1
                clip: true

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 1
                    spacing: 0

                    // Column headers
                    Rectangle {
                        Layout.fillWidth: true
                        height: 34
                        // color: "#242424"
                        color: root.darkTheme ? "#242424" : "#ccc"
                        radius: 7

                        Rectangle {
                            anchors.bottom: parent.bottom
                            width: parent.width
                            height: parent.radius
                            color: parent.color
                        }

                        RowLayout {
                            anchors {
                                fill: parent
                                leftMargin: 44
                                rightMargin: 12
                            }
                            spacing: 0

                            Label {
                                Layout.preferredWidth: 200
                                Layout.fillWidth: true
                                text: "Name"
                                font.pixelSize: 11
                                font.weight: Font.Medium
                                color: entityPageLayout.textColor
                            }
                            Label {
                                Layout.preferredWidth: 90
                                text: "Status"
                                font.pixelSize: 11
                                font.weight: Font.Medium
                                color: entityPageLayout.textColor
                            }
                            Label {
                                Layout.fillWidth: true
                                text: "Description"
                                font.pixelSize: 11
                                font.weight: Font.Medium
                                color: entityPageLayout.textColor
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: "#333"
                    }

                    // Empty / Placeholder state
                    Item {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        visible: entityList.length === 0

                        Column {
                            anchors.centerIn: parent
                            spacing: 12

                            Label {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: root.activeGroupId === ""
                                    ? "Select a group on the left."
                                    : "No entities found in this group."
                                font.pixelSize: 13
                                color: "#666"
                            }
                        }
                    }

                    // Entity rows
                    ScrollView {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        visible: entityList.length > 0
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                        ListView {
                            id: entityListView
                            model: root.entityList
                            spacing: 0
                            delegate: EntityDelegate {
                                width: entityListView.width
                                entityData: modelData
                                checked: !!root.checkedIds[modelData.id]
                                onToggled: (id) => root._toggleEntity(id)
                                textColor: entityPageLayout.textColor
                            }
                        }
                    }
                }
            }
        }

        // --- Selection summary strip ---
        EntitySelectionSummary {
            Layout.fillWidth: true
            visible: root.checkedCount > 0
            checkedIds: root.checkedIds
            entityType: root.entityType
            onEntityDeselected: (id) => {
                root._toggleEntity(id)
            }
        }

        // --- Bottom navigation bar ---
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

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

            Label {
                visible: root.checkedCount === 0
                text: "Select at least one entity to continue"
                font.pixelSize: 12
                color: "#666"
            }

            NavigationButton {
                text: "Next"
                navIcon: MaterialIcons.chevron_right
                navIconPosition: "right"
                Material.accent: "#230f91"
                highlighted: hovered
                enabled: root.checkedCount > 0
                onClicked: root._commit()
            }
        }
    }
}
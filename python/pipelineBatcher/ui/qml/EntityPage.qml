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

    // --- Data loading ---

    function _isArrayLike(v) {
        return !!v && typeof v.length === "number"
    }

    // Keep only items that have children.
    function _pruneLeaves(items) {
        var out = []
        if (!_isArrayLike(items)) return out
        for (var i = 0; i < items.length; i++) {
            var n = items[i]
            if (_isArrayLike(n.children) && n.children.length > 0) {
                var prunedChildren = _pruneLeaves(n.children)
                out.push({
                    id: n.id,
                    label: n.label,
                    icon: n.icon,
                    children: prunedChildren,
                    entityCount: n.children.length
                })
            }
        }
        return out
    }

    function _loadTree() {
        root.treeDataLoading = true
        checkedIds = {}
        entityList  = []
        treeData    = []
        activeGroupId = ""

        var raw = pipelineBatcherBackend.getEntitiesTree()
        try {
            if (!raw || raw === "" || raw === "null") {
                console.error("getEntitiesTree: empty or null raw string")
                treeData = []
                return
            }
            var parsedTree = JSON.parse(raw)
            treeData = _pruneLeaves(parsedTree)
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

        var raw = pipelineBatcherBackend.fetchEntitiesByGroup(groupId)
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

        // Top bar
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                height: 26
                implicitWidth: entityTypeBadgeLabel.implicitWidth + 20
                radius: 13
                color: PBColors.entityColor(root.entityType)

                Label {
                    id: entityTypeBadgeLabel
                    anchors.centerIn: parent
                    text: root.entityType || "—"
                    font.pixelSize: 12
                    font.weight: Font.Medium
                    color: PBColors.primaryText
                }
            }

            Label {
                text: root.checkedCount > 0
                        ? root.checkedCount + " selected"
                        : entityList.length + " entities in group"
                font.pixelSize: 13
                color: root.checkedCount > 0 ? Material.accent : PBColors.tertiaryText
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
                color: PBColors.panelBackground
                border.color: PBColors.panelBorder
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
                        color: PBColors.tertiaryText
                        leftPadding: 12
                        topPadding: 10
                        bottomPadding: 8
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: PBColors.panelBorder
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
                color: PBColors.panelBackground
                border.color: PBColors.panelBorder
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
                        color: PBColors.headerBackground
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
                                text: "Entities"
                                font.pixelSize: 11
                                font.weight: Font.Medium
                                color: PBColors.tertiaryText
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        height: 1
                        color: PBColors.panelBorder
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
                                color: PBColors.placeholderText
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
                textColor: "black"
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
                color: PBColors.placeholderText
            }

            NavigationButton {
                text: "Next"
                navIcon: MaterialIcons.chevron_right
                navIconPosition: "right"
                highlighted: hovered
                enabled: root.checkedCount > 0
                onClicked: root._commit()
            }
        }
    }
}
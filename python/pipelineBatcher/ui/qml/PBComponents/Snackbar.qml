import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Material 2.15

Rectangle {
    id: root
    
    property bool active: false
    property real amplitude: 0.15
    
    // --- State ---
    property real progress: 1.0  // 1.0 -> 0.0 (Remaining time)
    property real wave: 0.0      // cosine wave
    readonly property real breathe: (Math.cos(wave) + 1.0) / 2.0 
    readonly property real dimFactor: Math.min(1.0, progress / 0.20)

    // --- Color palette ---
    property bool lightMode: (Material.theme === Material.Light)
    readonly property color currentBg:   lightMode ? "#ffb9f6" : "#101069"
    readonly property color currentText: lightMode ? "#311861" : "#FFFFFF"
    readonly property color accentColor: lightMode ? "#a937b8" : "#2979FF"

    // --- Color animations ---
    color: currentBg
    width: Math.min(snackLabel.implicitWidth + 40, parent.width - 32)
    height: 42
    radius: 8

    // Border
    border.width: 1.5
    border.color: {
        // Breathing color
        let accent = PBColors.interpolate(accentColor, Qt.lighter(accentColor, 1.25), breathe);
        // Blend into the background color with progress
        return PBColors.interpolate(currentBg, accent, dimFactor);
    }

    // --- Position animations ---
    opacity: active ? 1.0 : 0.0
    visible: opacity > 0
    Behavior on opacity { NumberAnimation { duration: 150 } }

    scale: active ? 1.0 : 0.9
    Behavior on scale {
        NumberAnimation { 
            duration: 200
            easing.type: root.active ? Easing.OutBack : Easing.OutCubic 
        }
    }

    transform: Translate {
        y: root.active ? 0 : 10
        Behavior on y {
            NumberAnimation { 
                duration: 200
                easing.type: root.active ? Easing.OutBack : Easing.OutCubic 
            }
        }
    }

    // --- Heartbeat animation ---
    NumberAnimation {
        id: waveAnim
        target: root
        property: "wave"
        from: 0
        to: Math.PI * 2
        duration: 3000
        loops: Animation.Infinite
        running: root.active
    }

    // --- UI Layout ---
    Label {
        id: snackLabel
        anchors.centerIn: parent
        color: root.currentText
        font.pixelSize: 13
        font.bold: true
    }

    // Disable on click
    MouseArea {
        anchors.fill: parent
        onClicked: root.active = false
    }

    // --- Function show triggers the snackbar to show up ---
    function show(msg, duration = 3000) {
        snackLabel.text = msg
        active = true
        
        // Instantly reset progress to 1.0
        progress = 1.0 
        
        progressAnimation.stop()
        progressAnimation.duration = duration
        progressAnimation.start()

        hideTimer.interval = duration
        hideTimer.restart()
    }

    function hide() {
        root.active = false
    }

    PropertyAnimation {
        id: progressAnimation
        target: root
        property: "progress"
        to: 0.0
        easing.type: Easing.Linear
    }

    Timer {
        id: hideTimer
        onTriggered: root.active = false
    }
}
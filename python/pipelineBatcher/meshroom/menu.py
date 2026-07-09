"""
Add a menu for prod tools.
"""

import logging

from meshroom.api import register_menu, Menu, MenuCallback


class OpenTemplateBatcher(MenuCallback):
    def __call__(self, menu, app, **kwargs):
# 
# Create the menu
# 

batcher_menu = Menu("Batcher", tooltip="Meshroom production tools")

batcher_menu.addButton(
    "batcher",
    label="Pipeline Batcher UI",
    callback=OpenPipelineBatcher(),
    tooltip="Open the TemplateBatcher UI.",
    shortcut="Ctrl+Shift+B",
)

register_menu(batcher_menu)

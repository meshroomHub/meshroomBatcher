"""
Add a menu for prod tools.
"""

import logging

from meshroom.api import register_menu, Menu, MenuCallback


class OpenTemplateBatcher(MenuCallback):
    def __call__(self, menu, app, **kwargs):
        pass


mill_menu = Menu("Mill", tooltip="Meshroom production tools")

mill_menu.addButton(
    "batcher",
    label="Template Batcher",
    callback=OpenTemplateBatcher(),
    tooltip="Open the TemplateBatcher UI.",
    shortcut="Ctrl+Alt+T",
)

register_menu(mill_menu)

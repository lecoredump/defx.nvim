# ============================================================================
# FILE: action.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from enum import auto, IntFlag
import os
import typing
import shutil

from defx.context import Context
from defx.defx import Defx
from defx.util import error, cwd_input, expand, confirm
from defx.view import View


def do_action(view: View, defx: Defx,
              action_name: str, context: Context) -> None:
    """
    Do "action_name" action.
    """
    action = DEFAULT_ACTIONS[action_name]
    action.func(view, defx, context)
    if ActionAttr.REDRAW in action.attr:
        view.redraw(True)


def _cd(view: View, defx: Defx, context: Context) -> None:
    """
    Change the current directory.
    """
    path = context.args[0] if context.args else expand('~')
    path = os.path.normpath(os.path.join(defx._cwd, path))
    if not os.path.isdir(path):
        error(view._vim, '{} is not directory'.format(path))
        return

    view.cd(defx, path, context.cursor)
    view._selected_candidates = []


def _open(view: View, defx: Defx, context: Context) -> None:
    """
    Open the file.
    """
    cwd = view._vim.call('getcwd')
    command = context.args[0] if context.args else 'edit'
    for target in context.targets:
        path = target['action__path']

        if os.path.isdir(path):
            view.cd(defx, path, context.cursor)
        else:
            if path.startswith(cwd):
                path = os.path.relpath(path, cwd)
            view._vim.call('defx#util#execute_path', command, path)


def _new_directory(view: View, defx: Defx, context: Context) -> None:
    """
    Create a new directory.
    """
    filename = cwd_input(view._vim, defx._cwd,
                         'Please input a new directory: ', '', 'dir')
    if os.path.exists(filename):
        error(view._vim, '{} is already exists'.format(filename))
        return

    os.mkdir(filename)
    view.redraw(True)
    view.search_file(filename, defx._index)


def _new_file(view: View, defx: Defx, context: Context) -> None:
    """
    Create a new file and it's parent directories.
    """
    filename = cwd_input(view._vim, defx._cwd,
                         'Please input a new filename: ', '', 'file')
    if os.path.exists(filename):
        error(view._vim, '{} is already exists'.format(filename))
        return

    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    with open(filename, 'w') as f:
        f.write('')
    view.redraw(True)
    view.search_file(filename, defx._index)


def _redraw(view: View, defx: Defx, context: Context) -> None:
    pass


def _remove(view: View, defx: Defx, context: Context) -> None:
    """
    Delete the file or directory.
    """
    if not confirm(view._vim, 'Are you sure you want to delete this node?'):
        return

    for target in context.targets:
        path = target['action__path']

        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    view.redraw(True)


def _rename(view: View, defx: Defx, context: Context) -> None:
    """
    Rename the file or directory.
    """
    for target in context.targets:
        path = target['action__path']
        filename = cwd_input(
            view._vim, defx._cwd,
            ('New name: {} -> '.format(path)), path, 'file')
        if not filename or filename == path:
            continue
        if os.path.exists(filename):
            error(view._vim, '{} is already exists'.format(filename))
            continue

        os.rename(path, filename)

        view.redraw(True)
        view.search_file(filename, defx._index)


def _toggle_select(view: View, defx: Defx, context: Context) -> None:
    index = context.cursor - 1
    if index in view._selected_candidates:
        view._selected_candidates.remove(index)
    else:
        view._selected_candidates.append(index)
    view.redraw()


class ActionAttr(IntFlag):
    REDRAW = auto()
    NONE = 0


class ActionTable(typing.NamedTuple):
    func: typing.Callable[[View, Defx, Context], None]
    attr: ActionAttr = ActionAttr.NONE


DEFAULT_ACTIONS = {
    'cd': ActionTable(func=_cd),
    'open': ActionTable(func=_open),
    'new_directory': ActionTable(func=_new_directory),
    'new_file': ActionTable(func=_new_file),
    'redraw': ActionTable(func=_redraw, attr=ActionAttr.REDRAW),
    'remove': ActionTable(func=_remove),
    'rename': ActionTable(func=_rename),
    'toggle_select': ActionTable(func=_toggle_select),
}

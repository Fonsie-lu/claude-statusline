#!/usr/bin/env python3
"""Print the files open in VS Code for a workspace, most recently active first.

Reads the editor layout VS Code persists in workspaceStorage/<hash>/state.vscdb.
VS Code flushes that state periodically, so the result can lag a few seconds
behind the live editor. Usage: open-editor-files.py [dir]

The workspace is the nearest ancestor of [dir] (default: the current directory)
that VS Code has open as a folder, so the script works from any subdirectory.
If none matches, the ancestors of this script's own directory are tried.
"""
import glob
import json
import os
import sqlite3
import sys
from urllib.parse import unquote, urlparse

EDITORS = ['Code', 'Code - OSS', 'Code - Insiders', 'VSCodium', 'Cursor']
CONFIG_ROOTS = ['~/.config', '~/Library/Application Support']


def uri_to_path(uri):
    return os.path.realpath(unquote(urlparse(uri).path)) if uri.startswith('file://') else None


def load_jsonc(path):
    """Parse a JSON file that may hold comments and trailing commas, as .code-workspace files do."""
    with open(path) as f:
        text = f.read()
    out, i, in_string = [], 0, False
    while i < len(text):
        char = text[i]
        if in_string:
            out.append(char)
            if char == '\\':
                out.append(text[i + 1:i + 2])
                i += 1
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
            out.append(char)
        elif text.startswith('//', i):
            i = text.find('\n', i)
            i = len(text) if i < 0 else i
            continue
        elif text.startswith('/*', i):
            end = text.find('*/', i + 2)
            i = len(text) if end < 0 else end + 2
            continue
        elif char in ']}':
            while out and out[-1].isspace():
                out.pop()
            if out and out[-1] == ',':
                out.pop()
            out.append(char)
        else:
            out.append(char)
        i += 1
    return json.loads(''.join(out))


def workspace_folders(meta):
    """Return the folders one workspaceStorage entry covers: one for a folder, all roots for a multi-root workspace."""
    with open(meta) as f:
        entry = json.load(f)
    if 'folder' in entry:
        return [path for path in [uri_to_path(entry['folder'])] if path]
    workspace_file = uri_to_path(entry.get('workspace') or entry.get('configuration') or '')
    if not workspace_file:
        return []
    base = os.path.dirname(workspace_file)
    folders = []
    for folder in load_jsonc(workspace_file).get('folders', []):
        if 'path' in folder:
            folders.append(os.path.realpath(os.path.join(base, os.path.expanduser(folder['path']))))
        elif uri_to_path(folder.get('uri', '')):
            folders.append(uri_to_path(folder['uri']))
    return folders


def known_workspaces():
    """Map each workspace folder VS Code knows to its newest state.vscdb."""
    found = {}
    for root in CONFIG_ROOTS:
        for editor in EDITORS:
            storage = os.path.join(os.path.expanduser(root), editor, 'User', 'workspaceStorage')
            for meta in glob.glob(os.path.join(storage, '*', 'workspace.json')):
                db = os.path.join(os.path.dirname(meta), 'state.vscdb')
                if not os.path.exists(db):
                    continue
                try:
                    folders = workspace_folders(meta)
                except FileNotFoundError:
                    # Stale entry: VS Code keeps storage for deleted .code-workspace files.
                    continue
                except (OSError, ValueError) as error:
                    print(f'Skipping {meta}: {error}', file=sys.stderr)
                    continue
                for path in folders:
                    if path not in found or os.path.getmtime(db) > os.path.getmtime(found[path]):
                        found[path] = db
    return found


def ancestors(path):
    path = os.path.realpath(path)
    while True:
        yield path
        parent = os.path.dirname(path)
        if parent == path:
            return
        path = parent


def find_state_db(start):
    workspaces = known_workspaces()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for candidate in [*ancestors(start), *ancestors(script_dir)]:
        if candidate in workspaces:
            return workspaces[candidate]
    return None


def leaves(node):
    if node['type'] == 'leaf':
        yield node['data']
    else:
        for child in node['data']:
            yield from leaves(child)


def open_files(db):
    con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
    row = con.execute("SELECT value FROM ItemTable WHERE key = 'memento/workbench.parts.editor'").fetchone()
    if not row:
        return []
    state = json.loads(row[0])['editorpart.state']
    groups = {g['id']: g for g in leaves(state['serializedGrid']['root'])}
    order = state.get('mostRecentActiveGroups', []) + list(groups)
    files = []
    for gid in dict.fromkeys(order):
        group = groups.get(gid, {})
        editors = group.get('editors', [])
        for index in group.get('mru', range(len(editors))):
            editor = editors[index]
            if editor['id'] != 'workbench.editors.files.fileEditorInput':
                continue
            path = json.loads(editor['value'])['resourceJSON']['fsPath']
            if path not in files:
                files.append(path)
    return files


def main():
    start = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    db = find_state_db(start)
    if not db:
        sys.exit(f'No VS Code workspace state found for {os.path.realpath(start)} or its parents')
    print('\n'.join(open_files(db)))


main()

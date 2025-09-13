"""
Session management for workspace persistence
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import hashlib

try:
    from ..config import CHATGPT_URL, DEFAULT_WORKSPACE_NAMES
    from ..paths import get_sessions_file, get_workspace_notepad_file, ensure_directories
except ImportError:
    # Support direct module execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from config import CHATGPT_URL, DEFAULT_WORKSPACE_NAMES
    from paths import get_sessions_file, get_workspace_notepad_file, ensure_directories


@dataclass
class TabData:
    """Data structure for tab information"""
    url: str
    title: str = "ChatGPT"


@dataclass 
class WorkspaceData:
    """Data structure for workspace information"""
    name: str
    tabs: List[TabData]
    active_tab: int = 0
    notepad_content: str = ""
    notepad_visible: bool = False


class SessionManager:
    """Handles session persistence and auto-save functionality"""
    
    def __init__(self):
        self.session_file = get_sessions_file()
        self._last_session_hash = None
        self._last_notepad_hashes = {}
        ensure_directories()
    
    def _compute_content_hash(self, content: str) -> str:
        """Compute hash of content for change detection"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def save_sessions(self, workspaces: Dict[int, WorkspaceData]) -> bool:
        """Save workspace sessions to file (only if changed)"""
        try:
            session_data = {}
            files_written = 0
            
            for workspace_id, workspace_data in workspaces.items():
                # Check if notepad content has changed
                notepad_content = workspace_data.notepad_content
                notepad_hash = self._compute_content_hash(notepad_content)
                
                if notepad_hash != self._last_notepad_hashes.get(workspace_id):
                    # Only write notepad file if content changed
                    notepad_file = get_workspace_notepad_file(workspace_id)
                    notepad_file.write_text(notepad_content, encoding='utf-8')
                    self._last_notepad_hashes[workspace_id] = notepad_hash
                    files_written += 1
                
                # Prepare session data (without notepad content and without timestamp for hash)
                session_data[str(workspace_id)] = {
                    'name': workspace_data.name,
                    'tabs': [asdict(tab) for tab in workspace_data.tabs],
                    'active_tab': workspace_data.active_tab,
                    'notepad_visible': workspace_data.notepad_visible
                }
            
            # Check if session data has changed (compute hash WITHOUT timestamp)
            session_json = json.dumps(session_data, sort_keys=True)
            session_hash = self._compute_content_hash(session_json)
            
            if session_hash != self._last_session_hash:
                # Add timestamp only when we decide to write
                current_time = time.time()
                for workspace_data in session_data.values():
                    workspace_data['last_saved'] = current_time
                
                # Only write session file if data changed
                with open(self.session_file, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2)
                self._last_session_hash = session_hash
                files_written += 1
            
            return True
            
        except Exception:
            return False
    
    def load_sessions(self) -> Dict[int, WorkspaceData]:
        """Load workspace sessions from file"""
        if not self.session_file.exists():
            return self._create_default_workspaces()
        
        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            workspaces = {}
            for workspace_id_str, data in session_data.items():
                workspace_id = int(workspace_id_str)
                
                # Load tabs
                tabs = [TabData(**tab_data) for tab_data in data.get('tabs', [])]
                if not tabs:  # Ensure at least one tab
                    tabs = [TabData(url=CHATGPT_URL)]
                
                # Load notepad content from separate file
                notepad_file = get_workspace_notepad_file(workspace_id)
                notepad_content = ""
                if notepad_file.exists():
                    try:
                        notepad_content = notepad_file.read_text(encoding='utf-8')
                    except Exception:
                        pass  # Use empty notepad content
                
                workspaces[workspace_id] = WorkspaceData(
                    name=data.get('name', DEFAULT_WORKSPACE_NAMES[workspace_id]),
                    tabs=tabs,
                    active_tab=max(0, min(data.get('active_tab', 0), len(tabs) - 1)),
                    notepad_content=notepad_content,
                    notepad_visible=data.get('notepad_visible', False)
                )
            
            # Ensure we have all 4 workspaces
            for i in range(4):
                if i not in workspaces:
                    workspaces[i] = WorkspaceData(
                        name=DEFAULT_WORKSPACE_NAMES[i],
                        tabs=[TabData(url=CHATGPT_URL)],
                        active_tab=0,
                        notepad_content="",
                        notepad_visible=False
                    )
            
            return workspaces
            
        except Exception:
            return self._create_default_workspaces()
    
    def _create_default_workspaces(self) -> Dict[int, WorkspaceData]:
        """Create default workspace configuration"""
        return {
            i: WorkspaceData(
                name=DEFAULT_WORKSPACE_NAMES[i],
                tabs=[TabData(url=CHATGPT_URL)],
                active_tab=0,
                notepad_content="",
                notepad_visible=False
            )
            for i in range(4)
        }
    
    def backup_sessions(self) -> bool:
        """Create a backup of current sessions"""
        if not self.session_file.exists():
            return False
            
        try:
            import shutil
            backup_file = self.session_file.with_suffix('.backup.json')
            shutil.copy2(self.session_file, backup_file)
            return True
        except Exception:
            return False
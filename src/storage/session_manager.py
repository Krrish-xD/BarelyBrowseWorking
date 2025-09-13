"""
Session management for workspace persistence
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from ..config import CHATGPT_URL, DEFAULT_WORKSPACE_NAMES
from ..paths import get_sessions_file, get_workspace_notepad_file, ensure_directories


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
        ensure_directories()
    
    def save_sessions(self, workspaces: Dict[int, WorkspaceData]) -> bool:
        """Save workspace sessions to file"""
        try:
            session_data = {}
            
            for workspace_id, workspace_data in workspaces.items():
                # Save notepad content to separate file
                notepad_file = get_workspace_notepad_file(workspace_id)
                notepad_file.write_text(workspace_data.notepad_content, encoding='utf-8')
                
                # Save session data (without notepad content to keep it small)
                session_data[str(workspace_id)] = {
                    'name': workspace_data.name,
                    'tabs': [asdict(tab) for tab in workspace_data.tabs],
                    'active_tab': workspace_data.active_tab,
                    'notepad_visible': workspace_data.notepad_visible,
                    'last_saved': time.time()
                }
            
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
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
# PyTTI Phase 3 Implementation Plan

**Focus:** UI Enhancements & User Experience
**Duration:** Current session
**Status:** 🚀 IN PROGRESS

---

## 🎯 Phase 3 Objectives

### 1. **Real-time Preview** (HIGH PRIORITY)
- Show current generation progress visually
- Update preview every N steps
- Display in generation tab
- Add zoom/pan controls

### 2. **Prompt History** (HIGH PRIORITY)
- Save all prompts with timestamps
- Quick re-use of previous prompts
- Search/filter history
- Export/import history

### 3. **Image Gallery** (HIGH PRIORITY)
- Grid view of all generations
- Click to view full size
- Show metadata (prompt, settings)
- Re-generate with same settings
- Compare images side-by-side

### 4. **Settings UI** (MEDIUM PRIORITY)
- Load/save presets
- Visual settings editor
- Quick presets (Fast/Balanced/Quality)
- Export/import settings

### 5. **Enhanced Progress Display** (MEDIUM PRIORITY)
- Better progress bar visualization
- Show current step image preview
- ETA calculation
- Loss/quality metrics display

### 6. **Batch Generation** (LOW PRIORITY)
- Queue multiple prompts
- Batch processing
- Progress for entire queue
- Automatic naming

---

## 📋 Detailed Tasks

### Task Group 1: Real-time Preview (60 min) ⭐

**1.1 Create Preview Component** (20 min)
- Gradio Image component that updates
- Wire to generation callback
- Add zoom/pan if possible

**1.2 Integrate with Pipeline** (20 min)
- Modify GenerationPipeline to emit preview
- Add callback for intermediate images
- Throttle updates (every 5-10 steps)

**1.3 UI Integration** (20 min)
- Add preview to generate tab
- Side-by-side with controls
- Add "Show Preview" toggle

### Task Group 2: Prompt History (45 min) ⭐

**2.1 Create PromptHistoryManager** (20 min)
- Save prompts to JSON
- Load history on startup
- Add/remove/search methods
- Timestamp tracking

**2.2 Create History UI Component** (15 min)
- Dropdown or list of recent prompts
- Click to load prompt
- Delete button for each entry
- Search box

**2.3 Integration** (10 min)
- Auto-save on generate
- Wire up to prompt textbox
- Persistence across sessions

### Task Group 3: Image Gallery (60 min) ⭐

**3.1 Create GalleryManager** (20 min)
- Track all generated images
- Store metadata (prompt, settings, timestamp)
- Load from outputs directory
- Thumbnail generation

**3.2 Build Gallery UI** (30 min)
- Gradio Gallery component
- Image grid with metadata overlay
- Click to enlarge
- Re-generate button
- Delete button

**3.3 Integration** (10 min)
- Auto-add images after generation
- Refresh button
- Filter by date/prompt

### Task Group 4: Settings UI (45 min)

**4.1 Create Preset System** (20 min)
- Default presets (Fast/Balanced/Quality)
- Custom preset save/load
- JSON storage

**4.2 Settings Panel** (20 min)
- Visual editor for all settings
- Preset dropdown
- Save/Load/Reset buttons
- Export/Import buttons

**4.3 Integration** (5 min)
- Wire to ConfigManager
- Apply settings to generation

### Task Group 5: Enhanced Progress (30 min)

**5.1 Better Progress Bar** (10 min)
- Percentage display
- Time elapsed / ETA
- Steps completed / total

**5.2 Metrics Display** (10 min)
- Current loss value
- VRAM usage during generation
- Steps per second

**5.3 Visual Improvements** (10 min)
- Color-coded progress
- Animated when active
- Status messages

### Task Group 6: Batch Generation (Optional - 45 min)

**6.1 Queue Manager** (20 min)
- Add prompts to queue
- Process sequentially
- Cancel queue

**6.2 Queue UI** (20 min)
- List of queued prompts
- Re-order queue
- Remove from queue
- Progress for entire queue

**6.3 Integration** (5 min)
- Wire to generation pipeline
- Auto-save results

---

## 🏗️ Architecture

### New Components

```
src/pytti/
  ├── history/
  │   ├── __init__.py
  │   └── prompt_history.py       ← NEW: Prompt history manager
  ├── gallery/
  │   ├── __init__.py
  │   ├── gallery_manager.py      ← NEW: Gallery management
  │   └── metadata.py             ← NEW: Image metadata
  ├── presets/
  │   ├── __init__.py
  │   └── preset_manager.py       ← NEW: Settings presets
  └── webui/
      ├── components/
      │   ├── preview.py           ← NEW: Real-time preview
      │   ├── history_panel.py     ← NEW: Prompt history UI
      │   ├── gallery_panel.py     ← NEW: Gallery UI
      │   ├── settings_panel.py    ← NEW: Settings editor
      │   └── progress_panel.py    ← NEW: Enhanced progress
      └── tabs/
          └── gallery.py           ← NEW: Gallery tab
```

---

## 🎨 UI Mockup

### Generate Tab (Enhanced):
```
+----------------------------------------------------------+
| Prompt: [_________________________________] [History ▼]  |
+---------------------------+------------------------------+
| Settings Panel            | Preview Panel                |
| - Preset: [Balanced ▼]    | +------------------------+   |
| - Width: [1024]           | |                        |   |
| - Height: [1024]          | |    Live Preview        |   |
| - Steps: [100]            | |                        |   |
| - [Advanced ▼]            | +------------------------+   |
|                           | Progress: ████░░░░░ 45%     |
| [Generate] [Stop]         | ETA: 2m 15s                 |
+---------------------------+------------------------------+
```

### Gallery Tab:
```
+----------------------------------------------------------+
| [Search: ___________] [Sort: Recent ▼] [Refresh]         |
+----------------------------------------------------------+
| +--------+ +--------+ +--------+ +--------+ +--------+   |
| | IMG 1  | | IMG 2  | | IMG 3  | | IMG 4  | | IMG 5  |   |
| | sunset | | forest | | ocean  | | mtn    | | city   |   |
| | [👁][🔄]| | [👁][🔄]| | [👁][🔄]| | [👁][🔄]| | [👁][🔄]|   |
| +--------+ +--------+ +--------+ +--------+ +--------+   |
| +--------+ +--------+ +--------+                         |
| | IMG 6  | | IMG 7  | | IMG 8  |                         |
| +--------+ +--------+ +--------+                         |
+----------------------------------------------------------+
```

---

## 📊 Success Criteria

### User Experience
- [ ] Real-time preview updates during generation
- [ ] Prompt history accessible in 1 click
- [ ] Gallery shows all generations with metadata
- [ ] Settings can be saved as presets
- [ ] Progress shows ETA and current step

### Technical
- [ ] PromptHistoryManager persists to JSON
- [ ] GalleryManager loads from outputs directory
- [ ] PresetManager handles custom presets
- [ ] All components integrated into main UI
- [ ] No performance degradation

### Code Quality
- [ ] All new code has type hints
- [ ] Comprehensive error handling
- [ ] Clean separation of concerns
- [ ] Well documented
- [ ] Backward compatible

---

## 🚀 Implementation Order

**Priority 1 (Must Have):**
1. Prompt History ⭐ (45 min)
2. Real-time Preview ⭐ (60 min)
3. Enhanced Progress ⭐ (30 min)

**Priority 2 (Should Have):**
4. Image Gallery ⭐ (60 min)
5. Settings UI (45 min)

**Priority 3 (Nice to Have):**
6. Batch Generation (45 min)

**Total Estimated Time:** 4-5 hours

---

## 📝 Notes

- Focus on most impactful features first
- Keep UI responsive and fast
- Ensure mobile-friendly where possible
- Test with real generations
- Document new features

---

Let's enhance the UI! 🎨

# PyTTI Phase 2 Implementation Plan

**Focus:** Type Hints, Architecture Refinement & UI Integration
**Duration:** Current session
**Status:** 🚀 IN PROGRESS

---

## 🎯 Phase 2 Objectives

### 1. **Type Hints** (HIGH PRIORITY)
- Add comprehensive type hints to all new modules
- Add type hints to generation pipeline
- Add type hints to model loaders
- Target: 90% type hint coverage on modified code

### 2. **Architecture Refinement** (HIGH PRIORITY)
- Create GenerationPipeline class (separate concerns)
- Extract step functions from 300+ line generate_image()
- Create ConfigManager for settings persistence
- Better separation of UI and business logic

### 3. **UI Integration** (MEDIUM PRIORITY)
- Integrate VRAM monitor into main UI
- Integrate error display into main UI
- Add real-time status updates
- Improve progress feedback

### 4. **Logging** (MEDIUM PRIORITY)
- Set up proper logging configuration
- Add structured logging
- Log rotation and management
- Performance metrics logging

### 5. **Documentation** (LOW PRIORITY)
- Update docstrings with type information
- Add usage examples
- Create architecture diagram
- Update README with new features

---

## 📋 Detailed Tasks

### Task Group 1: Type Hints (90 min)

**1.1 Add type hints to managers** (15 min)
- Already have basic types, add more detailed ones
- Add return type annotations
- Add Optional/Union types where needed

**1.2 Add type hints to generation pipeline** (30 min)
- Annotate all function parameters
- Annotate return types
- Add TypedDict for config structure

**1.3 Add type hints to model loaders** (20 min)
- Check image_models/diffusion.py
- Add Protocol for model interface
- Annotate loader functions

**1.4 Add type hints to UI components** (25 min)
- Annotate Gradio component types
- Add callback type annotations

### Task Group 2: Architecture Refinement (90 min)

**2.1 Create GenerationPipeline class** (40 min)
- Extract steps from generate_image()
- Create clean step methods
- Add state management
- Make it testable

**2.2 Create ConfigManager** (30 min)
- Settings persistence (JSON)
- Load/save user preferences
- Default configuration
- Validation integration

**2.3 Refactor generation.py** (20 min)
- Use new GenerationPipeline class
- Simplify generate_image() to orchestration
- Better error propagation

### Task Group 3: UI Integration (60 min)

**3.1 Integrate VRAM monitor** (15 min)
- Add to main UI sidebar
- Wire up auto-refresh
- Test GPU/CPU modes

**3.2 Integrate error display** (15 min)
- Add error panel to main UI
- Wire up to generation callbacks
- Test error scenarios

**3.3 Improve progress display** (20 min)
- Add real-time step counter
- Add ETA calculation
- Add preview of current step (if time)

**3.4 Add status indicators** (10 min)
- Generation status badge
- Model loading indicators
- VRAM warnings

### Task Group 4: Logging Setup (30 min)

**4.1 Create logging configuration** (15 min)
- Configure loguru properly
- Add log rotation
- Set log levels
- Add performance logging

**4.2 Add structured logging** (15 min)
- Log with context
- Add timing decorators
- Add VRAM logging

### Task Group 5: Documentation (30 min)

**5.1 Update docstrings** (15 min)
- Add examples to key functions
- Document type parameters
- Add "See Also" sections

**5.2 Create PHASE2_IMPROVEMENTS.md** (15 min)
- Document all changes
- Add migration guide
- Update metrics

---

## 🏗️ Key Architectural Changes

### Before (Phase 1):
```
generate_image() [300 lines]
  ├─ Validation
  ├─ Model loading
  ├─ CLIP initialization
  ├─ Prompt parsing
  ├─ Optimization loop (200 lines)
  └─ Save results
```

### After (Phase 2):
```
GenerationPipeline:
  ├─ validate() [clean method]
  ├─ initialize_models() [clean method]
  ├─ setup_prompt() [clean method]
  ├─ optimize() [clean method]
  └─ finalize() [clean method]

generate_image() [50 lines]
  └─ Orchestrates pipeline + error handling
```

---

## 📊 Success Criteria

### Code Quality
- [ ] Type hint coverage: 90%+ on modified code
- [ ] No functions >100 lines
- [ ] Clear separation of concerns
- [ ] All public APIs documented

### User Experience
- [ ] VRAM monitor visible in UI
- [ ] Errors displayed in UI (not just console)
- [ ] Real-time progress feedback
- [ ] Settings persistence working

### Technical
- [ ] GenerationPipeline class tested
- [ ] ConfigManager saves/loads correctly
- [ ] Logging configured properly
- [ ] No syntax errors
- [ ] All imports work

---

## 🚀 Implementation Order

**Priority 1 (Do First):**
1. Create GenerationPipeline class ⭐
2. Integrate VRAM/error display into UI ⭐
3. Add comprehensive type hints ⭐

**Priority 2 (Do Next):**
4. Create ConfigManager for persistence
5. Set up logging properly
6. Refactor to use pipeline

**Priority 3 (If Time):**
7. Add real-time preview
8. Improve progress display
9. Documentation updates

---

## 📝 Notes

- Focus on making code more maintainable
- Each change should improve clarity
- Keep backward compatibility
- Test as we go
- Document significant changes

---

Let's build Phase 2! 🚀

# Analysis Tab Color Fixes - Complete Mapping

## Color Replacements Needed

### Background Colors:
- `bg-[#020617]` → `bg-[#eaf4f7]` (light blue-gray)
- `bg-[#0F1729]` → `bg-white` or `bg-white/95`

### Text Colors:
- `text-white` → `text-gray-900`
- `text-gray-100` → `text-gray-900`
- `text-gray-400` → `text-gray-600`
- `text-cyan-400` → `text-[#1762C7]`
- `text-cyan-300` → `text-[#1FA8A6]`

### Border Colors:
- `border-white/10` → `border-[#1762C7]/20`
- `border-white/5` → `border-[#1762C7]/10`
- `border-cyan-500/30` → `border-[#1762C7]/30`
- `border-cyan-500/20` → `border-[#1762C7]/20`

### Background Gradients:
- `from-cyan-500/5 to-transparent` → `from-[#1762C7]/5 to-transparent`
- `bg-cyan-500/10` → `bg-[#1762C7]/10`
- `bg-cyan-500/20` → `bg-[#1762C7]/20`

### Specific Elements:
1. **Modal Background**: Line 71
   - From: `bg-[#020617]/80`
   - To: `bg-gray-900/80`

2. **Modal Content**: Line 74
   - From: `bg-[#0F1729]`
   - To: `bg-white`

3. **Loading Screen**: Lines 292, 304, 320, 334
   - From: `bg-[#020617]`
   - To: `bg-[#eaf4f7]`

4. **Main Content**: Line 395
   - From: `bg-[#020617]`
   - To: `bg-[#eaf4f7]`

5. **Cards**: Lines 401, 435
   - From: `bg-[#0F1729]/30`
   - To: `bg-white`

## Implementation Strategy

Due to 50+ occurrences, create a Python script to do replacements systematically.

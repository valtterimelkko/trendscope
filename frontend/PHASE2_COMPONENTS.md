# Phase 2: shadcn Components Installation

## Core Components to Install

### Layout & Navigation
- `sidebar` - Dashboard sidebar navigation
- `sheet` - Mobile drawer/sheet
- `dropdown-menu` - User profile dropdown
- `navigation-menu` - Marketing header navigation

### Forms & Inputs
- `button` - Primary, secondary, ghost variants
- `input` - Text inputs
- `label` - Form labels
- `form` - Form wrapper with validation
- `select` - Dropdown selects
- `checkbox` - Checkboxes for settings
- `switch` - Toggle switches
- `textarea` - Multi-line text input
- `radio-group` - Radio button groups

### Display Components
- `card` - Content cards (trends, stats)
- `badge` - Status badges, velocity scores
- `avatar` - User avatars
- `table` - Data tables
- `separator` - Visual dividers
- `skeleton` - Loading placeholders

### Feedback & Modals
- `alert` - Info/warning/error alerts
- `dialog` - Modal dialogs
- `toast` - Toast notifications (via Sonner)
- `alert-dialog` - Confirmation dialogs
- `popover` - Popovers for additional info
- `tooltip` - Tooltips on hover

### Data Visualization
- `chart` - Recharts wrapper components
- `progress` - Progress bars (saturation meter)

### Utility
- `scroll-area` - Custom scrollbars
- `tabs` - Tabbed interfaces
- `accordion` - Collapsible sections
- `command` - Command palette (future)

## Installation Command

```bash
npx shadcn@latest add button card badge input label separator \
  dialog sheet dropdown-menu sidebar avatar table form select \
  checkbox switch textarea alert toast skeleton progress \
  scroll-area tabs accordion popover tooltip alert-dialog \
  navigation-menu radio-group chart
```

## Custom Variants to Create After Installation

### Button Variants
- `ghost-primary` - For sidebar menu items
- className: "hover:bg-primary/10 hover:text-primary"

### Card Variants
- `trend-card` - For trend list items with velocity bars
- Includes hover effects and click states

### Badge Variants
- `velocity` - Color-coded based on score (0-100)
  - 0-30: red (emerging)
  - 31-70: yellow (peaking)
  - 71-100: green (hot)

### Alert Variants
- `trend-alert` - Slack-style alert cards
- Compact design with icon and quick actions
